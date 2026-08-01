//! One actor task per table. The actor exclusively owns the `EuchreGame` plus
//! seat bindings, so there are no shared locks on game state; everything
//! arrives as a `TableCmd` and every state change fans out a per-role redacted
//! `TableView` to each attached connection.

use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;

use euc_shared::{
    redact, Action, Bot, ClientMsg, ErrorCode, EuchreGame, HeuristicBot, Phase, PlayerId, Role,
    RuleConfig, Seat, SeatInfo, ServerMsg, TableId, TableMeta, TableSummary,
};
use tokio::sync::mpsc;

use crate::lobby::{ConnId, Lobby};

const AI_NAMES: [&str; 4] = ["Chip", "Robo", "Data", "Zork"];
/// How long the hand summary stays up before the next hand deals itself.
const HAND_DONE_MS: u64 = 2500;
/// How long a finished trick lies on the table before the winner takes it
/// (the client's take-animation is timed to finish just inside this).
const TRICK_SETTLE_MS: u64 = 900;

/// AI think time: a little jitter so bots feel less mechanical. Overridable
/// via EUC_AI_DELAY_MS (integration tests set it to ~0).
fn ai_delay_ms(gen: u64) -> u64 {
    static OVERRIDE: std::sync::OnceLock<Option<u64>> = std::sync::OnceLock::new();
    OVERRIDE
        .get_or_init(|| std::env::var("EUC_AI_DELAY_MS").ok().and_then(|s| s.parse().ok()))
        .unwrap_or(400 + gen % 350)
}

pub enum TableCmd {
    Attach {
        conn: ConnId,
        player: PlayerId,
        name: String,
        role: Role,
        tx: mpsc::Sender<ServerMsg>,
    },
    Detach {
        conn: ConnId,
    },
    Msg {
        conn: ConnId,
        msg: ClientMsg,
    },
    /// AI move / auto-continue timer; stale if `gen` no longer matches.
    Tick {
        gen: u64,
    },
    /// Shut the table down if nobody has come back since `gen`.
    ReapCheck {
        gen: u64,
    },
}

/// How long an empty (non-persistent) table lingers before being reaped.
const REAP_AFTER: Duration = Duration::from_secs(300);

struct Conn {
    player: PlayerId,
    name: String,
    role: Role,
    tx: mpsc::Sender<ServerMsg>,
}

struct Table {
    id: TableId,
    meta: TableMeta,
    game: Option<EuchreGame>,
    /// Which human holds each seat; survives disconnects so a refresh
    /// reclaims the chair. None for open and AI seats.
    seat_players: [Option<PlayerId>; 4],
    conns: HashMap<ConnId, Conn>,
    /// Bumped on every state change; stale Ticks are dropped against it.
    gen: u64,
    cmd_tx: mpsc::Sender<TableCmd>,
    lobby: Arc<Lobby>,
    /// Persistent tables (the default one) are never reaped.
    persistent: bool,
}

pub fn spawn(
    id: TableId,
    name: String,
    rules: RuleConfig,
    lobby: Arc<Lobby>,
    persistent: bool,
) -> mpsc::Sender<TableCmd> {
    let (tx, rx) = mpsc::channel(64);
    let table = Table {
        meta: TableMeta {
            table_id: id.clone(),
            table_name: name,
            rules,
            seats: Default::default(),
            spectators: Vec::new(),
        },
        id,
        game: None,
        seat_players: Default::default(),
        conns: HashMap::new(),
        gen: 0,
        cmd_tx: tx.clone(),
        lobby,
        persistent,
    };
    tokio::spawn(table.run(rx));
    tx
}

impl Table {
    async fn run(mut self, mut rx: mpsc::Receiver<TableCmd>) {
        while let Some(cmd) = rx.recv().await {
            match cmd {
                TableCmd::Attach { conn, player, name, role, tx } => {
                    self.on_attach(conn, player, name, role, tx)
                }
                TableCmd::Detach { conn } => self.on_detach(conn),
                TableCmd::Msg { conn, msg } => self.on_msg(conn, msg),
                TableCmd::Tick { gen } => self.on_tick(gen),
                TableCmd::ReapCheck { gen } => {
                    if gen == self.gen && self.conns.is_empty() && !self.persistent {
                        self.lobby.remove_table(&self.id);
                        return;
                    }
                }
            }
        }
    }

    fn on_attach(
        &mut self,
        conn: ConnId,
        player: PlayerId,
        name: String,
        requested: Role,
        tx: mpsc::Sender<ServerMsg>,
    ) {
        // A player with a held seat always comes back to it.
        let held = (0..4).find(|&i| self.seat_players[i] == Some(player.clone()));
        let role = if let Some(i) = held {
            self.meta.seats[i].name = Some(name.clone());
            Role::Seated { seat: Seat(i as u8) }
        } else {
            match requested {
                Role::Seated { seat } => {
                    if self.claim_seat(seat, &player, &name) {
                        Role::Seated { seat }
                    } else {
                        let _ = tx.try_send(ServerMsg::Error {
                            code: ErrorCode::SeatTaken,
                            message: "that seat is taken — joining as a spectator".into(),
                        });
                        Role::Spectator
                    }
                }
                other => other,
            }
        };
        let _ = tx.try_send(ServerMsg::Joined { table_id: self.id.clone(), role });
        self.conns.insert(conn, Conn { player, name, role, tx });
        self.broadcast();
    }

    fn on_detach(&mut self, conn: ConnId) {
        // Seat bindings survive the disconnect; the seat just shows as away.
        self.conns.remove(&conn);
        self.broadcast();
        if self.conns.is_empty() && !self.persistent {
            let gen = self.gen;
            let tx = self.cmd_tx.clone();
            tokio::spawn(async move {
                tokio::time::sleep(REAP_AFTER).await;
                let _ = tx.send(TableCmd::ReapCheck { gen }).await;
            });
        }
    }

    /// True if the seat was free and is now bound to `player`.
    fn claim_seat(&mut self, seat: Seat, player: &PlayerId, name: &str) -> bool {
        let i = seat.index();
        if self.meta.seats[i].is_ai || self.seat_players[i].is_some() {
            return false;
        }
        self.seat_players[i] = Some(player.clone());
        self.meta.seats[i] = SeatInfo {
            name: Some(name.to_string()),
            is_ai: false,
            connected: true,
        };
        self.lobby.set_seat(player.clone(), self.id.clone());
        true
    }

    fn vacate_seat(&mut self, i: usize) {
        if let Some(pid) = self.seat_players[i].take() {
            self.lobby.clear_seat(&pid);
        }
        self.meta.seats[i] = SeatInfo::default();
    }

    fn error(&self, conn: ConnId, code: ErrorCode, message: &str) {
        if let Some(c) = self.conns.get(&conn) {
            let _ = c.tx.try_send(ServerMsg::Error { code, message: message.to_string() });
        }
    }

    fn on_msg(&mut self, conn: ConnId, msg: ClientMsg) {
        let Some(c) = self.conns.get(&conn) else { return };
        let player = c.player.clone();
        let role = c.role;
        match msg {
            ClientMsg::TakeSeat { seat } => {
                let current = match role {
                    Role::Seated { seat } => Some(seat.index()),
                    _ => None,
                };
                if current.is_some() && self.game.is_some() {
                    return self.error(conn, ErrorCode::BadRequest, "can't switch seats mid-game");
                }
                let name = c.name.clone();
                if !self.claim_seat(seat, &player, &name) {
                    return self.error(conn, ErrorCode::SeatTaken, "that seat is taken");
                }
                if let Some(old) = current {
                    self.vacate_seat(old);
                    // claim_seat re-registered the new seat in the lobby index.
                    self.lobby.set_seat(player, self.id.clone());
                }
                self.conns.get_mut(&conn).unwrap().role = Role::Seated { seat };
                self.broadcast();
            }
            ClientMsg::StandUp => {
                let Role::Seated { seat } = role else {
                    return self.error(conn, ErrorCode::BadRequest, "you are not seated");
                };
                self.vacate_seat(seat.index());
                self.conns.get_mut(&conn).unwrap().role = Role::Spectator;
                self.broadcast();
            }
            ClientMsg::AddAi { seat } => {
                let i = seat.index();
                let disconnected_human = self.seat_players[i].is_some()
                    && !self
                        .conns
                        .values()
                        .any(|c| Some(&c.player) == self.seat_players[i].as_ref());
                if self.meta.seats[i].is_ai
                    || (self.seat_players[i].is_some() && !disconnected_human)
                {
                    return self.error(conn, ErrorCode::SeatTaken, "seat is occupied");
                }
                self.vacate_seat(i);
                self.meta.seats[i] = SeatInfo {
                    name: Some(AI_NAMES[i].to_string()),
                    is_ai: true,
                    connected: true,
                };
                self.broadcast();
            }
            ClientMsg::RemoveAi { seat } => {
                let i = seat.index();
                if !self.meta.seats[i].is_ai {
                    return self.error(conn, ErrorCode::BadRequest, "no AI on that seat");
                }
                if self.game.is_some() {
                    return self.error(conn, ErrorCode::BadRequest, "can't remove an AI mid-game");
                }
                self.meta.seats[i] = SeatInfo::default();
                self.broadcast();
            }
            ClientMsg::SetRules { rules } => {
                if self.in_progress() {
                    return self.error(conn, ErrorCode::BadRequest, "can't change rules mid-game");
                }
                self.meta.rules = rules;
                self.broadcast();
            }
            ClientMsg::StartGame => {
                if self.in_progress() {
                    return self.error(conn, ErrorCode::BadRequest, "game already running");
                }
                if self.meta.seats.iter().any(|s| s.name.is_none()) {
                    return self.error(conn, ErrorCode::BadRequest, "need all four seats filled");
                }
                let seed = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_nanos() as u64)
                    .unwrap_or(1)
                    ^ self.gen.rotate_left(32);
                self.game = Some(EuchreGame::new(self.meta.rules, seed));
                self.broadcast();
            }
            ClientMsg::Act { action } => {
                let Role::Seated { seat } = role else {
                    return self.error(conn, ErrorCode::BadRequest, "spectators can't act");
                };
                let Some(game) = &mut self.game else {
                    return self.error(conn, ErrorCode::BadRequest, "no game in progress");
                };
                match game.apply(seat, action) {
                    Ok(()) => self.broadcast(),
                    Err(euc_shared::RuleError::NotYourTurn) => {
                        self.error(conn, ErrorCode::NotYourTurn, "not your turn")
                    }
                    Err(euc_shared::RuleError::IllegalAction) => {
                        self.error(conn, ErrorCode::IllegalAction, "that play is not legal")
                    }
                }
            }
            ClientMsg::SetName { name } => {
                self.conns.get_mut(&conn).unwrap().name = name.clone();
                if let Role::Seated { seat } = role {
                    self.meta.seats[seat.index()].name = Some(name);
                }
                self.broadcast();
            }
            _ => self.error(conn, ErrorCode::BadRequest, "not a table message"),
        }
    }

    /// A game is "in progress" for seating purposes unless it's over.
    fn in_progress(&self) -> bool {
        matches!(&self.game, Some(g) if !matches!(g.phase, Phase::GameOver { .. }))
    }

    fn on_tick(&mut self, gen: u64) {
        if gen != self.gen {
            return; // stale timer: state moved on
        }
        let Some(game) = &mut self.game else { return };
        let Some(turn) = game.turn_seat() else { return };
        let acted = if matches!(game.phase, Phase::TrickDone { .. } | Phase::HandDone { .. }) {
            game.apply(turn, Action::Continue).is_ok()
        } else if self.meta.seats[turn.index()].is_ai {
            let view = redact(&self.meta, Some(game), Role::Seated { seat: turn });
            let action = HeuristicBot.choose(&view);
            game.apply(turn, action).is_ok()
        } else {
            false
        };
        if acted {
            self.broadcast();
        }
    }

    /// Arm the timer that advances AI turns and hand summaries. Called from
    /// `broadcast()` only: every state change invalidates all earlier timers
    /// (their `gen` goes stale), so the one scheduled here is always the
    /// single live timer. Scheduling anywhere else risks a dropped turn —
    /// an unrelated broadcast (someone joining mid-think) would cancel it.
    fn schedule(&mut self) {
        let Some(game) = &self.game else { return };
        let delay_ms = match &game.phase {
            Phase::GameOver { .. } => return,
            Phase::HandDone { .. } => HAND_DONE_MS,
            Phase::TrickDone { .. } => TRICK_SETTLE_MS,
            _ => {
                let turn = game.turn_seat().expect("active phase has a turn");
                if !self.meta.seats[turn.index()].is_ai {
                    return;
                }
                ai_delay_ms(self.gen)
            }
        };
        let gen = self.gen;
        let tx = self.cmd_tx.clone();
        tokio::spawn(async move {
            tokio::time::sleep(Duration::from_millis(delay_ms)).await;
            let _ = tx.send(TableCmd::Tick { gen }).await;
        });
    }

    /// Fan the new state out: one redacted view per connection, plus the
    /// lobby summary. Every caller that mutated state must end with this.
    fn broadcast(&mut self) {
        self.gen += 1;
        for i in 0..4 {
            self.meta.seats[i].connected = match &self.seat_players[i] {
                Some(pid) => self.conns.values().any(|c| &c.player == pid),
                None => self.meta.seats[i].is_ai,
            };
        }
        self.meta.spectators = self
            .conns
            .values()
            .filter(|c| matches!(c.role, Role::Spectator))
            .map(|c| c.name.clone())
            .collect();
        for c in self.conns.values() {
            let view = redact(&self.meta, self.game.as_ref(), c.role);
            let _ = c.tx.try_send(ServerMsg::TableState { view });
        }
        self.lobby.update_summary(self.summary());
        self.schedule();
    }

    fn summary(&self) -> TableSummary {
        let humans = self.seat_players.iter().filter(|p| p.is_some()).count() as u8;
        let ais = self.meta.seats.iter().filter(|s| s.is_ai).count() as u8;
        TableSummary {
            id: self.id.clone(),
            name: self.meta.table_name.clone(),
            humans,
            ais,
            open_seats: 4 - humans - ais,
            spectators: self.meta.spectators.len() as u8,
            in_game: self.in_progress(),
        }
    }
}

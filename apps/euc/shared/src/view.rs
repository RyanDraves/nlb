//! Per-role redaction: the ONLY game state that ever crosses the wire.
//! A seated player sees their own hand; everyone else sees card counts.
//! The kitty and other hands are structurally absent — they cannot leak.

use serde::{Deserialize, Serialize};

use crate::cards::{Card, Suit};
use crate::game::{Action, EuchreGame, Phase, Seat};
use crate::protocol::TableId;
use crate::rules::RuleConfig;

/// How a connection participates at a table. Also used as the join request.
#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Role {
    Seated { seat: Seat },
    Spectator,
    /// A shared display (tablet on the physical table): public state only.
    TableDisplay,
}

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Eq, Default)]
pub struct SeatInfo {
    /// None = open seat.
    pub name: Option<String>,
    pub is_ai: bool,
    /// False when a human seat's connection dropped (seat is held for them).
    pub connected: bool,
}

/// Table state independent of any deal: who sits where, table identity, rules.
/// Maintained by the server's table actor.
#[derive(Clone, Debug, Default)]
pub struct TableMeta {
    pub table_id: TableId,
    pub table_name: String,
    pub rules: RuleConfig,
    pub seats: [SeatInfo; 4],
    pub spectators: Vec<String>,
}

/// The in-game portion of a view, present once cards are dealt.
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
pub struct GameView {
    pub phase: Phase,
    pub dealer: Seat,
    /// Your cards (six during your own DealerDiscard). Empty for
    /// spectators/table displays.
    pub hand: Vec<Card>,
    pub hand_counts: [u8; 4],
    pub upcard: Option<Card>,
    pub turned_down: Option<Card>,
    pub trump: Option<Suit>,
    pub maker: Option<Seat>,
    pub alone: bool,
    pub sitting_out: Option<Seat>,
    pub current_trick: Vec<(Seat, Card)>,
    pub last_trick: Option<Vec<(Seat, Card)>>,
    pub tricks_won: [u8; 2],
    /// Who actually won each trick, for per-player trick markers.
    pub tricks_by_seat: [u8; 4],
    pub scores: [u8; 2],
}

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
pub struct TableView {
    pub table_id: TableId,
    pub table_name: String,
    pub rules: RuleConfig,
    pub role: Role,
    /// Your seat, if seated (redundant with `role`, convenient for clients).
    pub you: Option<Seat>,
    pub seats: [SeatInfo; 4],
    pub spectators: Vec<String>,
    /// None while seating / between games.
    pub game: Option<GameView>,
    /// Your legal actions right now; non-empty exactly when you must act.
    /// Clients and bots should treat this as authoritative and pick from it.
    pub legal: Vec<Action>,
}

pub fn redact(meta: &TableMeta, game: Option<&EuchreGame>, role: Role) -> TableView {
    let you = match role {
        Role::Seated { seat } => Some(seat),
        _ => None,
    };
    let game_view = game.map(|g| GameView {
        phase: g.phase.clone(),
        dealer: g.dealer,
        hand: you.map(|s| g.hand(s).to_vec()).unwrap_or_default(),
        hand_counts: [
            g.hand(Seat(0)).len() as u8,
            g.hand(Seat(1)).len() as u8,
            g.hand(Seat(2)).len() as u8,
            g.hand(Seat(3)).len() as u8,
        ],
        upcard: g.upcard,
        turned_down: g.turned_down,
        trump: g.trump,
        maker: g.maker,
        alone: g.alone,
        sitting_out: g.sitting_out(),
        current_trick: g.current_trick.clone(),
        last_trick: g.last_trick.clone(),
        tricks_won: g.tricks_won,
        tricks_by_seat: g.tricks_by_seat,
        scores: g.scores,
    });
    let legal = match (you, game) {
        (Some(seat), Some(g)) => g.legal_actions(seat),
        _ => Vec::new(),
    };
    TableView {
        table_id: meta.table_id.clone(),
        table_name: meta.table_name.clone(),
        rules: meta.rules,
        role,
        you,
        seats: meta.seats.clone(),
        spectators: meta.spectators.clone(),
        game: game_view,
        legal,
    }
}

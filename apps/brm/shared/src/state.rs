//! The authoritative game state, arena generation, and match-flow transitions.

use serde::{Deserialize, Serialize};
use std::collections::HashSet;

use crate::{
    rng_f32, Map, Phase, Player, PlayerId, Tile, COUNTDOWN_SECS, DEFAULT_BOMBS, DEFAULT_RANGE,
    MAX_NAME_LEN, PLAYER_SPEED,
};

/// Spawn corners, ordered so the first two players take opposite corners.
const SPAWNS: [(i32, i32); 4] = [(1, 1), (11, 9), (11, 1), (1, 9)];

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GameState {
    pub map: Map,
    pub players: Vec<Player>,
    pub bombs: Vec<crate::Bomb>,
    pub explosions: Vec<crate::Explosion>,
    pub powerups: Vec<crate::PowerUp>,
    pub phase: Phase,
    /// Counts down during `Countdown` and `RoundOver`.
    pub phase_timer: f32,
    pub winner: Option<PlayerId>,
    pub tick: u64,
    next_id: PlayerId,
    /// Deterministic RNG cursor (map generation, power-up drops). `pub(crate)` so
    /// [`crate::sim`] can advance it.
    pub(crate) rng: u64,
}

/// Build a classic odd-sized arena: solid border, indestructible pillars on
/// even/even interior coordinates, destructible blocks scattered elsewhere, with
/// the four corners and their neighbors kept clear for spawns.
fn generate_arena(rng: &mut u64) -> Map {
    let (w, h) = (13, 11);
    let mut tiles = vec![Tile::Empty; (w * h) as usize];
    let idx = |x: i32, y: i32| (y * w + x) as usize;

    for y in 0..h {
        for x in 0..w {
            let border = x == 0 || y == 0 || x == w - 1 || y == h - 1;
            let pillar = x % 2 == 0 && y % 2 == 0;
            tiles[idx(x, y)] = if border || pillar { Tile::Wall } else { Tile::Empty };
        }
    }

    // Corners (and their orthogonal neighbors) stay clear so spawns aren't boxed in.
    let mut keep_clear = HashSet::new();
    for &(cx, cy) in &SPAWNS {
        keep_clear.insert((cx, cy));
        keep_clear.insert((cx + 1, cy));
        keep_clear.insert((cx - 1, cy));
        keep_clear.insert((cx, cy + 1));
        keep_clear.insert((cx, cy - 1));
    }

    for y in 1..h - 1 {
        for x in 1..w - 1 {
            if tiles[idx(x, y)] == Tile::Empty
                && !keep_clear.contains(&(x, y))
                && rng_f32(rng) < 0.75
            {
                tiles[idx(x, y)] = Tile::Block;
            }
        }
    }
    Map { w, h, tiles }
}

impl GameState {
    /// A fresh server state: an empty lobby waiting for players.
    pub fn new(seed: u64) -> Self {
        let mut rng = seed.max(1);
        let map = generate_arena(&mut rng);
        GameState {
            map,
            players: Vec::new(),
            bombs: Vec::new(),
            explosions: Vec::new(),
            powerups: Vec::new(),
            phase: Phase::Lobby,
            phase_timer: 0.0,
            winner: None,
            tick: 0,
            next_id: 1,
            rng,
        }
    }

    /// Register a newly connected player at a spawn corner. Joining mid-round
    /// makes them a spectator until the next round.
    pub fn add_player(&mut self) -> PlayerId {
        let slot = self.players.len().min(SPAWNS.len() - 1);
        let (sx, sy) = SPAWNS[slot];
        let id = self.next_id;
        self.next_id += 1;
        let spectating = self.phase != Phase::Lobby;
        self.players.push(Player {
            id,
            name: format!("Player {id}"),
            x: sx as f32 + 0.5,
            y: sy as f32 + 0.5,
            alive: !spectating,
            bombs_max: DEFAULT_BOMBS,
            range: DEFAULT_RANGE,
            speed: PLAYER_SPEED,
            speed_ups: 0,
            color: (id % 8) as u8,
            slot: slot as u8,
            ready: false,
            spectating,
            can_kick: false,
            pierce: false,
            shield: false,
        });
        id
    }

    pub fn remove_player(&mut self, id: PlayerId) {
        self.players.retain(|p| p.id != id);
        // If that was the last participant mid-match (everyone disconnected, or
        // only spectators remain), snap back to the lobby. Otherwise the server
        // sits in a dead, never-ending round and the next joiner is stuck
        // spectating it.
        if self.phase != Phase::Lobby && !self.players.iter().any(|p| !p.spectating) {
            self.return_to_lobby();
        }
    }

    /// Update a player's display name, capped at [`MAX_NAME_LEN`]. Empty names
    /// are ignored so a player always has a label (the default `Player N`).
    pub fn set_name(&mut self, id: PlayerId, name: &str) {
        let name: String = name.chars().take(MAX_NAME_LEN).collect();
        if name.is_empty() {
            return;
        }
        if let Some(p) = self.players.iter_mut().find(|p| p.id == id) {
            p.name = name;
        }
    }

    /// Set up a fresh arena, place every player at a corner with default stats,
    /// and enter the pre-round countdown.
    pub(crate) fn begin_round(&mut self) {
        self.map = generate_arena(&mut self.rng);
        self.bombs.clear();
        self.explosions.clear();
        self.powerups.clear();
        self.winner = None;
        for (i, p) in self.players.iter_mut().enumerate() {
            let slot = i.min(SPAWNS.len() - 1);
            let (sx, sy) = SPAWNS[slot];
            p.x = sx as f32 + 0.5;
            p.y = sy as f32 + 0.5;
            p.slot = slot as u8;
            p.alive = true;
            p.spectating = false;
            p.bombs_max = DEFAULT_BOMBS;
            p.range = DEFAULT_RANGE;
            p.speed = PLAYER_SPEED;
            p.speed_ups = 0;
            p.can_kick = false;
            p.pierce = false;
            p.shield = false;
        }
        self.phase = Phase::Countdown;
        self.phase_timer = COUNTDOWN_SECS;
    }

    /// Tear down the round and return everyone to an un-readied lobby. Spectators
    /// become full lobby members.
    pub(crate) fn return_to_lobby(&mut self) {
        self.bombs.clear();
        self.explosions.clear();
        self.powerups.clear();
        self.winner = None;
        self.phase = Phase::Lobby;
        self.phase_timer = 0.0;
        for p in &mut self.players {
            p.ready = false;
            p.spectating = false;
            p.alive = true;
        }
    }

    pub(crate) fn player_mut(&mut self, id: PlayerId) -> Option<&mut Player> {
        self.players.iter_mut().find(|p| p.id == id)
    }

    /// Empty game on a caller-supplied map, mid-round, used by the simulation
    /// tests to set up precise scenarios.
    #[cfg(test)]
    pub(crate) fn with_map(map: Map) -> Self {
        GameState {
            map,
            players: Vec::new(),
            bombs: Vec::new(),
            explosions: Vec::new(),
            powerups: Vec::new(),
            phase: Phase::Playing,
            phase_timer: 0.0,
            winner: None,
            tick: 0,
            next_id: 1,
            rng: 42,
        }
    }
}

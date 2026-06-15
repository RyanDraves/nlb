//! The authoritative game state and arena generation.

use serde::{Deserialize, Serialize};
use std::collections::HashSet;

use crate::{
    rng_f32, Map, Phase, Player, PlayerId, Tile, DEFAULT_BOMBS, DEFAULT_RANGE, PLAYER_SPEED,
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
    pub winner: Option<PlayerId>,
    pub tick: u64,
    next_id: PlayerId,
    /// Deterministic RNG cursor (power-up drops). `pub(crate)` so [`crate::sim`]
    /// can advance it.
    pub(crate) rng: u64,
}

impl GameState {
    /// Build a classic odd-sized arena: solid border, indestructible pillars on
    /// even/even interior coordinates, destructible blocks scattered elsewhere,
    /// with the four corners and their neighbors kept clear for spawns.
    pub fn new(seed: u64) -> Self {
        let (w, h) = (13, 11);
        let mut rng = seed.max(1);
        let mut tiles = vec![Tile::Empty; (w * h) as usize];
        let idx = |x: i32, y: i32| (y * w + x) as usize;

        for y in 0..h {
            for x in 0..w {
                let border = x == 0 || y == 0 || x == w - 1 || y == h - 1;
                let pillar = x % 2 == 0 && y % 2 == 0;
                tiles[idx(x, y)] = if border || pillar { Tile::Wall } else { Tile::Empty };
            }
        }

        // Corners (and their orthogonal neighbors) stay clear so spawns aren't
        // boxed in.
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
                    && rng_f32(&mut rng) < 0.75
                {
                    tiles[idx(x, y)] = Tile::Block;
                }
            }
        }

        GameState {
            map: Map { w, h, tiles },
            players: Vec::new(),
            bombs: Vec::new(),
            explosions: Vec::new(),
            powerups: Vec::new(),
            phase: Phase::Playing,
            winner: None,
            tick: 0,
            next_id: 1,
            rng,
        }
    }

    /// Add a player at the next free spawn corner. Returns its id.
    pub fn add_player(&mut self) -> PlayerId {
        let slot = self.players.len().min(SPAWNS.len() - 1);
        let (sx, sy) = SPAWNS[slot];
        let id = self.next_id;
        self.next_id += 1;
        self.players.push(Player {
            id,
            x: sx as f32 + 0.5,
            y: sy as f32 + 0.5,
            alive: true,
            bombs_max: DEFAULT_BOMBS,
            range: DEFAULT_RANGE,
            speed: PLAYER_SPEED,
            color: (id % 8) as u8,
        });
        id
    }

    pub fn remove_player(&mut self, id: PlayerId) {
        self.players.retain(|p| p.id != id);
    }

    pub(crate) fn player_mut(&mut self, id: PlayerId) -> Option<&mut Player> {
        self.players.iter_mut().find(|p| p.id == id)
    }

    /// Empty game on a caller-supplied map, used by the simulation tests to set
    /// up precise scenarios.
    #[cfg(test)]
    pub(crate) fn with_map(map: Map) -> Self {
        GameState {
            map,
            players: Vec::new(),
            bombs: Vec::new(),
            explosions: Vec::new(),
            powerups: Vec::new(),
            phase: Phase::Playing,
            winner: None,
            tick: 0,
            next_id: 1,
            rng: 42,
        }
    }
}

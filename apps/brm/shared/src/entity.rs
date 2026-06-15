//! Entities and per-tick input that live inside a [`crate::GameState`].

use serde::{Deserialize, Serialize};

use crate::PlayerId;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Player {
    pub id: PlayerId,
    pub x: f32,
    pub y: f32,
    pub alive: bool,
    pub bombs_max: u32,
    pub range: i32,
    pub speed: f32,
    /// Index into the client's color palette.
    pub color: u8,
}

impl Player {
    /// Tile the player's center currently occupies.
    pub fn tile(&self) -> (i32, i32) {
        (self.x.floor() as i32, self.y.floor() as i32)
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Bomb {
    pub owner: PlayerId,
    pub x: i32,
    pub y: i32,
    pub fuse: f32,
    pub range: i32,
}

/// A burst of flame. All cells share one lifetime so the client can fade them
/// out together.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Explosion {
    pub cells: Vec<(i32, i32)>,
    pub ttl: f32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum PowerKind {
    /// +1 simultaneous bomb.
    ExtraBomb,
    /// +1 blast range.
    Range,
    /// +movement speed.
    Speed,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PowerUp {
    pub x: i32,
    pub y: i32,
    pub kind: PowerKind,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct PlayerInput {
    /// Desired movement direction, components in [-1, 1].
    pub dx: f32,
    pub dy: f32,
    /// True on the frame the player wants to drop a bomb.
    pub place_bomb: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Phase {
    Playing,
    RoundOver,
}

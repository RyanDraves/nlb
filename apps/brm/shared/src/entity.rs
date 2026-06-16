//! Entities and per-tick input that live inside a [`crate::GameState`].

use serde::{Deserialize, Serialize};

use crate::{PlayerId, DEFAULT_BOMBS, DEFAULT_RANGE};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Player {
    pub id: PlayerId,
    /// Player-chosen display name (capped at [`crate::MAX_NAME_LEN`]).
    pub name: String,
    pub x: f32,
    pub y: f32,
    pub alive: bool,
    pub bombs_max: u32,
    pub range: i32,
    pub speed: f32,
    /// Number of Speed power-ups collected (for the stats display).
    pub speed_ups: u8,
    /// Index into the client's color palette.
    pub color: u8,
    /// Spawn corner index (0=TL, 1=BR, 2=TR, 3=BL); positions the stats display.
    pub slot: u8,
    /// Lobby ready state; ignored once a round is in progress.
    pub ready: bool,
    /// Joined while a round was in progress: sits out until the next one.
    pub spectating: bool,
    /// Can push bombs by walking into them (the Kick power-up).
    pub can_kick: bool,
    /// Bombs this player places pierce through blocks (the Pierce power-up).
    pub pierce: bool,
    /// Absorbs the next otherwise-fatal blast (the Shield power-up).
    pub shield: bool,
}

impl Player {
    /// Tile the player's center currently occupies.
    pub fn tile(&self) -> (i32, i32) {
        (self.x.floor() as i32, self.y.floor() as i32)
    }

    /// Currently-held power-up counts in [`PowerKind::ALL`] order, for the
    /// in-game stats display.
    pub fn powerup_counts(&self) -> [u8; 6] {
        [
            self.bombs_max.saturating_sub(DEFAULT_BOMBS) as u8,
            (self.range - DEFAULT_RANGE).max(0) as u8,
            self.speed_ups,
            self.can_kick as u8,
            self.pierce as u8,
            self.shield as u8,
        ]
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Bomb {
    pub owner: PlayerId,
    pub x: i32,
    pub y: i32,
    pub fuse: f32,
    pub range: i32,
    /// Blast continues through (rather than stopping at) destructible blocks.
    pub pierce: bool,
    /// Direction this bomb is sliding after a kick; `(0, 0)` when at rest.
    pub slide_dir: (i32, i32),
    /// Progress in `[0, 1)` toward the next tile while sliding (for smooth
    /// rendering); the bomb's logical position stays on the integer grid.
    pub slide_t: f32,
}

impl Bomb {
    /// A freshly placed, stationary bomb.
    pub fn new(owner: PlayerId, x: i32, y: i32, fuse: f32, range: i32, pierce: bool) -> Self {
        Bomb {
            owner,
            x,
            y,
            fuse,
            range,
            pierce,
            slide_dir: (0, 0),
            slide_t: 0.0,
        }
    }
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
    /// Push bombs by walking into them.
    Kick,
    /// Your bombs' blast pierces through blocks.
    Pierce,
    /// Survive the next otherwise-fatal blast.
    Shield,
}

impl PowerKind {
    /// All kinds, in palette/sprite-sheet order.
    pub const ALL: [PowerKind; 6] = [
        PowerKind::ExtraBomb,
        PowerKind::Range,
        PowerKind::Speed,
        PowerKind::Kick,
        PowerKind::Pierce,
        PowerKind::Shield,
    ];
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
    /// Players are joining and readying up.
    Lobby,
    /// Everyone is ready; the arena is set up and a 3-2-1 timer is running.
    Countdown,
    /// A round is in progress.
    Playing,
    /// The round ended; the winner is shown before returning to the lobby.
    RoundOver,
}

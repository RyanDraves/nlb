//! Gameplay tunables. Distances are in tile units (one tile == 1.0); the client
//! scales these to pixels at render time.

/// Half-extent of a player's collision box. Smaller than 0.5 so a player fits
/// comfortably inside a single tile lane.
pub const PLAYER_R: f32 = 0.35;
/// Player movement speed in tiles/second.
pub const PLAYER_SPEED: f32 = 4.5;
/// Seconds from placement until a bomb detonates.
pub const BOMB_FUSE: f32 = 2.5;
/// Seconds an explosion's flames linger (used for rendering and kills).
pub const EXPLOSION_TTL: f32 = 0.5;
/// Tiles a fresh player's blast reaches in each direction.
pub const DEFAULT_RANGE: i32 = 2;
/// Bombs a fresh player may have live at once.
pub const DEFAULT_BOMBS: u32 = 1;
/// Probability a destroyed block reveals a power-up.
pub const POWERUP_CHANCE: f32 = 0.35;
/// Speed (tiles/second) a kicked bomb slides across the floor.
pub const KICK_SPEED: f32 = 6.0;
/// Seconds of 3-2-1 countdown after everyone readies, before a round begins.
pub const COUNTDOWN_SECS: f32 = 3.0;
/// Seconds the winner is shown before the match auto-returns to the lobby.
pub const ROUNDOVER_SECS: f32 = 4.0;
/// Maximum length of a player's chosen display name.
pub const MAX_NAME_LEN: usize = 15;

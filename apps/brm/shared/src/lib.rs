//! Shared, deterministic Bomberman game model + wire protocol.
//!
//! This crate is pure logic with no I/O so it compiles identically for the
//! native server, the native client, and the wasm browser client. The server
//! is authoritative: it owns a [`GameState`] and advances it with [`step`].

mod entity;
mod map;
mod protocol;
mod sim;
mod state;
mod tuning;

#[cfg(test)]
mod tests;

pub use entity::*;
pub use map::*;
pub use protocol::*;
pub use sim::step;
pub use state::GameState;
pub use tuning::*;

/// Stable identifier the server assigns to each connected player.
pub type PlayerId = u32;

/// Cheap deterministic xorshift returning a value in `[0, 1)`. Shared with the
/// other games via `lrb_rng` (bit-identical sequence); both map generation
/// ([`state`]) and power-up drops ([`sim`]) advance the same RNG.
pub(crate) use lrb_rng::next_f32 as rng_f32;

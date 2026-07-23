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

/// Cheap deterministic xorshift returning a value in `[0, 1)`. Lives at the
/// crate root because both map generation ([`state`]) and power-up drops
/// ([`sim`]) advance the same RNG.
pub(crate) fn rng_f32(state: &mut u64) -> f32 {
    *state ^= *state << 13;
    *state ^= *state >> 7;
    *state ^= *state << 17;
    ((*state >> 40) as f32) / (1u64 << 24) as f32
}

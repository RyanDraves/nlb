//! The client/server wire protocol. Encoding (bincode) is the caller's
//! responsibility so this crate stays dependency-light and wasm-friendly.

use serde::{Deserialize, Serialize};

use crate::{GameState, PlayerId, PlayerInput};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum ClientMsg {
    Join { name: String },
    Input(PlayerInput),
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum ServerMsg {
    Welcome { id: PlayerId },
    Snapshot(GameState),
}

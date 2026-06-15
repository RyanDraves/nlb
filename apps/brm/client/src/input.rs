//! Keyboard bindings for local (couch) players and per-frame input sampling.

use brm_shared::PlayerInput;
use macroquad::prelude::*;

#[derive(Clone, Copy)]
pub struct Binds {
    up: KeyCode,
    down: KeyCode,
    left: KeyCode,
    right: KeyCode,
    bomb: KeyCode,
}

/// Couch bindings: player 1 on WASD+Space, player 2 on arrows+Enter.
pub const BINDS: [Binds; 2] = [
    Binds { up: KeyCode::W, down: KeyCode::S, left: KeyCode::A, right: KeyCode::D, bomb: KeyCode::Space },
    Binds { up: KeyCode::Up, down: KeyCode::Down, left: KeyCode::Left, right: KeyCode::Right, bomb: KeyCode::Enter },
];

/// Sample one player's input this frame. Movement is held; `place_bomb` is
/// edge-triggered so a held bomb key drops a single bomb.
pub fn read_input(b: &Binds) -> PlayerInput {
    let mut dx = 0.0;
    let mut dy = 0.0;
    if is_key_down(b.left) {
        dx -= 1.0;
    }
    if is_key_down(b.right) {
        dx += 1.0;
    }
    if is_key_down(b.up) {
        dy -= 1.0;
    }
    if is_key_down(b.down) {
        dy += 1.0;
    }
    PlayerInput { dx, dy, place_bomb: is_key_pressed(b.bomb) }
}

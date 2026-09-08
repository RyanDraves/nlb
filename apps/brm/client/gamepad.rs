//! Native controller support via gilrs. This module is compiled only for the
//! native client (`mod gamepad` is cfg-gated in main.rs); the web client reads
//! the browser Gamepad API through `web.rs`/`brm_net.js` instead.
//!
//! Each connected controller becomes its own player (its own server
//! connection), hot-plugged in and out at runtime. Movement comes from the left
//! stick or D-pad; the South button (A / Cross) drops a bomb and readies up,
//! mirroring the keyboard's bomb key.

use std::collections::HashSet;

use brm_shared::PlayerInput;
use gilrs::{Axis, Button, EventType, Gilrs};

pub use gilrs::GamepadId;

/// A controller connecting or disconnecting this frame, so the client can add or
/// remove the matching player.
pub enum Hotplug {
    Connected(GamepadId),
    Disconnected(GamepadId),
}

/// Stick magnitude below which we treat the axis as centered (sticks rarely rest
/// at exactly zero).
const DEADZONE: f32 = 0.35;

pub struct Pads {
    /// `None` if no gamepad subsystem is available — then everything is inert.
    gilrs: Option<Gilrs>,
    /// Controllers whose bomb button went down *this frame* (edge-triggered, so
    /// holding A drops a single bomb / toggles ready once).
    bomb_edges: HashSet<GamepadId>,
}

impl Pads {
    pub fn new() -> Self {
        let gilrs = match Gilrs::new() {
            Ok(g) => Some(g),
            Err(e) => {
                macroquad::prelude::error!("gamepad subsystem unavailable: {e}");
                None
            }
        };
        Pads { gilrs, bomb_edges: HashSet::new() }
    }

    /// Controllers already connected at startup (gilrs reports these from its
    /// initial state rather than as `Connected` events).
    pub fn connected_ids(&self) -> Vec<GamepadId> {
        match &self.gilrs {
            Some(g) => g.gamepads().map(|(id, _)| id).collect(),
            None => Vec::new(),
        }
    }

    /// Drain this frame's gilrs events: refresh cached pad state (needed for
    /// `read`), record bomb-button edges, and surface connect/disconnect changes.
    pub fn poll(&mut self) -> Vec<Hotplug> {
        self.bomb_edges.clear();
        let mut changes = Vec::new();
        let Some(gilrs) = self.gilrs.as_mut() else {
            return changes;
        };
        while let Some(ev) = gilrs.next_event() {
            match ev.event {
                EventType::Connected => changes.push(Hotplug::Connected(ev.id)),
                EventType::Disconnected => changes.push(Hotplug::Disconnected(ev.id)),
                EventType::ButtonPressed(Button::South, _) => {
                    self.bomb_edges.insert(ev.id);
                }
                _ => {}
            }
        }
        changes
    }

    /// Sample one controller's input. Left stick or D-pad drives movement;
    /// `place_bomb` is the bomb-button edge recorded in the last `poll`.
    pub fn read(&self, id: GamepadId) -> PlayerInput {
        let Some(gilrs) = self.gilrs.as_ref() else {
            return PlayerInput::default();
        };
        let gp = gilrs.gamepad(id);
        let mut dx = gp.value(Axis::LeftStickX);
        // gilrs sticks are +Y up; the game's +Y is down.
        let mut dy = -gp.value(Axis::LeftStickY);
        if dx.abs() < DEADZONE {
            dx = 0.0;
        }
        if dy.abs() < DEADZONE {
            dy = 0.0;
        }
        // The D-pad overrides the stick (full deflection, exact directions).
        if gp.is_pressed(Button::DPadLeft) {
            dx = -1.0;
        }
        if gp.is_pressed(Button::DPadRight) {
            dx = 1.0;
        }
        if gp.is_pressed(Button::DPadUp) {
            dy = -1.0;
        }
        if gp.is_pressed(Button::DPadDown) {
            dy = 1.0;
        }
        PlayerInput { dx, dy, place_bomb: self.bomb_edges.contains(&id) }
    }
}

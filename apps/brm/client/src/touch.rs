//! On-screen touch controls for mobile: a floating joystick on the left and a
//! bomb/action button on the lower right. Reads macroquad's `touches()`, so it
//! works on the web client on phones (and is simply inert when there are no
//! touches).

use brm_shared::PlayerInput;
use macroquad::prelude::*;

/// Persistent state for the floating joystick (the active drag).
pub struct Touch {
    /// Id of the touch currently driving the joystick, if any.
    move_id: Option<u64>,
    origin: Vec2,
    current: Vec2,
}

impl Touch {
    pub fn new() -> Self {
        Touch {
            move_id: None,
            origin: Vec2::ZERO,
            current: Vec2::ZERO,
        }
    }

    /// Radius of the joystick's travel (also its drawn base radius).
    fn radius() -> f32 {
        screen_width().min(screen_height()) * 0.13
    }

    /// Bomb button center and radius (lower-right).
    fn bomb_button() -> (Vec2, f32) {
        let r = screen_width().min(screen_height()) * 0.11;
        let m = r * 1.4;
        (vec2(screen_width() - m, screen_height() - m), r)
    }

    /// Resting joystick base position (lower-left) when not being dragged.
    fn rest_base() -> Vec2 {
        let r = Self::radius();
        vec2(r * 1.4, screen_height() - r * 1.4)
    }

    /// Process this frame's touches and produce the resulting input. A tap on
    /// the bomb button is an edge (`place_bomb` true for that frame); dragging
    /// anywhere on the left drives movement.
    pub fn update(&mut self) -> PlayerInput {
        let (bomb_c, bomb_r) = Self::bomb_button();
        let mut place_bomb = false;

        for t in touches() {
            let on_bomb = (t.position - bomb_c).length() <= bomb_r;
            match t.phase {
                TouchPhase::Started => {
                    if on_bomb {
                        place_bomb = true;
                    } else if self.move_id.is_none() && t.position.x < screen_width() * 0.6 {
                        self.move_id = Some(t.id);
                        self.origin = t.position;
                        self.current = t.position;
                    }
                }
                TouchPhase::Moved | TouchPhase::Stationary => {
                    if self.move_id == Some(t.id) {
                        self.current = t.position;
                    }
                }
                TouchPhase::Ended | TouchPhase::Cancelled => {
                    if self.move_id == Some(t.id) {
                        self.move_id = None;
                    }
                }
            }
        }

        let (mut dx, mut dy) = (0.0, 0.0);
        if self.move_id.is_some() {
            let v = (self.current - self.origin) / Self::radius();
            let len = v.length();
            if len > 0.18 {
                // deadzone
                let v = if len > 1.0 { v / len } else { v };
                dx = v.x;
                dy = v.y;
            }
        }
        PlayerInput { dx, dy, place_bomb }
    }

    /// Draw the controls. The joystick is only shown while in a round
    /// (`show_joystick`); the bomb button is always shown (it also readies up in
    /// the lobby).
    pub fn draw(&self, show_joystick: bool) {
        let (bomb_c, bomb_r) = Self::bomb_button();
        draw_circle(bomb_c.x, bomb_c.y, bomb_r, Color::new(1.0, 0.45, 0.35, 0.22));
        draw_circle_lines(bomb_c.x, bomb_c.y, bomb_r, 3.0, Color::new(1.0, 0.55, 0.45, 0.6));
        draw_circle(bomb_c.x, bomb_c.y, bomb_r * 0.32, Color::new(0.12, 0.12, 0.14, 0.8));

        if show_joystick {
            let rad = Self::radius();
            let base = if self.move_id.is_some() { self.origin } else { Self::rest_base() };
            let knob = if self.move_id.is_some() { self.current } else { base };
            let knob = base + (knob - base).clamp_length_max(rad);
            draw_circle_lines(base.x, base.y, rad, 3.0, Color::new(1.0, 1.0, 1.0, 0.22));
            draw_circle(knob.x, knob.y, rad * 0.45, Color::new(1.0, 1.0, 1.0, 0.30));
        }
    }
}

//! Pixel-art 2.5D rendering of the game state with macroquad.

use brm_shared::*;
use macroquad::prelude::*;

const BG: Color = Color::new(0.09, 0.09, 0.12, 1.0);
const FLOOR: Color = Color::new(0.16, 0.17, 0.21, 1.0);
const FLOOR_ALT: Color = Color::new(0.19, 0.20, 0.25, 1.0);
const WALL_TOP: Color = Color::new(0.45, 0.47, 0.53, 1.0);
const WALL_SIDE: Color = Color::new(0.30, 0.32, 0.37, 1.0);
const BLOCK_TOP: Color = Color::new(0.55, 0.40, 0.28, 1.0);
const BLOCK_SIDE: Color = Color::new(0.38, 0.27, 0.18, 1.0);

/// Draw one frame: the board if we have a snapshot, otherwise a connecting
/// message. `my_ids` are the local players' ids, marked with a triangle.
pub fn frame(latest: &Option<GameState>, my_ids: &[PlayerId]) {
    clear_background(BG);
    match latest {
        Some(gs) => draw_game(gs, my_ids),
        None => center_text("Connecting to server...", 28.0, LIGHTGRAY),
    }
}

// 8-color player palette, indexed by `Player::color`.
fn player_color(i: u8) -> Color {
    match i % 8 {
        0 => Color::from_rgba(0xE6, 0x39, 0x46, 0xff), // red
        1 => Color::from_rgba(0x45, 0x7B, 0x9D, 0xff), // blue
        2 => Color::from_rgba(0x2A, 0x9D, 0x8F, 0xff), // teal
        3 => Color::from_rgba(0xE9, 0xC4, 0x6A, 0xff), // yellow
        4 => Color::from_rgba(0x9B, 0x5D, 0xE5, 0xff), // purple
        5 => Color::from_rgba(0xF1, 0x5B, 0xB5, 0xff), // pink
        6 => Color::from_rgba(0x43, 0xAA, 0x8B, 0xff), // green
        _ => Color::from_rgba(0xF3, 0x72, 0x2C, 0xff), // orange
    }
}

/// Pixels-per-tile and the top-left origin that centers the board on screen.
fn layout(map: &Map) -> (f32, f32, f32) {
    let ts = (screen_width() / map.w as f32)
        .min(screen_height() / map.h as f32)
        .floor();
    let ox = (screen_width() - ts * map.w as f32) / 2.0;
    let oy = (screen_height() - ts * map.h as f32) / 2.0;
    (ts, ox, oy)
}

fn draw_game(gs: &GameState, my_ids: &[PlayerId]) {
    let (ts, ox, oy) = layout(&gs.map);
    // Faux-height for the 2.5D look: solid tiles get a "front face" strip.
    let lip = ts * 0.18;

    // Floor + solid tiles.
    for y in 0..gs.map.h {
        for x in 0..gs.map.w {
            let px = ox + x as f32 * ts;
            let py = oy + y as f32 * ts;
            match gs.map.get(x, y) {
                Tile::Empty => {
                    let c = if (x + y) % 2 == 0 { FLOOR } else { FLOOR_ALT };
                    draw_rectangle(px, py, ts, ts, c);
                }
                Tile::Wall => draw_block(px, py, ts, lip, WALL_TOP, WALL_SIDE),
                Tile::Block => draw_block(px, py, ts, lip, BLOCK_TOP, BLOCK_SIDE),
            }
        }
    }

    // Power-ups: small diamonds.
    for p in &gs.powerups {
        let cx = ox + (p.x as f32 + 0.5) * ts;
        let cy = oy + (p.y as f32 + 0.5) * ts;
        let c = match p.kind {
            PowerKind::ExtraBomb => Color::new(0.95, 0.45, 0.45, 1.0),
            PowerKind::Range => Color::new(0.95, 0.75, 0.35, 1.0),
            PowerKind::Speed => Color::new(0.45, 0.85, 0.95, 1.0),
        };
        draw_poly(cx, cy, 4, ts * 0.28, 45.0, c);
    }

    // Bombs: dark spheres with a pulsing highlight.
    for b in &gs.bombs {
        let cx = ox + (b.x as f32 + 0.5) * ts;
        let cy = oy + (b.y as f32 + 0.5) * ts;
        let pulse = 0.5 + 0.5 * (get_time() as f32 * 6.0).sin();
        draw_circle(cx, cy + ts * 0.12, ts * 0.34, Color::new(0.0, 0.0, 0.0, 0.25)); // shadow
        draw_circle(cx, cy, ts * 0.32, Color::new(0.12, 0.12, 0.14, 1.0));
        draw_circle(cx - ts * 0.1, cy - ts * 0.1, ts * 0.08, Color::new(0.9, 0.5, 0.3, 0.4 + 0.4 * pulse));
    }

    // Explosions: bright flame cells.
    for e in &gs.explosions {
        let a = (e.ttl / EXPLOSION_TTL).clamp(0.0, 1.0);
        for &(x, y) in &e.cells {
            let px = ox + x as f32 * ts;
            let py = oy + y as f32 * ts;
            draw_rectangle(px, py, ts, ts, Color::new(1.0, 0.6, 0.2, 0.85 * a));
            draw_rectangle(px + ts * 0.2, py + ts * 0.2, ts * 0.6, ts * 0.6, Color::new(1.0, 0.9, 0.5, 0.9 * a));
        }
    }

    // Players: shadow + body + own-player marker.
    for p in &gs.players {
        if !p.alive {
            continue;
        }
        let cx = ox + p.x * ts;
        let cy = oy + p.y * ts;
        draw_circle(cx, cy + ts * 0.18, ts * 0.3, Color::new(0.0, 0.0, 0.0, 0.25));
        draw_circle(cx, cy, ts * 0.32, player_color(p.color));
        draw_circle_lines(cx, cy, ts * 0.32, 2.0, Color::new(0.0, 0.0, 0.0, 0.4));
        if my_ids.contains(&p.id) {
            // Little triangle marker above your own character.
            draw_triangle(
                Vec2::new(cx, cy - ts * 0.5),
                Vec2::new(cx - ts * 0.12, cy - ts * 0.72),
                Vec2::new(cx + ts * 0.12, cy - ts * 0.72),
                WHITE,
            );
        }
    }

    // Round-over banner.
    if gs.phase == Phase::RoundOver {
        let msg = match gs.winner {
            Some(id) => format!("Player {id} wins!"),
            None => "Draw!".to_owned(),
        };
        center_text(&msg, 40.0, WHITE);
    }
}

fn draw_block(px: f32, py: f32, ts: f32, lip: f32, top: Color, side: Color) {
    draw_rectangle(px, py + ts - lip, ts, lip, side);
    draw_rectangle(px, py, ts, ts - lip, top);
}

fn center_text(text: &str, size: f32, color: Color) {
    let d = measure_text(text, None, size as u16, 1.0);
    draw_text(
        text,
        (screen_width() - d.width) / 2.0,
        screen_height() / 2.0,
        size,
        color,
    );
}

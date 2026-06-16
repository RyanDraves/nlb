//! Pixel-art 2.5D rendering of the game state with macroquad.

use brm_shared::*;
use macroquad::prelude::*;

/// Width/height of one power-up icon in the sprite sheet.
const SPRITE: f32 = 32.0;

/// GPU textures, loaded once after the window opens.
pub struct Assets {
    /// Horizontal strip of power-up icons, one per [`PowerKind`] in
    /// [`PowerKind::ALL`] order.
    powerups: Texture2D,
}

impl Assets {
    pub fn load() -> Assets {
        let powerups = Texture2D::from_file_with_format(
            include_bytes!("../../assets/powerups.png"),
            None,
        );
        powerups.set_filter(FilterMode::Nearest); // crisp pixel-art scaling
        Assets { powerups }
    }
}

const BG: Color = Color::new(0.09, 0.09, 0.12, 1.0);
const FLOOR: Color = Color::new(0.16, 0.17, 0.21, 1.0);
const FLOOR_ALT: Color = Color::new(0.19, 0.20, 0.25, 1.0);
const WALL_TOP: Color = Color::new(0.45, 0.47, 0.53, 1.0);
const WALL_SIDE: Color = Color::new(0.30, 0.32, 0.37, 1.0);
const BLOCK_TOP: Color = Color::new(0.55, 0.40, 0.28, 1.0);
const BLOCK_SIDE: Color = Color::new(0.38, 0.27, 0.18, 1.0);

/// Draw one frame for the current match phase. `my_ids` are the local players'
/// ids (marked with a triangle in-game, and "(you)" in the lobby).
pub fn frame(
    assets: &Assets,
    latest: &Option<GameState>,
    my_ids: &[PlayerId],
    editing: Option<PlayerId>,
) {
    clear_background(BG);
    let gs = match latest {
        Some(gs) => gs,
        None => {
            center_text("Connecting to server...", 28.0, LIGHTGRAY);
            return;
        }
    };
    match gs.phase {
        Phase::Lobby => draw_lobby(gs, my_ids, editing),
        Phase::Countdown => {
            draw_game(assets, gs, my_ids);
            dim();
            let n = gs.phase_timer.ceil().max(0.0) as i32;
            center_text(&n.to_string(), 120.0, WHITE);
        }
        Phase::Playing => draw_game(assets, gs, my_ids),
        Phase::RoundOver => {
            draw_game(assets, gs, my_ids);
            dim();
            let msg = match gs.winner {
                Some(id) => {
                    let name = gs
                        .players
                        .iter()
                        .find(|p| p.id == id)
                        .map(|p| p.name.as_str())
                        .unwrap_or("Someone");
                    format!("{name} wins!")
                }
                None => "Round over!".to_owned(),
            };
            center_text_at(&msg, screen_height() / 2.0 - 20.0, 48.0, WHITE);
            center_text_at(
                "returning to lobby...",
                screen_height() / 2.0 + 30.0,
                24.0,
                LIGHTGRAY,
            );
        }
    }
}

/// A translucent black scrim drawn over the board for overlay text.
fn dim() {
    draw_rectangle(0.0, 0.0, screen_width(), screen_height(), Color::new(0.0, 0.0, 0.0, 0.5));
}

/// The lobby / start screen: title, the roster with ready/typing states, and
/// how to edit your name and ready up. `editing` is the id of the local player
/// (if any) currently typing their name.
fn draw_lobby(gs: &GameState, my_ids: &[PlayerId], editing: Option<PlayerId>) {
    let cx = screen_width() / 2.0;
    center_text_at("BRM", 110.0, 72.0, WHITE);
    center_text_at("LOBBY", 165.0, 28.0, LIGHTGRAY);

    // Blink the caret with a steady-width character so the row doesn't jitter.
    let caret = if (get_time() * 3.0).sin() > 0.0 { '|' } else { ' ' };

    let mut y = 240.0;
    if gs.players.is_empty() {
        center_text_at("waiting for players...", y, 26.0, GRAY);
    }
    for p in &gs.players {
        let you = my_ids.contains(&p.id);
        let is_editing = Some(p.id) == editing;
        let mut name = p.name.clone();
        if is_editing {
            name.push(caret); // caret sits at the end: typing appends here
        }
        let label = format!("{}{}", name, if you { "  (you)" } else { "" });
        let dims = measure_text(&label, None, 30, 1.0);
        let block_w = dims.width.max(160.0);
        let row_left = cx - block_w / 2.0 - 56.0;
        draw_circle(row_left, y - 9.0, 12.0, player_color(p.color));
        let name_col = if is_editing || you { WHITE } else { LIGHTGRAY };
        draw_text(&label, row_left + 24.0, y, 30.0, name_col);
        let (status, col) = if p.ready {
            ("READY", Color::new(0.45, 0.85, 0.5, 1.0))
        } else if is_editing {
            ("typing", Color::new(0.95, 0.82, 0.40, 1.0))
        } else {
            ("...", GRAY)
        };
        draw_text(status, row_left + block_w + 40.0, y, 28.0, col);
        y += 44.0;
    }

    center_text_at("press E to edit your name", screen_height() - 110.0, 22.0, LIGHTGRAY);
    center_text_at(
        "press your bomb key to ready up",
        screen_height() - 84.0,
        22.0,
        LIGHTGRAY,
    );
    center_text_at("Space = P1     Enter = P2", screen_height() - 58.0, 20.0, GRAY);
    center_text_at(
        "match starts when everyone is ready",
        screen_height() - 32.0,
        18.0,
        GRAY,
    );
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

/// Reserved top/bottom margin (px) for the per-player stats so the board never
/// fills the whole window (which would leave nowhere to draw them).
const STATS_MARGIN: f32 = 58.0;

/// Pixels-per-tile and the top-left origin that centers the board on screen,
/// keeping `STATS_MARGIN` of headroom top and bottom.
fn layout(map: &Map) -> (f32, f32, f32) {
    let avail_h = (screen_height() - 2.0 * STATS_MARGIN).max(1.0);
    let ts = (screen_width() / map.w as f32)
        .min(avail_h / map.h as f32)
        .floor()
        .max(1.0);
    let ox = (screen_width() - ts * map.w as f32) / 2.0;
    let oy = (screen_height() - ts * map.h as f32) / 2.0;
    (ts, ox, oy)
}

/// Sprite-sheet cell index for a power-up kind (matches `PowerKind::ALL`).
fn powerup_cell(kind: PowerKind) -> usize {
    PowerKind::ALL.iter().position(|&k| k == kind).unwrap_or(0)
}

fn draw_game(assets: &Assets, gs: &GameState, my_ids: &[PlayerId]) {
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

    // Power-ups: sprite-sheet icons that bob and glow.
    let t = get_time() as f32;
    for p in &gs.powerups {
        let cx = ox + (p.x as f32 + 0.5) * ts;
        let cy = oy + (p.y as f32 + 0.5) * ts + (t * 3.0 + p.x as f32).sin() * ts * 0.06;
        let size = ts * 0.8;
        // Soft glow behind the icon.
        draw_circle(cx, cy, size * 0.62, Color::new(1.0, 1.0, 1.0, 0.08));
        draw_texture_ex(
            &assets.powerups,
            cx - size / 2.0,
            cy - size / 2.0,
            WHITE,
            DrawTextureParams {
                dest_size: Some(vec2(size, size)),
                source: Some(Rect::new(powerup_cell(p.kind) as f32 * SPRITE, 0.0, SPRITE, SPRITE)),
                ..Default::default()
            },
        );
    }

    // Bombs: dark spheres with a pulsing highlight, drawn at their slid position.
    for b in &gs.bombs {
        let fx = b.x as f32 + b.slide_dir.0 as f32 * b.slide_t;
        let fy = b.y as f32 + b.slide_dir.1 as f32 * b.slide_t;
        let cx = ox + (fx + 0.5) * ts;
        let cy = oy + (fy + 0.5) * ts;
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
        // Shield: a pulsing cyan ring around the body.
        if p.shield {
            let a = 0.5 + 0.5 * (t * 4.0).sin();
            draw_circle_lines(cx, cy, ts * 0.42, 2.5, Color::new(0.5, 0.9, 1.0, 0.5 + 0.4 * a));
        }
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

    draw_stats(assets, gs, ts, ox, oy);
}

/// Per-player name + collected power-ups, drawn in the screen margin by each
/// player's spawn corner. Skipped when the margin is too thin (e.g. a short
/// landscape phone) to avoid crowding the board.
fn draw_stats(assets: &Assets, gs: &GameState, ts: f32, ox: f32, oy: f32) {
    if oy < 48.0 {
        return;
    }
    let board_w = gs.map.w as f32 * ts;
    let bottom = oy + gs.map.h as f32 * ts;
    let icon = 18.0;
    let cell = icon + 16.0; // icon + count label

    for p in &gs.players {
        if p.spectating {
            continue;
        }
        let top = p.slot == 0 || p.slot == 2;
        let left = p.slot == 0 || p.slot == 3;
        let (name_y, icons_y) = if top {
            (18.0, 26.0)
        } else {
            (bottom + 20.0, bottom + 28.0)
        };

        // Name, anchored to the corner's side.
        let nd = measure_text(&p.name, None, 18, 1.0);
        let name_x = if left { ox } else { ox + board_w - nd.width };
        draw_text(&p.name, name_x, name_y, 18.0, player_color(p.color));

        // Owned power-ups (icon + count), only kinds with a count.
        let counts = p.powerup_counts();
        let owned: Vec<(usize, u8)> = counts
            .iter()
            .enumerate()
            .filter(|(_, &c)| c > 0)
            .map(|(i, &c)| (i, c))
            .collect();
        let total = owned.len() as f32 * cell;
        let mut x = if left { ox } else { ox + board_w - total };
        for (i, c) in owned {
            draw_texture_ex(
                &assets.powerups,
                x,
                icons_y,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(vec2(icon, icon)),
                    source: Some(Rect::new(i as f32 * SPRITE, 0.0, SPRITE, SPRITE)),
                    ..Default::default()
                },
            );
            draw_text(&format!("{c}"), x + icon + 1.0, icons_y + icon - 3.0, 16.0, WHITE);
            x += cell;
        }
    }
}

fn draw_block(px: f32, py: f32, ts: f32, lip: f32, top: Color, side: Color) {
    draw_rectangle(px, py + ts - lip, ts, lip, side);
    draw_rectangle(px, py, ts, ts - lip, top);
}

fn center_text(text: &str, size: f32, color: Color) {
    center_text_at(text, screen_height() / 2.0, size, color);
}

/// Horizontally centered text with a caller-chosen baseline `y`.
fn center_text_at(text: &str, y: f32, size: f32, color: Color) {
    let d = measure_text(text, None, size as u16, 1.0);
    draw_text(text, (screen_width() - d.width) / 2.0, y, size, color);
}

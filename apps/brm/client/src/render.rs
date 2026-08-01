//! Pixel-art 2.5D rendering of the game state with macroquad.

use std::cell::RefCell;
use std::collections::HashMap;

use brm_shared::*;
use macroquad::prelude::*;

/// Width/height of one power-up icon in the sprite sheet.
const SPRITE: f32 = 32.0;

/// Per-player animation state, tracked across frames so characters can face
/// their movement direction and play a walk cycle. Kept render-side because the
/// snapshot only carries positions, not velocity.
struct Anim {
    /// Last seen board position, to derive movement between frames.
    px: f32,
    py: f32,
    /// Facing direction (unit-ish), last nonzero movement. Defaults to "down".
    face: Vec2,
    /// Walk-cycle phase, advanced only while moving.
    walk: f32,
    /// `get_time()` of the last detected movement (for a short "still moving"
    /// grace window, so the 30 Hz snapshot cadence doesn't strobe the legs).
    last_move: f64,
}

/// GPU textures + animation state, created once after the window opens.
pub struct Assets {
    /// Horizontal strip of power-up icons, one per [`PowerKind`] in
    /// [`PowerKind::ALL`] order.
    powerups: Texture2D,
    /// Per-player walk/facing state. `RefCell` for interior mutability so the
    /// render path can keep `&Assets`.
    anim: RefCell<HashMap<PlayerId, Anim>>,
}

impl Assets {
    pub fn load() -> Assets {
        let powerups = Texture2D::from_file_with_format(
            include_bytes!("../../assets/powerups.png"),
            None,
        );
        powerups.set_filter(FilterMode::Nearest); // crisp pixel-art scaling
        Assets { powerups, anim: RefCell::new(HashMap::new()) }
    }
}

const BG: Color = Color::new(0.09, 0.09, 0.12, 1.0);
const FLOOR: Color = Color::new(0.16, 0.17, 0.21, 1.0);
const FLOOR_ALT: Color = Color::new(0.19, 0.20, 0.25, 1.0);
const WALL_TOP: Color = Color::new(0.47, 0.50, 0.57, 1.0);
const WALL_HI: Color = Color::new(0.60, 0.63, 0.70, 1.0);
const WALL_SIDE: Color = Color::new(0.29, 0.31, 0.37, 1.0);
const CRATE_TOP: Color = Color::new(0.60, 0.43, 0.28, 1.0);
const CRATE_HI: Color = Color::new(0.72, 0.54, 0.36, 1.0);
const CRATE_SIDE: Color = Color::new(0.40, 0.27, 0.17, 1.0);
const CRATE_LINE: Color = Color::new(0.30, 0.20, 0.12, 1.0);

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
    center_text_at("Space = P1   Enter = P2   A = controller", screen_height() - 58.0, 20.0, GRAY);
    center_text_at(
        "match starts when everyone is ready",
        screen_height() - 32.0,
        18.0,
        GRAY,
    );
}

/// Native-only lobby menu line: controllers connected and the active number of
/// split-keyboard players (toggle with 0/1/2). Drawn over the shared lobby.
#[cfg(not(target_arch = "wasm32"))]
pub fn lobby_status(controllers: usize, keyboard: usize) {
    let t = format!("controllers: {controllers}    keyboard players: {keyboard}   (0 / 1 / 2)");
    center_text_at(&t, 202.0, 20.0, SKYBLUE);
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
                Tile::Empty => draw_floor(px, py, ts, (x + y) % 2 == 0),
                Tile::Wall => draw_wall(px, py, ts, lip),
                Tile::Block => draw_crate(px, py, ts, lip),
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

    // Bombs: a classic black bomb with a lit, flickering fuse that quickens and
    // reddens as the fuse runs down. Drawn at the (possibly sliding) position.
    for b in &gs.bombs {
        let fx = b.x as f32 + b.slide_dir.0 as f32 * b.slide_t;
        let fy = b.y as f32 + b.slide_dir.1 as f32 * b.slide_t;
        draw_bomb(ox + (fx + 0.5) * ts, oy + (fy + 0.5) * ts, ts, b.fuse);
    }

    // Explosions: layered, flickering flames; neighboring cells overlap into a
    // continuous blast.
    for e in &gs.explosions {
        let a = (e.ttl / EXPLOSION_TTL).clamp(0.0, 1.0);
        for &(x, y) in &e.cells {
            draw_flame(ox + (x as f32 + 0.5) * ts, oy + (y as f32 + 0.5) * ts, ts, a, x, y);
        }
    }

    // Players: animated characters that face their movement and bob as they walk.
    let now = get_time();
    let dt = get_frame_time();
    let mut anim = assets.anim.borrow_mut();
    anim.retain(|id, _| gs.players.iter().any(|p| p.id == *id));
    for p in &gs.players {
        let a = anim.entry(p.id).or_insert(Anim {
            px: p.x,
            py: p.y,
            face: vec2(0.0, 1.0),
            walk: 0.0,
            last_move: 0.0,
        });
        let d = vec2(p.x - a.px, p.y - a.py);
        if d.length() > 0.0005 {
            a.face = d.normalize();
            a.last_move = now;
            a.walk += dt * 10.0;
        }
        a.px = p.x;
        a.py = p.y;
        if !p.alive {
            continue;
        }
        // A short grace window keeps the legs moving between 30 Hz snapshots.
        let moving = now - a.last_move < 0.18;
        draw_player(
            ox + p.x * ts,
            oy + p.y * ts,
            ts,
            player_color(p.color),
            a.face,
            a.walk,
            moving,
            p.shield,
            my_ids.contains(&p.id),
        );
    }
    drop(anim);

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

/// Linear blend from `c` toward `o` by `t` (keeps `c`'s alpha).
fn mix(c: Color, o: Color, t: f32) -> Color {
    Color::new(
        c.r + (o.r - c.r) * t,
        c.g + (o.g - c.g) * t,
        c.b + (o.b - c.b) * t,
        c.a,
    )
}

fn draw_floor(px: f32, py: f32, ts: f32, alt: bool) {
    draw_rectangle(px, py, ts, ts, if alt { FLOOR } else { FLOOR_ALT });
    // Faint seams give the floor a tiled feel without a texture.
    let seam = Color::new(0.0, 0.0, 0.0, 0.06);
    draw_line(px, py + ts, px + ts, py + ts, 1.0, seam);
    draw_line(px + ts, py, px + ts, py + ts, 1.0, seam);
}

/// An indestructible wall: flat top with a bright top edge and a darker front
/// face for 2.5D height, plus a subtle inset panel.
fn draw_wall(px: f32, py: f32, ts: f32, lip: f32) {
    draw_rectangle(px, py + ts - lip, ts, lip, WALL_SIDE);
    draw_rectangle(px, py, ts, ts - lip, WALL_TOP);
    draw_rectangle(px, py, ts, ts * 0.10, WALL_HI);
    draw_rectangle_lines(
        px + ts * 0.14,
        py + ts * 0.14,
        ts * 0.72,
        (ts - lip) - ts * 0.20,
        2.0,
        mix(WALL_TOP, BLACK, 0.18),
    );
}

/// A destructible crate: top + front face, banded edges, and an X of planks.
fn draw_crate(px: f32, py: f32, ts: f32, lip: f32) {
    draw_rectangle(px, py + ts - lip, ts, lip, CRATE_SIDE);
    draw_rectangle(px, py, ts, ts - lip, CRATE_TOP);
    draw_rectangle(px, py, ts, ts * 0.09, CRATE_HI);
    let inset = ts * 0.13;
    let (tw, th) = (ts - inset * 2.0, (ts - lip) - inset * 1.5);
    draw_rectangle_lines(px + inset, py + inset, tw, th, 2.0, CRATE_LINE);
    draw_line(px + inset, py + inset, px + inset + tw, py + inset + th, 2.0, CRATE_LINE);
    draw_line(px + inset + tw, py + inset, px + inset, py + inset + th, 2.0, CRATE_LINE);
}

/// A bomb: shadow, black body with a top highlight, and a lit fuse whose spark
/// flickers faster and redder as `fuse` approaches zero.
fn draw_bomb(cx: f32, cy: f32, ts: f32, fuse: f32) {
    let r = ts * 0.32;
    draw_ellipse(cx, cy + ts * 0.26, r * 1.05, r * 0.5, 0.0, Color::new(0.0, 0.0, 0.0, 0.28));
    draw_circle(cx, cy, r, Color::new(0.11, 0.11, 0.14, 1.0));
    draw_circle_lines(cx, cy, r, 2.0, Color::new(0.0, 0.0, 0.0, 0.45));
    draw_circle(cx - r * 0.32, cy - r * 0.34, r * 0.22, Color::new(0.85, 0.88, 0.95, 0.35));

    // Fuse nub on top, then a flickering spark.
    let urgency = (1.0 - (fuse / BOMB_FUSE)).clamp(0.0, 1.0);
    draw_rectangle(cx - r * 0.10, cy - r * 1.25, r * 0.20, r * 0.4, Color::new(0.25, 0.20, 0.16, 1.0));
    let blink = 0.5 + 0.5 * (get_time() as f32 * (10.0 + urgency * 32.0)).sin();
    let spark = vec2(cx + r * 0.05, cy - r * 1.35);
    let scol = mix(Color::new(1.0, 0.9, 0.4, 1.0), Color::new(1.0, 0.3, 0.15, 1.0), urgency);
    draw_circle(spark.x, spark.y, r * (0.18 + 0.10 * blink), Color::new(scol.r, scol.g, scol.b, 0.85));
    draw_circle(spark.x, spark.y, r * 0.08, Color::new(1.0, 1.0, 0.9, 0.9));
}

/// One explosion cell: overlapping flickering discs (outer ember → white core)
/// that bleed into neighbors for a continuous blast. `x,y` seed the flicker.
fn draw_flame(cx: f32, cy: f32, ts: f32, a: f32, x: i32, y: i32) {
    let flick = 0.85 + 0.15 * (get_time() as f32 * 18.0 + (x * 7 + y * 13) as f32).sin();
    let r = ts * 0.62 * flick;
    draw_circle(cx, cy, r, Color::new(1.0, 0.45, 0.12, 0.55 * a));
    draw_circle(cx, cy, r * 0.72, Color::new(1.0, 0.7, 0.2, 0.75 * a));
    draw_circle(cx, cy, r * 0.42, Color::new(1.0, 0.95, 0.7, 0.9 * a));
}

/// Draw an animated character: shadow, bobbing body with a lighter crown, eyes
/// that look toward `face`, shuffling feet while `moving`, and the shield ring /
/// own-player marker. `walk` is the walk-cycle phase.
#[allow(clippy::too_many_arguments)]
fn draw_player(
    cx: f32,
    cy: f32,
    ts: f32,
    color: Color,
    face: Vec2,
    walk: f32,
    moving: bool,
    shield: bool,
    is_me: bool,
) {
    let rb = ts * 0.30;
    let bob = if moving {
        -walk.sin().abs() * ts * 0.06
    } else {
        -((get_time() as f32 * 2.0).sin() * 0.5 + 0.5) * ts * 0.012
    };
    let by = cy + bob;

    // Shadow stays on the ground (doesn't bob).
    draw_ellipse(cx, cy + ts * 0.24, rb * 1.0, rb * 0.42, 0.0, Color::new(0.0, 0.0, 0.0, 0.28));

    // Shuffling feet.
    if moving {
        let lift = ts * 0.05;
        let l = walk.sin().max(0.0) * lift;
        let r = (-walk.sin()).max(0.0) * lift;
        let foot = mix(color, BLACK, 0.45);
        draw_ellipse(cx - rb * 0.45, cy + ts * 0.2 - l, rb * 0.28, rb * 0.18, 0.0, foot);
        draw_ellipse(cx + rb * 0.45, cy + ts * 0.2 - r, rb * 0.28, rb * 0.18, 0.0, foot);
    }

    // Body + lighter crown + outline.
    draw_circle(cx, by, rb, color);
    draw_circle(cx, by - rb * 0.35, rb * 0.7, mix(color, WHITE, 0.22));
    draw_circle_lines(cx, by, rb, 2.0, Color::new(0.0, 0.0, 0.0, 0.45));

    // Eyes look toward the facing direction.
    let look = face.normalize_or_zero();
    let eye_c = vec2(cx, by - rb * 0.10) + look * rb * 0.28;
    let perp = vec2(-look.y, look.x) * rb * 0.34;
    for s in [-1.0_f32, 1.0] {
        let e = eye_c + perp * s;
        draw_circle(e.x, e.y, rb * 0.20, WHITE);
        let pupil = e + look * rb * 0.08;
        draw_circle(pupil.x, pupil.y, rb * 0.10, Color::new(0.05, 0.05, 0.08, 1.0));
    }

    // Shield: a pulsing cyan ring around the body.
    if shield {
        let p = 0.5 + 0.5 * (get_time() as f32 * 4.0).sin();
        draw_circle_lines(cx, by, rb * 1.35, 2.5, Color::new(0.5, 0.9, 1.0, 0.5 + 0.4 * p));
    }

    // Bobbing marker above your own character.
    if is_me {
        let m = by - rb - ts * 0.18 + (get_time() as f32 * 3.0).sin() * ts * 0.03;
        draw_triangle(
            vec2(cx, m + ts * 0.14),
            vec2(cx - ts * 0.11, m),
            vec2(cx + ts * 0.11, m),
            WHITE,
        );
    }
}

fn center_text(text: &str, size: f32, color: Color) {
    center_text_at(text, screen_height() / 2.0, size, color);
}

/// Horizontally centered text with a caller-chosen baseline `y`.
fn center_text_at(text: &str, y: f32, size: f32, color: Color) {
    let d = measure_text(text, None, size as u16, 1.0);
    draw_text(text, (screen_width() - d.width) / 2.0, y, size, color);
}

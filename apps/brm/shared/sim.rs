//! The authoritative simulation step and its helpers.

use std::collections::HashMap;

use crate::{
    rng_f32, Bomb, Explosion, GameState, Phase, PlayerId, PlayerInput, PowerKind, PowerUp, Tile,
    BOMB_FUSE, EXPLOSION_TTL, KICK_SPEED, PLAYER_R, POWERUP_CHANCE, ROUNDOVER_SECS,
};

/// Advance the authoritative simulation by `dt` seconds, applying each player's
/// latest [`PlayerInput`]. Drives the whole match flow:
/// `Lobby -> Countdown -> Playing -> RoundOver -> Lobby`.
pub fn step(state: &mut GameState, inputs: &HashMap<PlayerId, PlayerInput>, dt: f32) {
    state.tick += 1;

    match state.phase {
        Phase::Lobby => {
            apply_ready(state, inputs);
            if all_ready(state) {
                state.begin_round();
            }
        }
        Phase::Countdown => {
            apply_ready(state, inputs);
            // An un-ready cancels the countdown (a spectator joining does not).
            if !all_ready(state) {
                state.return_to_lobby();
            } else {
                state.phase_timer -= dt;
                if state.phase_timer <= 0.0 {
                    state.phase = Phase::Playing;
                }
            }
        }
        Phase::Playing => {
            let ids: Vec<PlayerId> = state.players.iter().map(|p| p.id).collect();
            for id in ids {
                let input = inputs.get(&id).copied().unwrap_or_default();
                move_player(state, id, input, dt);
                try_kick(state, id, input);
                if input.place_bomb {
                    try_place_bomb(state, id);
                }
            }
            slide_bombs(state, dt);
            pickup_powerups(state);
            explode_bombs(state, dt);
            tick_explosions(state, dt);
            check_win(state);
        }
        Phase::RoundOver => {
            // Let pending blasts finish and fade, then return to the lobby.
            explode_bombs(state, dt);
            tick_explosions(state, dt);
            state.phase_timer -= dt;
            if state.phase_timer <= 0.0 {
                state.return_to_lobby();
            }
        }
    }
}

/// In the lobby/countdown, a participant's bomb-key press toggles their ready
/// state. Spectators can't ready up.
fn apply_ready(state: &mut GameState, inputs: &HashMap<PlayerId, PlayerInput>) {
    for p in &mut state.players {
        if p.spectating {
            continue;
        }
        if inputs.get(&p.id).map(|i| i.place_bomb).unwrap_or(false) {
            p.ready = !p.ready;
        }
    }
}

/// True when there's at least one participant (non-spectator) and all of them
/// are ready.
fn all_ready(state: &GameState) -> bool {
    let mut any = false;
    for p in state.players.iter().filter(|p| !p.spectating) {
        any = true;
        if !p.ready {
            return false;
        }
    }
    any
}

fn cell_solid(state: &GameState, x: i32, y: i32, passable: &[(i32, i32)]) -> bool {
    match state.map.get(x, y) {
        Tile::Wall | Tile::Block => return true,
        Tile::Empty => {}
    }
    state
        .bombs
        .iter()
        .any(|b| b.x == x && b.y == y && !passable.contains(&(x, y)))
}

fn aabb_overlaps_tile(px: f32, py: f32, r: f32, tx: i32, ty: i32) -> bool {
    px + r > tx as f32
        && px - r < (tx + 1) as f32
        && py + r > ty as f32
        && py - r < (ty + 1) as f32
}

fn move_player(state: &mut GameState, id: PlayerId, input: PlayerInput, dt: f32) {
    let (mut x, mut y, r, speed, alive) = match state.players.iter().find(|p| p.id == id) {
        Some(p) => (p.x, p.y, PLAYER_R, p.speed, p.alive),
        None => return,
    };
    if !alive {
        return;
    }

    // Normalize diagonal input so diagonal movement isn't faster.
    let (mut dx, mut dy) = (input.dx, input.dy);
    let mag = (dx * dx + dy * dy).sqrt();
    if mag > 1.0 {
        dx /= mag;
        dy /= mag;
    }

    // A bomb the player currently overlaps is passable until they step off it.
    let passable: Vec<(i32, i32)> = state
        .bombs
        .iter()
        .filter(|b| aabb_overlaps_tile(x, y, r, b.x, b.y))
        .map(|b| (b.x, b.y))
        .collect();

    x = sweep_axis(state, &passable, x, y, r, dx * speed * dt, true);
    y = sweep_axis(state, &passable, x, y, r, dy * speed * dt, false);

    if let Some(p) = state.player_mut(id) {
        p.x = x;
        p.y = y;
    }
}

/// Move one axis by `delta` and clamp against the first solid tile the leading
/// edge of the AABB reaches. Assumes `|delta| < 1` (true for one tick).
fn sweep_axis(
    state: &GameState,
    passable: &[(i32, i32)],
    x: f32,
    y: f32,
    r: f32,
    delta: f32,
    is_x: bool,
) -> f32 {
    let pos = if is_x { x } else { y };
    let mut np = pos + delta;
    if delta == 0.0 {
        return np;
    }

    // Cells spanned on the perpendicular axis.
    let (perp, px, py) = if is_x { (y, np, y) } else { (x, x, np) };
    let p0 = (perp - r + 1e-4).floor() as i32;
    let p1 = (perp + r - 1e-4).floor() as i32;

    if delta > 0.0 {
        let lead = (if is_x { px } else { py }) + r;
        let line = lead.floor() as i32;
        for p in p0..=p1 {
            let (cx, cy) = if is_x { (line, p) } else { (p, line) };
            if cell_solid(state, cx, cy, passable) {
                np = line as f32 - r;
                break;
            }
        }
    } else {
        let lead = (if is_x { px } else { py }) - r;
        let line = lead.floor() as i32;
        for p in p0..=p1 {
            let (cx, cy) = if is_x { (line, p) } else { (p, line) };
            if cell_solid(state, cx, cy, passable) {
                np = (line + 1) as f32 + r;
                break;
            }
        }
    }
    np
}

fn try_place_bomb(state: &mut GameState, id: PlayerId) {
    let (tx, ty, range, pierce, max) = match state.players.iter().find(|p| p.id == id) {
        Some(p) if p.alive => (
            p.x.floor() as i32,
            p.y.floor() as i32,
            p.range,
            p.pierce,
            p.bombs_max,
        ),
        _ => return,
    };
    let live = state.bombs.iter().filter(|b| b.owner == id).count() as u32;
    let occupied = state.bombs.iter().any(|b| b.x == tx && b.y == ty);
    if live < max && !occupied {
        state.bombs.push(Bomb::new(id, tx, ty, BOMB_FUSE, range, pierce));
    }
}

/// If the player has Kick and is pressed against a resting bomb in their
/// movement direction, start that bomb sliding.
fn try_kick(state: &mut GameState, id: PlayerId, input: PlayerInput) {
    let (px, py) = match state.players.iter().find(|p| p.id == id) {
        Some(p) if p.alive && p.can_kick => (p.x, p.y),
        _ => return,
    };
    // Cardinal push direction (dominant input axis).
    let (dx, dy) = if input.dx.abs() > input.dy.abs() {
        (input.dx.signum() as i32, 0)
    } else if input.dy.abs() > 0.0 {
        (0, input.dy.signum() as i32)
    } else {
        return;
    };

    let (bx, by) = (px.floor() as i32 + dx, py.floor() as i32 + dy);
    // Only kick when actually pressed up against that tile's near boundary.
    let pressed = match (dx, dy) {
        (1, 0) => px + PLAYER_R >= bx as f32 - 1e-3,
        (-1, 0) => px - PLAYER_R <= (bx + 1) as f32 + 1e-3,
        (0, 1) => py + PLAYER_R >= by as f32 - 1e-3,
        (0, -1) => py - PLAYER_R <= (by + 1) as f32 + 1e-3,
        _ => return,
    };
    if !pressed {
        return;
    }
    if let Some(b) = state
        .bombs
        .iter_mut()
        .find(|b| b.x == bx && b.y == by && b.slide_dir == (0, 0))
    {
        b.slide_dir = (dx, dy);
        b.slide_t = 0.0;
    }
}

/// Advance kicked bombs across the floor, snapping to the integer grid (the
/// position the blast uses) and stopping at walls, blocks, players, or bombs.
fn slide_bombs(state: &mut GameState, dt: f32) {
    let step = KICK_SPEED * dt;
    let player_tiles: Vec<(i32, i32)> = state
        .players
        .iter()
        .filter(|p| p.alive)
        .map(|p| (p.x.floor() as i32, p.y.floor() as i32))
        .collect();

    for i in 0..state.bombs.len() {
        let dir = state.bombs[i].slide_dir;
        if dir == (0, 0) {
            continue;
        }
        let mut t = state.bombs[i].slide_t + step;
        let (mut bx, mut by) = (state.bombs[i].x, state.bombs[i].y);
        while t >= 1.0 {
            let (nx, ny) = (bx + dir.0, by + dir.1);
            let blocked = state.map.get(nx, ny) != Tile::Empty
                || player_tiles.contains(&(nx, ny))
                || state
                    .bombs
                    .iter()
                    .enumerate()
                    .any(|(j, b)| j != i && b.x == nx && b.y == ny);
            if blocked {
                t = 0.0;
                state.bombs[i].slide_dir = (0, 0);
                break;
            }
            bx = nx;
            by = ny;
            t -= 1.0;
        }
        state.bombs[i].x = bx;
        state.bombs[i].y = by;
        state.bombs[i].slide_t = if state.bombs[i].slide_dir == (0, 0) {
            0.0
        } else {
            t
        };
    }
}

fn explode_bombs(state: &mut GameState, dt: f32) {
    for b in &mut state.bombs {
        b.fuse -= dt;
    }
    if !state.bombs.iter().any(|b| b.fuse <= 0.0) {
        return;
    }

    let mut done = vec![false; state.bombs.len()];
    let mut stack: Vec<usize> = state
        .bombs
        .iter()
        .enumerate()
        .filter(|(_, b)| b.fuse <= 0.0)
        .map(|(i, _)| i)
        .collect();

    let mut cells: Vec<(i32, i32)> = Vec::new();
    let mut destroyed: Vec<(i32, i32)> = Vec::new();

    while let Some(bi) = stack.pop() {
        if done[bi] {
            continue;
        }
        done[bi] = true;
        let (bx, by, range, pierce) = (
            state.bombs[bi].x,
            state.bombs[bi].y,
            state.bombs[bi].range,
            state.bombs[bi].pierce,
        );
        cells.push((bx, by));

        for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)] {
            for s in 1..=range {
                let (cx, cy) = (bx + dx * s, by + dy * s);
                match state.map.get(cx, cy) {
                    Tile::Wall => break,
                    Tile::Block => {
                        destroyed.push((cx, cy));
                        cells.push((cx, cy));
                        // A pierce blast keeps going through blocks.
                        if !pierce {
                            break;
                        }
                    }
                    Tile::Empty => {
                        cells.push((cx, cy));
                        // Chain-detonate any bomb caught in the blast. Placement
                        // guarantees at most one bomb per tile.
                        if let Some(other) = state.bombs.iter().position(|b| b.x == cx && b.y == cy)
                        {
                            if !done[other] {
                                stack.push(other);
                            }
                        }
                    }
                }
            }
        }
    }

    // Pre-existing power-ups caught in this blast are destroyed.
    state.powerups.retain(|p| !cells.contains(&(p.x, p.y)));

    // Destroy blocks and maybe reveal a fresh power-up where each stood. This
    // runs AFTER the retain above: a revealed power-up sits on a blasted cell,
    // so doing it earlier would immediately delete it.
    for (cx, cy) in &destroyed {
        state.map.set(*cx, *cy, Tile::Empty);
        if rng_f32(&mut state.rng) < POWERUP_CHANCE {
            let kind = PowerKind::ALL[(state.rng >> 8) as usize % PowerKind::ALL.len()];
            state.powerups.push(PowerUp {
                x: *cx,
                y: *cy,
                kind,
            });
        }
    }

    // Kill players standing in the blast — unless a shield absorbs it.
    for p in &mut state.players {
        if p.alive && cells.contains(&(p.x.floor() as i32, p.y.floor() as i32)) {
            if p.shield {
                p.shield = false;
            } else {
                p.alive = false;
            }
        }
    }

    // Retain only bombs that didn't go off this tick.
    let mut i = 0;
    state.bombs.retain(|_| {
        let keep = !done[i];
        i += 1;
        keep
    });

    cells.sort_unstable();
    cells.dedup();
    state.explosions.push(Explosion {
        cells,
        ttl: EXPLOSION_TTL,
    });
}

fn tick_explosions(state: &mut GameState, dt: f32) {
    for e in &mut state.explosions {
        e.ttl -= dt;
    }
    state.explosions.retain(|e| e.ttl > 0.0);
}

fn pickup_powerups(state: &mut GameState) {
    let mut taken = Vec::new();
    for p in &mut state.players {
        if !p.alive {
            continue;
        }
        let (tx, ty) = (p.x.floor() as i32, p.y.floor() as i32);
        if let Some(pos) = state.powerups.iter().position(|u| u.x == tx && u.y == ty) {
            match state.powerups[pos].kind {
                PowerKind::ExtraBomb => p.bombs_max += 1,
                PowerKind::Range => p.range += 1,
                PowerKind::Speed => {
                    p.speed += 0.75;
                    p.speed_ups = p.speed_ups.saturating_add(1);
                }
                PowerKind::Kick => p.can_kick = true,
                PowerKind::Pierce => p.pierce = true,
                PowerKind::Shield => p.shield = true,
            }
            taken.push(pos);
        }
    }
    // Remove from the back so indices stay valid.
    taken.sort_unstable_by(|a, b| b.cmp(a));
    for pos in taken {
        state.powerups.remove(pos);
    }
}

fn check_win(state: &mut GameState) {
    // Only round participants (not spectators) count.
    let total = state.players.iter().filter(|p| !p.spectating).count();
    let alive: Vec<PlayerId> = state
        .players
        .iter()
        .filter(|p| !p.spectating && p.alive)
        .map(|p| p.id)
        .collect();

    // A 2+ player round ends when one is left; a solo round ends when the lone
    // player dies (so it returns to the lobby rather than running forever).
    if total >= 1 && alive.len() <= 1 && (total >= 2 || alive.is_empty()) {
        state.phase = Phase::RoundOver;
        state.phase_timer = ROUNDOVER_SECS;
        state.winner = alive.first().copied();
    }
}

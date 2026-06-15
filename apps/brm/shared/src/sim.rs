//! The authoritative simulation step and its helpers.

use std::collections::HashMap;

use crate::{
    rng_f32, Bomb, Explosion, GameState, Phase, PlayerId, PlayerInput, PowerKind, PowerUp, Tile,
    BOMB_FUSE, EXPLOSION_TTL, PLAYER_R, POWERUP_CHANCE,
};

/// Advance the authoritative simulation by `dt` seconds, applying each player's
/// latest [`PlayerInput`]. Missing inputs are treated as idle.
pub fn step(state: &mut GameState, inputs: &HashMap<PlayerId, PlayerInput>, dt: f32) {
    state.tick += 1;

    if state.phase == Phase::Playing {
        let ids: Vec<PlayerId> = state.players.iter().map(|p| p.id).collect();
        for id in ids {
            let input = inputs.get(&id).copied().unwrap_or_default();
            move_player(state, id, input, dt);
            if input.place_bomb {
                try_place_bomb(state, id);
            }
        }
        pickup_powerups(state);
    }

    explode_bombs(state, dt);
    tick_explosions(state, dt);

    if state.phase == Phase::Playing {
        check_win(state);
    }
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
    let (tx, ty, range) = match state.players.iter().find(|p| p.id == id) {
        Some(p) if p.alive => (p.x.floor() as i32, p.y.floor() as i32, p.range),
        _ => return,
    };
    let live = state.bombs.iter().filter(|b| b.owner == id).count() as u32;
    let max = state
        .players
        .iter()
        .find(|p| p.id == id)
        .map(|p| p.bombs_max)
        .unwrap_or(0);
    let occupied = state.bombs.iter().any(|b| b.x == tx && b.y == ty);
    if live < max && !occupied {
        state.bombs.push(Bomb {
            owner: id,
            x: tx,
            y: ty,
            fuse: BOMB_FUSE,
            range,
        });
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
        let (bx, by, range) = (state.bombs[bi].x, state.bombs[bi].y, state.bombs[bi].range);
        cells.push((bx, by));

        for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)] {
            for s in 1..=range {
                let (cx, cy) = (bx + dx * s, by + dy * s);
                match state.map.get(cx, cy) {
                    Tile::Wall => break,
                    Tile::Block => {
                        destroyed.push((cx, cy));
                        cells.push((cx, cy));
                        break;
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

    // Destroy blocks and maybe reveal power-ups.
    for (cx, cy) in &destroyed {
        state.map.set(*cx, *cy, Tile::Empty);
        if rng_f32(&mut state.rng) < POWERUP_CHANCE {
            let kind = match (state.rng >> 8) % 3 {
                0 => PowerKind::ExtraBomb,
                1 => PowerKind::Range,
                _ => PowerKind::Speed,
            };
            state.powerups.push(PowerUp {
                x: *cx,
                y: *cy,
                kind,
            });
        }
    }

    // A power-up sitting in the blast is destroyed.
    state.powerups.retain(|p| !cells.contains(&(p.x, p.y)));

    // Kill players standing in the blast.
    for p in &mut state.players {
        if p.alive && cells.contains(&(p.x.floor() as i32, p.y.floor() as i32)) {
            p.alive = false;
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
                PowerKind::Speed => p.speed += 0.75,
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
    let alive: Vec<PlayerId> = state
        .players
        .iter()
        .filter(|p| p.alive)
        .map(|p| p.id)
        .collect();
    // Only end a round that actually started with 2+ players.
    if state.players.len() >= 2 && alive.len() <= 1 {
        state.phase = Phase::RoundOver;
        state.winner = alive.first().copied();
    }
}

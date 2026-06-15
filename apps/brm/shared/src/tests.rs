//! Deterministic simulation tests. These build precise scenarios on an open
//! arena and assert the outcome of a single detonation or a run of ticks.

use std::collections::HashMap;

use crate::*;

/// An open arena with a solid border and no interior blocks/pillars, so tests
/// can place exactly the obstacles they care about.
fn open_map(w: i32, h: i32) -> GameState {
    let mut tiles = vec![Tile::Empty; (w * h) as usize];
    for y in 0..h {
        for x in 0..w {
            if x == 0 || y == 0 || x == w - 1 || y == h - 1 {
                tiles[(y * w + x) as usize] = Tile::Wall;
            }
        }
    }
    GameState::with_map(Map { w, h, tiles })
}

fn detonate_now(gs: &mut GameState) {
    for b in &mut gs.bombs {
        b.fuse = 0.001;
    }
    step(gs, &HashMap::new(), 0.01);
}

#[test]
fn explosion_is_blocked_by_walls() {
    let mut gs = open_map(7, 7);
    gs.map.set(5, 3, Tile::Wall); // wall two tiles right of the bomb
    gs.bombs.push(Bomb {
        owner: 1,
        x: 3,
        y: 3,
        fuse: 0.0,
        range: 3,
    });
    detonate_now(&mut gs);
    let cells = &gs.explosions[0].cells;
    assert!(cells.contains(&(4, 3)), "flame reaches the open tile");
    assert!(!cells.contains(&(5, 3)), "flame stops at the wall");
    assert!(!cells.contains(&(6, 3)), "flame never passes the wall");
}

#[test]
fn explosion_destroys_one_block_then_stops() {
    let mut gs = open_map(8, 5);
    gs.map.set(4, 2, Tile::Block);
    gs.map.set(5, 2, Tile::Block);
    gs.bombs.push(Bomb {
        owner: 1,
        x: 2,
        y: 2,
        fuse: 0.0,
        range: 5,
    });
    detonate_now(&mut gs);
    assert_eq!(gs.map.get(4, 2), Tile::Empty, "first block destroyed");
    assert_eq!(gs.map.get(5, 2), Tile::Block, "second block shielded");
    let cells = &gs.explosions[0].cells;
    assert!(cells.contains(&(4, 2)));
    assert!(!cells.contains(&(5, 2)));
}

#[test]
fn bombs_chain_detonate() {
    let mut gs = open_map(9, 5);
    // Bomb A at (2,2) range 2 reaches (4,2) where bomb B sits with a long fuse.
    gs.bombs.push(Bomb { owner: 1, x: 2, y: 2, fuse: 0.0, range: 2 });
    gs.bombs.push(Bomb { owner: 2, x: 4, y: 2, fuse: 99.0, range: 2 });
    detonate_now(&mut gs);
    assert!(gs.bombs.is_empty(), "both bombs detonated via chain");
    let cells = &gs.explosions[0].cells;
    assert!(cells.contains(&(6, 2)), "chained bomb's own blast is present");
}

#[test]
fn explosion_kills_players_in_blast() {
    let mut gs = open_map(7, 7);
    gs.add_player(); // id 1 at (1,1)
    gs.players[0].x = 3.5;
    gs.players[0].y = 3.5;
    gs.bombs.push(Bomb { owner: 1, x: 3, y: 3, fuse: 0.0, range: 1 });
    detonate_now(&mut gs);
    assert!(!gs.players[0].alive, "player on the bomb tile dies");
}

#[test]
fn last_player_standing_wins() {
    let mut gs = open_map(7, 7);
    let a = gs.add_player();
    let _b = gs.add_player();
    gs.players[1].x = 3.5;
    gs.players[1].y = 3.5;
    gs.bombs.push(Bomb { owner: a, x: 3, y: 3, fuse: 0.0, range: 1 });
    detonate_now(&mut gs);
    assert_eq!(gs.phase, Phase::RoundOver);
    assert_eq!(gs.winner, Some(a));
}

#[test]
fn walls_block_movement() {
    let mut gs = open_map(7, 7);
    let id = gs.add_player();
    gs.players[0].x = 1.5;
    gs.players[0].y = 1.5;
    // Push hard left into the border wall for many ticks.
    let mut inputs = HashMap::new();
    inputs.insert(id, PlayerInput { dx: -1.0, dy: 0.0, place_bomb: false });
    for _ in 0..60 {
        step(&mut gs, &inputs, 1.0 / 30.0);
    }
    assert!(gs.players[0].x >= 1.0 + PLAYER_R - 1e-3, "stopped at the wall");
}

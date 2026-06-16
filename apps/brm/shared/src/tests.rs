//! Deterministic simulation tests. These build precise scenarios on an open
//! arena and assert the outcome of a single detonation or a run of ticks.

use std::collections::HashMap;

use crate::*;

/// An open arena with a solid border and no interior blocks/pillars, so tests
/// can place exactly the obstacles they care about. The state is mid-round
/// (`Playing`).
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

/// Add a player as an active round participant. The `open_map` tests construct a
/// `Playing` scenario directly, where `add_player` would otherwise spectate.
fn add_active(gs: &mut GameState) -> PlayerId {
    let id = gs.add_player();
    let p = gs.players.last_mut().unwrap();
    p.alive = true;
    p.spectating = false;
    id
}

fn detonate_now(gs: &mut GameState) {
    for b in &mut gs.bombs {
        b.fuse = 0.001;
    }
    step(gs, &HashMap::new(), 0.01);
}

/// Inputs that press the bomb/action key for the given players (toggles ready in
/// the lobby).
fn ready_inputs(ids: &[PlayerId]) -> HashMap<PlayerId, PlayerInput> {
    ids.iter()
        .map(|&id| (id, PlayerInput { dx: 0.0, dy: 0.0, place_bomb: true }))
        .collect()
}

/// Advance `secs` worth of idle ticks at 30 Hz.
fn idle_for(gs: &mut GameState, secs: f32) {
    let idle = HashMap::new();
    for _ in 0..((secs * 30.0) as usize) {
        step(gs, &idle, 1.0 / 30.0);
    }
}

#[test]
fn explosion_is_blocked_by_walls() {
    let mut gs = open_map(7, 7);
    gs.map.set(5, 3, Tile::Wall); // wall two tiles right of the bomb
    gs.bombs.push(Bomb::new(1, 3, 3, 0.0, 3, false));
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
    gs.bombs.push(Bomb::new(1, 2, 2, 0.0, 5, false));
    detonate_now(&mut gs);
    assert_eq!(gs.map.get(4, 2), Tile::Empty, "first block destroyed");
    assert_eq!(gs.map.get(5, 2), Tile::Block, "second block shielded");
    let cells = &gs.explosions[0].cells;
    assert!(cells.contains(&(4, 2)));
    assert!(!cells.contains(&(5, 2)));
}

#[test]
fn pierce_blast_punches_through_blocks() {
    let mut gs = open_map(9, 5);
    gs.map.set(3, 2, Tile::Block);
    gs.map.set(4, 2, Tile::Block);
    gs.bombs.push(Bomb::new(1, 2, 2, 0.0, 4, true)); // pierce, range 4
    detonate_now(&mut gs);
    assert_eq!(gs.map.get(3, 2), Tile::Empty, "first block destroyed");
    assert_eq!(gs.map.get(4, 2), Tile::Empty, "pierce continues to the second");
    assert!(
        gs.explosions[0].cells.contains(&(5, 2)),
        "flame reaches past the blocks"
    );
}

#[test]
fn destroyed_blocks_can_reveal_surviving_power_ups() {
    // A long pierce blast through a row of blocks. The bug this guards against:
    // a power-up revealed on a destroyed block was instantly deleted by that
    // same blast, so none ever appeared.
    let mut gs = open_map(16, 5);
    for x in 3..13 {
        gs.map.set(x, 2, Tile::Block);
    }
    gs.bombs.push(Bomb::new(1, 2, 2, 0.0, 12, true)); // pierce, long range
    detonate_now(&mut gs);
    assert!(
        !gs.powerups.is_empty(),
        "destroying a row of blocks revealed at least one power-up"
    );
    for p in &gs.powerups {
        assert_eq!(gs.map.get(p.x, p.y), Tile::Empty, "power-up sits on floor");
    }
}

#[test]
fn bombs_chain_detonate() {
    let mut gs = open_map(9, 5);
    // Bomb A at (2,2) range 2 reaches (4,2) where bomb B sits with a long fuse.
    gs.bombs.push(Bomb::new(1, 2, 2, 0.0, 2, false));
    gs.bombs.push(Bomb::new(2, 4, 2, 99.0, 2, false));
    detonate_now(&mut gs);
    assert!(gs.bombs.is_empty(), "both bombs detonated via chain");
    let cells = &gs.explosions[0].cells;
    assert!(cells.contains(&(6, 2)), "chained bomb's own blast is present");
}

#[test]
fn explosion_kills_players_in_blast() {
    let mut gs = open_map(7, 7);
    add_active(&mut gs); // id 1 at (1,1)
    gs.players[0].x = 3.5;
    gs.players[0].y = 3.5;
    gs.bombs.push(Bomb::new(1, 3, 3, 0.0, 1, false));
    detonate_now(&mut gs);
    assert!(!gs.players[0].alive, "player on the bomb tile dies");
}

#[test]
fn shield_absorbs_one_blast() {
    let mut gs = open_map(7, 7);
    add_active(&mut gs);
    gs.players[0].x = 3.5;
    gs.players[0].y = 3.5;
    gs.players[0].shield = true;
    gs.bombs.push(Bomb::new(1, 3, 3, 0.0, 1, false));
    detonate_now(&mut gs);
    assert!(gs.players[0].alive, "shield absorbs the blast");
    assert!(!gs.players[0].shield, "shield is consumed");
}

#[test]
fn kick_slides_a_bomb() {
    let mut gs = open_map(9, 5);
    let id = add_active(&mut gs);
    gs.players[0].can_kick = true;
    // Center pressed against the bomb in tile (3,2), pushing right.
    gs.players[0].x = 3.0 - PLAYER_R;
    gs.players[0].y = 2.5;
    gs.bombs.push(Bomb::new(2, 3, 2, 99.0, 1, false)); // long fuse: won't detonate
    let start_x = gs.bombs[0].x;

    let mut inputs = HashMap::new();
    inputs.insert(id, PlayerInput { dx: 1.0, dy: 0.0, place_bomb: false });
    for _ in 0..30 {
        step(&mut gs, &inputs, 1.0 / 30.0);
    }
    assert!(gs.bombs[0].x > start_x, "kicked bomb slid away");
}

#[test]
fn speed_pickup_is_counted_for_stats() {
    let mut gs = open_map(7, 7);
    add_active(&mut gs);
    gs.players[0].x = 3.5;
    gs.players[0].y = 3.5;
    gs.powerups.push(PowerUp { x: 3, y: 3, kind: PowerKind::Speed });
    step(&mut gs, &HashMap::new(), 1.0 / 30.0);
    assert_eq!(gs.players[0].speed_ups, 1, "Speed pickup counted for stats");
    assert!(gs.powerups.is_empty());
}

#[test]
fn picking_up_kick_grants_the_ability() {
    let mut gs = open_map(7, 7);
    add_active(&mut gs);
    gs.players[0].x = 3.5;
    gs.players[0].y = 3.5;
    gs.powerups.push(PowerUp { x: 3, y: 3, kind: PowerKind::Kick });
    step(&mut gs, &HashMap::new(), 1.0 / 30.0);
    assert!(gs.players[0].can_kick, "Kick power-up grants kicking");
    assert!(gs.powerups.is_empty(), "power-up consumed on pickup");
}

#[test]
fn last_player_standing_wins() {
    let mut gs = open_map(7, 7);
    let a = add_active(&mut gs);
    let _b = add_active(&mut gs);
    gs.players[1].x = 3.5;
    gs.players[1].y = 3.5;
    gs.bombs.push(Bomb::new(a, 3, 3, 0.0, 1, false));
    detonate_now(&mut gs);
    assert_eq!(gs.phase, Phase::RoundOver);
    assert_eq!(gs.winner, Some(a));
}

#[test]
fn solo_player_death_ends_round() {
    let mut gs = open_map(7, 7);
    let a = add_active(&mut gs);
    gs.players[0].x = 3.5;
    gs.players[0].y = 3.5;
    gs.bombs.push(Bomb::new(a, 3, 3, 0.0, 1, false));
    detonate_now(&mut gs);
    assert_eq!(gs.phase, Phase::RoundOver, "a solo round ends on death");
    assert_eq!(gs.winner, None);
}

#[test]
fn lobby_starts_when_all_players_ready() {
    let mut gs = GameState::new(1);
    let a = gs.add_player();
    let b = gs.add_player();
    assert_eq!(gs.phase, Phase::Lobby);

    // Both press their action to ready -> countdown begins.
    step(&mut gs, &ready_inputs(&[a, b]), 1.0 / 30.0);
    assert_eq!(gs.phase, Phase::Countdown);
    assert!(gs.players.iter().all(|p| p.ready));

    // Countdown elapses -> the round is live with both players spawned.
    idle_for(&mut gs, COUNTDOWN_SECS + 0.1);
    assert_eq!(gs.phase, Phase::Playing);
    assert!(gs.players.iter().all(|p| p.alive));
}

#[test]
fn unreadying_during_countdown_returns_to_lobby() {
    let mut gs = GameState::new(1);
    let a = gs.add_player();
    let b = gs.add_player();
    step(&mut gs, &ready_inputs(&[a, b]), 1.0 / 30.0); // -> Countdown
    assert_eq!(gs.phase, Phase::Countdown);

    step(&mut gs, &ready_inputs(&[a]), 1.0 / 30.0); // A toggles back off
    assert_eq!(gs.phase, Phase::Lobby);
    assert!(!gs.players[0].ready);
}

#[test]
fn round_over_auto_returns_to_lobby() {
    let mut gs = GameState::new(1);
    let a = gs.add_player();
    let b = gs.add_player();
    step(&mut gs, &ready_inputs(&[a, b]), 1.0 / 30.0);
    idle_for(&mut gs, COUNTDOWN_SECS + 0.1);
    assert_eq!(gs.phase, Phase::Playing);

    // Stack both players and detonate to force the round to end.
    gs.players[1].x = gs.players[0].x;
    gs.players[1].y = gs.players[0].y;
    let (bx, by) = gs.players[0].tile();
    gs.bombs.push(Bomb::new(a, bx, by, 0.0, 1, false));
    detonate_now(&mut gs);
    assert_eq!(gs.phase, Phase::RoundOver);

    idle_for(&mut gs, ROUNDOVER_SECS + 0.1);
    assert_eq!(gs.phase, Phase::Lobby);
    assert!(gs.players.iter().all(|p| !p.ready), "lobby clears ready flags");
}

#[test]
fn mid_round_joiner_spectates_then_plays_next_round() {
    let mut gs = GameState::new(1);
    let a = gs.add_player();
    let b = gs.add_player();
    step(&mut gs, &ready_inputs(&[a, b]), 1.0 / 30.0);
    idle_for(&mut gs, COUNTDOWN_SECS + 0.1);
    assert_eq!(gs.phase, Phase::Playing);

    // A third player joins mid-round: they spectate and don't disturb the round.
    let c = gs.add_player();
    let cp = gs.players.iter().find(|p| p.id == c).unwrap();
    assert!(cp.spectating && !cp.alive, "mid-round joiner spectates");
    assert_eq!(gs.phase, Phase::Playing, "spectator doesn't end/alter the round");

    // After the round ends and returns to lobby, they're a full participant.
    gs.players.iter_mut().find(|p| p.id == b).unwrap().alive = false;
    idle_for(&mut gs, ROUNDOVER_SECS + 0.2);
    assert_eq!(gs.phase, Phase::Lobby);
    let cp = gs.players.iter().find(|p| p.id == c).unwrap();
    assert!(!cp.spectating, "spectator joins the next lobby");
}

#[test]
fn set_name_truncates_to_limit() {
    let mut gs = GameState::new(1);
    let a = gs.add_player();
    gs.set_name(a, "this_is_a_really_long_name");
    let name = &gs.players[0].name;
    assert!(name.chars().count() <= MAX_NAME_LEN);
    assert_eq!(name, "this_is_a_reall");
}

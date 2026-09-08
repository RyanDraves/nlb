//! Shared authoritative state and the fixed-timestep simulation loop.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use brm_shared::{step, GameState, PlayerId, PlayerInput, ServerMsg};
use tokio::sync::broadcast;

/// Simulation tick rate. The server is authoritative; clients only send input.
const TICK_HZ: f32 = 30.0;

pub struct App {
    pub game: Mutex<GameState>,
    /// Latest input per connected player, merged between ticks.
    pub inputs: Mutex<HashMap<PlayerId, PlayerInput>>,
    /// Fan-out of serialized `ServerMsg::Snapshot` frames to every connection.
    pub snapshots: broadcast::Sender<Arc<Vec<u8>>>,
}

impl App {
    pub fn new(seed: u64) -> Arc<Self> {
        let (snapshots, _) = broadcast::channel(64);
        Arc::new(App {
            game: Mutex::new(GameState::new(seed)),
            inputs: Mutex::new(HashMap::new()),
            snapshots,
        })
    }
}

/// Fixed-timestep authoritative loop: apply inputs, advance the sim, broadcast a
/// snapshot, then clear the one-shot `place_bomb` edges.
pub async fn run(app: Arc<App>) {
    let dt = 1.0 / TICK_HZ;
    let mut interval = tokio::time::interval(Duration::from_secs_f32(dt));
    loop {
        interval.tick().await;
        let bytes = {
            let mut game = app.game.lock().unwrap();
            let mut inputs = app.inputs.lock().unwrap();
            step(&mut game, &inputs, dt);
            for v in inputs.values_mut() {
                v.place_bomb = false;
            }
            bincode::serialize(&ServerMsg::Snapshot(game.clone())).unwrap()
        };
        // Ignore send errors (no receivers yet / all lagged); next tick retries.
        let _ = app.snapshots.send(Arc::new(bytes));
    }
}

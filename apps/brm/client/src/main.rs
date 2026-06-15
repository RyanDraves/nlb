//! Bomberman client: renders the authoritative game state and forwards local
//! input. The same binary builds natively (couch players, one WebSocket per
//! split-keyboard player) and to wasm (one browser/phone player), differing only
//! in how the server URL and player count are chosen.

mod input;
mod net;
mod render;

use brm_shared::{ClientMsg, GameState, PlayerId, ServerMsg};
use input::{read_input, Binds, BINDS};
use macroquad::prelude::*;
use net::WebSocket;

/// One local player: its own connection to the server plus key bindings.
struct Local {
    ws: WebSocket,
    /// Player id assigned by the server (via `ServerMsg::Welcome`).
    id: Option<PlayerId>,
    binds: Binds,
    name: String,
    /// Whether we've sent our `Join` yet. On wasm the socket connects
    /// asynchronously, so we must wait for `connected()` before sending
    /// anything — sending on a still-CONNECTING socket throws and traps wasm.
    joined: bool,
}

fn window_conf() -> Conf {
    Conf {
        window_title: "brm".to_owned(),
        window_width: 832,
        window_height: 704,
        ..Default::default()
    }
}

#[macroquad::main(window_conf)]
async fn main() {
    let url = server_url();
    let count = local_player_count();

    let mut locals: Vec<Local> = Vec::new();
    for i in 0..count {
        match WebSocket::connect(url.as_str()) {
            Ok(ws) => locals.push(Local {
                ws,
                id: None,
                binds: BINDS[i.min(BINDS.len() - 1)],
                name: format!("P{}", i + 1),
                joined: false,
            }),
            Err(e) => error!("failed to connect to {url}: {e:?}"),
        }
    }

    let mut latest: Option<GameState> = None;

    loop {
        for lp in &mut locals {
            while let Some(buf) = lp.ws.try_recv() {
                match bincode::deserialize::<ServerMsg>(&buf) {
                    Ok(ServerMsg::Welcome { id }) => lp.id = Some(id),
                    Ok(ServerMsg::Snapshot(gs)) => latest = Some(gs),
                    Err(_) => {}
                }
            }
            // Only transmit once the socket is open (see `joined`).
            if lp.ws.connected() {
                if !lp.joined {
                    if let Ok(b) = bincode::serialize(&ClientMsg::Join { name: lp.name.clone() }) {
                        lp.ws.send_bytes(&b);
                    }
                    lp.joined = true;
                }
                let input = read_input(&lp.binds);
                if let Ok(b) = bincode::serialize(&ClientMsg::Input(input)) {
                    lp.ws.send_bytes(&b);
                }
            }
        }

        let my_ids: Vec<PlayerId> = locals.iter().filter_map(|l| l.id).collect();
        render::frame(&latest, &my_ids);
        next_frame().await;
    }
}

#[cfg(not(target_arch = "wasm32"))]
fn server_url() -> String {
    std::env::args()
        .nth(1)
        .or_else(|| std::env::var("BRM_SERVER").ok())
        .unwrap_or_else(|| "ws://127.0.0.1:8080/ws".to_owned())
}

#[cfg(not(target_arch = "wasm32"))]
fn local_player_count() -> usize {
    std::env::var("BRM_PLAYERS")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(2)
}

// On the web a guest is always a single player. We hand the JS layer a relative
// path; brm_net.js turns it into an absolute ws:// URL against the page's own
// origin, so a phone/laptop that loaded the page over the LAN connects back to
// the hosting machine automatically.
#[cfg(target_arch = "wasm32")]
fn server_url() -> String {
    "/ws".to_owned()
}

#[cfg(target_arch = "wasm32")]
fn local_player_count() -> usize {
    1
}

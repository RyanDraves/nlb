//! Bomberman client: renders the authoritative game state and forwards local
//! input. The same binary builds natively (couch players, one WebSocket per
//! split-keyboard player) and to wasm (one browser/phone player), differing only
//! in how the server URL and player count are chosen.

mod input;
mod net;
mod render;

use brm_shared::{ClientMsg, GameState, Phase, PlayerId, ServerMsg};
use input::{read_input, Binds, BINDS};
use macroquad::prelude::*;
use net::WebSocket;

/// One local player: its own connection to the server plus key bindings.
struct Local {
    ws: WebSocket,
    /// Player id assigned by the server (via `ServerMsg::Welcome`).
    id: Option<PlayerId>,
    binds: Binds,
    /// Locally-typed name; empty means "use the server's default `Player N`".
    name: String,
    /// Last name sent, so we only resend `SetName` when it changes.
    name_sent: String,
    /// Whether this player is currently editing their name (entered with E).
    editing: bool,
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
    let assets = render::Assets::load();

    let mut locals: Vec<Local> = Vec::new();
    for i in 0..count {
        match WebSocket::connect(url.as_str()) {
            Ok(ws) => locals.push(Local {
                ws,
                id: None,
                binds: BINDS[i.min(BINDS.len() - 1)],
                name: String::new(),
                name_sent: String::new(),
                editing: false,
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
        }

        // Lobby name entry. Editing is explicit (press E to start) so stray
        // key-mashing — e.g. at the end of a round — never leaks into names.
        // Typed characters go to the focused local player (the first of yours
        // who hasn't readied up yet).
        let phase_lobby = matches!(&latest, Some(g) if g.phase == Phase::Lobby);
        let focus = if phase_lobby {
            focused_local(&locals, latest.as_ref())
        } else {
            None
        };
        if let Some(i) = focus {
            if locals[i].editing {
                input::edit_name(&mut locals[i].name);
                // The same action-key press both finishes editing and readies up.
                if is_key_pressed(locals[i].binds.bomb_key()) {
                    locals[i].editing = false;
                }
            } else if is_key_pressed(KeyCode::E) {
                locals[i].editing = true;
                // Seed the buffer with the name shown so far, so typing extends
                // it (rather than the first keystroke replacing the visible name).
                if locals[i].name.is_empty() {
                    if let Some(name) = locals[i]
                        .id
                        .and_then(|id| latest.as_ref().and_then(|g| g.players.iter().find(|p| p.id == id)))
                        .map(|p| p.name.clone())
                    {
                        locals[i].name = name;
                    }
                }
                while get_char_pressed().is_some() {} // drop the 'e' that opened the editor
            } else {
                while get_char_pressed().is_some() {} // discard stray typed chars
            }
        } else {
            while get_char_pressed().is_some() {}
            for lp in &mut locals {
                lp.editing = false;
            }
        }
        let editing_id = focus.and_then(|i| if locals[i].editing { locals[i].id } else { None });

        for lp in &mut locals {
            // Only transmit once the socket is open (see `joined`).
            if lp.ws.connected() {
                if !lp.joined {
                    send(&lp.ws, &ClientMsg::Join { name: lp.name.clone() });
                    lp.joined = true;
                    lp.name_sent = lp.name.clone();
                }
                if lp.name != lp.name_sent {
                    send(&lp.ws, &ClientMsg::SetName { name: lp.name.clone() });
                    lp.name_sent = lp.name.clone();
                }
                send(&lp.ws, &ClientMsg::Input(read_input(&lp.binds)));
            }
        }

        let my_ids: Vec<PlayerId> = locals.iter().filter_map(|l| l.id).collect();
        render::frame(&assets, &latest, &my_ids, editing_id);
        next_frame().await;
    }
}

fn send(ws: &WebSocket, msg: &ClientMsg) {
    if let Ok(bytes) = bincode::serialize(msg) {
        ws.send_bytes(&bytes);
    }
}

/// The local player currently accepting typed name input: the first one who
/// isn't ready yet (so couch players name themselves in turn, then ready up).
fn focused_local(locals: &[Local], latest: Option<&GameState>) -> Option<usize> {
    for (i, lp) in locals.iter().enumerate() {
        let ready = lp
            .id
            .and_then(|id| latest.and_then(|g| g.players.iter().find(|p| p.id == id)))
            .map(|p| p.ready)
            .unwrap_or(false);
        if !ready {
            return Some(i);
        }
    }
    None
}

#[cfg(not(target_arch = "wasm32"))]
fn arg_after(flag: &str) -> Option<String> {
    let args: Vec<String> = std::env::args().collect();
    args.iter()
        .position(|a| a == flag)
        .and_then(|i| args.get(i + 1))
        .cloned()
}

#[cfg(not(target_arch = "wasm32"))]
fn server_url() -> String {
    arg_after("--server")
        .or_else(|| std::env::var("BRM_SERVER").ok())
        .unwrap_or_else(|| "ws://127.0.0.1:8080/ws".to_owned())
}

/// Number of split-keyboard players: `--players 1|2` (or `BRM_PLAYERS`), 2 by
/// default.
#[cfg(not(target_arch = "wasm32"))]
fn local_player_count() -> usize {
    arg_after("--players")
        .or_else(|| std::env::var("BRM_PLAYERS").ok())
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(2)
        .clamp(1, 2)
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

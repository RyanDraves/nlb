//! Bomberman client: renders the authoritative game state and forwards local
//! input. The same binary builds natively (couch players, one WebSocket per
//! split-keyboard player) and to wasm (one browser/phone player), differing only
//! in how the server URL and player count are chosen.

mod audio;
#[cfg(not(target_arch = "wasm32"))]
mod gamepad;
mod input;
mod net;
mod render;
mod touch;
mod web;

use brm_shared::{ClientMsg, GameState, Phase, PlayerId, ServerMsg};
use input::{read_input, Binds, BINDS};
use macroquad::prelude::*;
use net::WebSocket;

/// Where a local player's input comes from. The wasm client always uses
/// `Keyboard` here and overrides it per-frame with touch/gamepad (a browser
/// guest is a single player), so the `Pad` variant is native-only.
enum Source {
    Keyboard(Binds),
    #[cfg(not(target_arch = "wasm32"))]
    Pad(gamepad::GamepadId),
}

impl Source {
    /// The keyboard bindings, if this is a keyboard player (used for the lobby
    /// name-editing flow, which only applies to keyboard players).
    fn keyboard_binds(&self) -> Option<Binds> {
        #[allow(irrefutable_let_patterns)]
        if let Source::Keyboard(b) = self {
            Some(*b)
        } else {
            None
        }
    }
}

/// One local player: its own connection to the server plus its input source.
struct Local {
    ws: WebSocket,
    /// Player id assigned by the server (via `ServerMsg::Welcome`).
    id: Option<PlayerId>,
    source: Source,
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
    let mut audio = audio::Audio::load().await;

    let mut locals: Vec<Local> = Vec::new();
    let connect = |source: Source| match WebSocket::connect(url.as_str()) {
        Ok(ws) => Some(Local {
            ws,
            id: None,
            source,
            name: String::new(),
            name_sent: String::new(),
            editing: false,
            joined: false,
        }),
        Err(e) => {
            error!("failed to connect to {url}: {e:?}");
            None
        }
    };
    for i in 0..count {
        if let Some(lp) = connect(Source::Keyboard(BINDS[i.min(BINDS.len() - 1)])) {
            locals.push(lp);
        }
    }

    // Native controllers: one player per pad, hot-plugged at runtime. Seed with
    // any pads already connected at startup.
    #[cfg(not(target_arch = "wasm32"))]
    let mut pads = gamepad::Pads::new();
    #[cfg(not(target_arch = "wasm32"))]
    for id in pads.connected_ids() {
        if let Some(lp) = connect(Source::Pad(id)) {
            locals.push(lp);
        }
    }

    let mut latest: Option<GameState> = None;
    // On-screen joystick + bomb button. Only consulted on touch devices, where
    // there is exactly one (wasm) local player.
    let touch_input = web::is_touch();
    let mut controls = touch::Touch::new();
    // Whether the soft keyboard (hidden HTML input) is currently shown.
    let mut name_input_shown = false;

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

        // Controller hot-plug: a newly connected pad becomes a new player; an
        // unplugged one drops its connection (dropping the socket lets the
        // server clean the player up).
        #[cfg(not(target_arch = "wasm32"))]
        for change in pads.poll() {
            match change {
                gamepad::Hotplug::Connected(id) => {
                    let known = locals
                        .iter()
                        .any(|l| matches!(&l.source, Source::Pad(p) if *p == id));
                    if !known {
                        if let Some(lp) = connect(Source::Pad(id)) {
                            locals.push(lp);
                        }
                    }
                }
                gamepad::Hotplug::Disconnected(id) => {
                    if let Some(pos) = locals
                        .iter()
                        .position(|l| matches!(&l.source, Source::Pad(p) if *p == id))
                    {
                        let removed = locals.remove(pos);
                        forget_player(&mut latest, removed.id);
                    }
                }
            }
        }

        // Read the on-screen controls every frame so the joystick tracks the
        // drag (the resulting input is only consumed by the wasm touch player,
        // below; on native there are no touches and it's discarded).
        #[allow(unused_variables)]
        let touch_action = controls.update();

        let phase_lobby = matches!(&latest, Some(g) if g.phase == Phase::Lobby);

        // Native lobby menu: 0/1/2 set the number of split-keyboard players
        // (controllers add players on top of these). Disabled while a name is
        // being typed so the digits don't land in the name.
        #[cfg(not(target_arch = "wasm32"))]
        if phase_lobby && !locals.iter().any(|l| l.editing) {
            let target = if is_key_pressed(KeyCode::Key0) {
                Some(0)
            } else if is_key_pressed(KeyCode::Key1) {
                Some(1)
            } else if is_key_pressed(KeyCode::Key2) {
                Some(2)
            } else {
                None
            };
            if let Some(k) = target {
                let kb: Vec<usize> = locals
                    .iter()
                    .enumerate()
                    .filter(|(_, l)| l.source.keyboard_binds().is_some())
                    .map(|(i, _)| i)
                    .collect();
                if kb.len() > k {
                    // Drop the trailing keyboard players (leave controllers be).
                    for &idx in kb[k..].iter().rev() {
                        let removed = locals.remove(idx);
                        forget_player(&mut latest, removed.id);
                    }
                } else {
                    for slot in kb.len()..k {
                        if let Some(lp) = connect(Source::Keyboard(BINDS[slot.min(BINDS.len() - 1)])) {
                            locals.push(lp);
                        }
                    }
                }
            }
        }

        // Name entry. Editing is explicit (press E to start) so stray key-mashing
        // never leaks into names. The focused player — the first local who hasn't
        // readied up — accepts typed input; the host keyboard can name controller
        // players this way too (they can't type for themselves).
        let focus = if phase_lobby {
            focused_local(&locals, latest.as_ref())
        } else {
            None
        };
        // Only the focused player may be editing.
        for (j, lp) in locals.iter_mut().enumerate() {
            if Some(j) != focus {
                lp.editing = false;
            }
        }

        // On touch, name entry is the hidden HTML input (a real soft keyboard);
        // skip the keyboard E-to-edit flow entirely.
        if touch_input {
            if let Some(i) = focus {
                if !name_input_shown {
                    web::name_show();
                    name_input_shown = true;
                }
                if let Some(v) = web::name_value() {
                    locals[i].name = v;
                }
            } else if name_input_shown {
                web::name_hide();
                name_input_shown = false;
            }
        } else if let Some(i) = focus {
            if locals[i].editing {
                // Finish on E (any player, incl. controllers) or on a keyboard
                // player's own bomb key (which also readies them up in one press).
                let kb_finish = locals[i]
                    .source
                    .keyboard_binds()
                    .is_some_and(|b| is_key_pressed(b.bomb_key()));
                if is_key_pressed(KeyCode::E) || kb_finish {
                    locals[i].editing = false;
                    while get_char_pressed().is_some() {} // swallow the finishing key
                } else {
                    input::edit_name(&mut locals[i].name);
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
        }
        let editing_id = focus.and_then(|i| if locals[i].editing { locals[i].id } else { None });

        // Mute toggle (M), ignored while typing a name so 'm' goes into the name.
        if editing_id.is_none() && is_key_pressed(KeyCode::M) {
            audio.toggle_mute();
        }
        // Sound effects + music, derived from what changed in the snapshot.
        audio.update(&latest);

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
                // Native: each player reads its own source. Web guest is a
                // single player whose input prefers a connected gamepad, then
                // touch, then the keyboard.
                #[cfg(not(target_arch = "wasm32"))]
                let input = match &lp.source {
                    Source::Keyboard(b) => read_input(b),
                    Source::Pad(id) => pads.read(*id),
                };
                #[cfg(target_arch = "wasm32")]
                let input = if web::gamepad_present() {
                    web::gamepad_input()
                } else if touch_input {
                    touch_action
                } else {
                    match &lp.source {
                        Source::Keyboard(b) => read_input(b),
                    }
                };
                send(&lp.ws, &ClientMsg::Input(input));
            }
        }

        let my_ids: Vec<PlayerId> = locals.iter().filter_map(|l| l.id).collect();
        render::frame(&assets, &latest, &my_ids, editing_id);
        // Native lobby menu line: controllers connected + keyboard-player count.
        #[cfg(not(target_arch = "wasm32"))]
        if phase_lobby {
            let pads = locals.iter().filter(|l| l.source.keyboard_binds().is_none()).count();
            let keyboard = locals.len() - pads;
            render::lobby_status(pads, keyboard);
        }
        if touch_input {
            // Show the joystick only during a live round; the bomb button is
            // always up (it readies in the lobby and during the countdown).
            let in_round = matches!(&latest, Some(g) if g.phase == Phase::Playing);
            controls.draw(in_round);
        }
        next_frame().await;
    }
}

fn send(ws: &WebSocket, msg: &ClientMsg) {
    if let Ok(bytes) = bincode::serialize(msg) {
        ws.send_bytes(&bytes);
    }
}

/// Drop a just-removed local player from our cached snapshot immediately, so the
/// view reflects the removal even when no socket remains to deliver a fresh one
/// (e.g. setting keyboard players to 0 with no controllers connected — the
/// client would otherwise keep rendering the last snapshot's ghost names).
#[cfg(not(target_arch = "wasm32"))]
fn forget_player(latest: &mut Option<GameState>, id: Option<PlayerId>) {
    if let (Some(id), Some(g)) = (id, latest.as_mut()) {
        g.players.retain(|p| p.id != id);
    }
}

/// The local player currently accepting typed name input: the first local (of
/// any input source) who isn't ready yet, so players are named in turn. Includes
/// controller players — they can't type, but the host keyboard names them here.
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

/// Number of split-keyboard players: `--players 0|1|2` (or `BRM_PLAYERS`), 2 by
/// default. 0 is for controller-only sessions (each connected pad still adds its
/// own player).
#[cfg(not(target_arch = "wasm32"))]
fn local_player_count() -> usize {
    arg_after("--players")
        .or_else(|| std::env::var("BRM_PLAYERS").ok())
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(2)
        .clamp(0, 2)
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

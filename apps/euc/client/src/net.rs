//! WebSocket transport: JSON frames in/out, reconnect with backoff, and a
//! process-wide sender so any UI handler can fire a `ClientMsg`.

use std::cell::{Cell, RefCell};
use std::rc::Rc;

use euc_shared::{ClientMsg, ServerMsg};
use leptos::prelude::*;
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;
use web_sys::{MessageEvent, WebSocket};

use crate::state::{storage_get, AppState};

thread_local! {
    static SOCKET: RefCell<Option<WebSocket>> = const { RefCell::new(None) };
}

pub fn send(msg: &ClientMsg) {
    let text = serde_json::to_string(msg).expect("ClientMsg serializes");
    SOCKET.with(|s| {
        if let Some(ws) = &*s.borrow() {
            let _ = ws.send_with_str(&text);
        }
    });
}

/// Bounce to the login page if the server says our session is gone.
fn redirect_if_unauthenticated() {
    let Some(window) = web_sys::window() else { return };
    let fetched = wasm_bindgen_futures::JsFuture::from(window.fetch_with_str("/api/session"));
    wasm_bindgen_futures::spawn_local(async move {
        if let Ok(value) = fetched.await {
            if let Ok(resp) = value.dyn_into::<web_sys::Response>() {
                if resp.status() == 401 {
                    if let Some(window) = web_sys::window() {
                        let _ = window.location().assign("/login.html");
                    }
                }
            }
        }
    });
}

pub fn set_timeout(ms: i32, f: impl FnOnce() + 'static) {
    let cb = Closure::once_into_js(f);
    if let Some(window) = web_sys::window() {
        let _ = window
            .set_timeout_with_callback_and_timeout_and_arguments_0(cb.unchecked_ref(), ms);
    }
}

pub fn connect(state: AppState) {
    let window = web_sys::window().expect("browser window");
    let location = window.location();
    let proto = if location.protocol().as_deref() == Ok("https:") {
        "wss"
    } else {
        "ws"
    };
    let host = location.host().expect("location.host");
    let url = match storage_get("euc_player") {
        Some(player) => format!("{proto}://{host}/ws?player={player}"),
        None => format!("{proto}://{host}/ws"),
    };
    let Ok(ws) = WebSocket::new(&url) else {
        set_timeout(2000, move || connect(state));
        return;
    };

    let opened = Rc::new(Cell::new(false));

    let opened_flag = opened.clone();
    let onopen = Closure::<dyn FnMut()>::new(move || {
        opened_flag.set(true);
        state.connected.set(true);
        let name = state.name.get_untracked();
        if !name.is_empty() {
            send(&ClientMsg::Hello { name });
        }
    });
    ws.set_onopen(Some(onopen.as_ref().unchecked_ref()));
    onopen.forget();

    let onmessage = Closure::<dyn FnMut(MessageEvent)>::new(move |ev: MessageEvent| {
        if let Some(text) = ev.data().as_string() {
            match serde_json::from_str::<ServerMsg>(&text) {
                Ok(msg) => state.apply(msg),
                Err(err) => leptos::logging::warn!("bad server message: {err}"),
            }
        }
    });
    ws.set_onmessage(Some(onmessage.as_ref().unchecked_ref()));
    onmessage.forget();

    let onclose = Closure::<dyn FnMut()>::new(move || {
        state.connected.set(false);
        state.table.set(None);
        SOCKET.with(|s| s.borrow_mut().take());
        if !opened.get() {
            // Never connected: possibly an expired/missing auth token rather
            // than a server blip — the session probe settles it.
            redirect_if_unauthenticated();
        }
        set_timeout(1500, move || connect(state));
    });
    ws.set_onclose(Some(onclose.as_ref().unchecked_ref()));
    onclose.forget();

    SOCKET.with(|s| *s.borrow_mut() = Some(ws));
}

//! Leptos CSR browser client for the Euchre server. One WebSocket, a handful
//! of signals, and a UI rendered entirely from the server's redacted
//! `TableView` — the client holds no game logic beyond `view.legal`.

mod net;
mod state;
mod ui;

use wasm_bindgen::prelude::*;

#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
    leptos::mount::mount_to_body(ui::App);
}

//! Notes scratchpad, hand-rolled on `web-sys`. One half of the Phase 0
//! framework bake-off; `../notes_leptos` is the same app on Leptos, and the
//! only interesting output is the size difference between the two `.html`
//! files.
//!
//! Deliberately minimal — a textarea and Ctrl+S — so the measurement reflects
//! framework overhead rather than app code.

use lrb_monofile::web;
use lrb_monofile::{Payload, DEFAULT_SHELL};
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast as _;

const CONTENT_TYPE: &str = "text/plain";

#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
    if let Err(e) = mount() {
        web_sys::console::error_1(&format!("notes_sys: {e}").into());
    }
}

fn textarea() -> web_sys::HtmlTextAreaElement {
    web_sys::window()
        .and_then(|w| w.document())
        .and_then(|d| d.get_element_by_id("notes"))
        .expect("notes textarea is mounted")
        .unchecked_into()
}

fn mount() -> Result<(), String> {
    let document = web_sys::window()
        .and_then(|w| w.document())
        .ok_or("no document")?;
    let app = document.get_element_by_id("app").ok_or("no #app")?;

    let initial = web::current_payload().map_err(|e| e.to_string())?;
    let text = String::from_utf8_lossy(&initial.data).into_owned();

    app.set_inner_html(
        "<div style=\"padding:1rem;display:flex;flex-direction:column;gap:.6rem;height:100%;\
         box-sizing:border-box\">\
         <div style=\"font-size:12px;opacity:.7\">notes (web-sys) — Ctrl+S to save</div>\
         <textarea id=\"notes\" style=\"flex:1;font:13px/1.5 ui-monospace,monospace;padding:.6rem\"\
         ></textarea></div>",
    );
    textarea().set_value(&text);

    if !web::can_save_in_place() {
        web::show_toast(
            "Ctrl+S will download a copy \u{2014} this browser can\u{2019}t save in place.",
        );
    }

    let on_keydown = Closure::<dyn FnMut(web_sys::KeyboardEvent)>::new(
        move |e: web_sys::KeyboardEvent| {
            if !(e.ctrl_key() || e.meta_key()) || e.key() != "s" {
                return;
            }
            e.prevent_default();
            wasm_bindgen_futures::spawn_local(async move {
                let doc = Payload::new(CONTENT_TYPE, textarea().value().into_bytes());
                // `save` acquires the write target before rendering, so the
                // picker still has the user activation from this keypress.
                match web::save(DEFAULT_SHELL, &doc, false).await {
                    // `save` toasts its own outcome; nothing to add.
                    Ok(_) => {}
                    Err(e) => web_sys::console::error_1(&format!("save failed: {e}").into()),
                }
            });
        },
    );
    document
        .add_event_listener_with_callback("keydown", on_keydown.as_ref().unchecked_ref())
        .map_err(|e| format!("{e:?}"))?;
    on_keydown.forget();

    Ok(())
}

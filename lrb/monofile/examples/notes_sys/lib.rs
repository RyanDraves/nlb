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

const CONTENT_TYPE: &str = "text/plain";

#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
    // Scopes this app's IndexedDB database. Must precede any save or
    // draft call; see lrb_monofile::web::configure.
    web::configure("notes-sys");
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

    app.set_inner_html(
        "<div style=\"padding:1rem;display:flex;flex-direction:column;gap:.6rem;height:100%;\
         box-sizing:border-box\">\
         <div id=\"hint\" style=\"font-size:12px;opacity:.7\"></div>\
         <textarea id=\"notes\" style=\"flex:1;font:13px/1.5 ui-monospace,monospace;padding:.6rem\"\
         ></textarea></div>",
    );
    document
        .get_element_by_id("hint")
        .ok_or("no #hint")?
        .set_text_content(Some(if web::can_save_in_place() {
            "notes (web-sys) — Ctrl+S saves this file"
        } else {
            "notes (web-sys) — Ctrl+S saves locally, Ctrl+Shift+S downloads a copy"
        }));

    // A stored draft may hold edits made after the file was last written.
    wasm_bindgen_futures::spawn_local(async {
        match web::current_document().await {
            Ok((doc, from_draft)) => {
                textarea().set_value(&String::from_utf8_lossy(&doc.data));
                if from_draft {
                    web::show_toast("Restored unsaved changes");
                    web::set_dirty(true);
                }
            }
            Err(e) => {
                web::show_toast("Couldn't read this file's contents — starting empty.");
                web_sys::console::error_1(&format!("load failed: {e}").into());
            }
        }
    });

    let on_input = Closure::<dyn FnMut()>::new(|| web::set_dirty(true));
    textarea()
        .add_event_listener_with_callback("input", on_input.as_ref().unchecked_ref())
        .map_err(|e| format!("{e:?}"))?;
    on_input.forget();

    let on_keydown = Closure::<dyn FnMut(web_sys::KeyboardEvent)>::new(
        move |e: web_sys::KeyboardEvent| {
            if !(e.ctrl_key() || e.meta_key()) || e.key().to_ascii_lowercase() != "s" {
                return;
            }
            e.prevent_default();
            let export = e.shift_key();
            wasm_bindgen_futures::spawn_local(async move {
                let doc = Payload::new(CONTENT_TYPE, textarea().value().into_bytes());
                // Both paths acquire the write target before rendering, so the
                // picker still has the user activation from this keypress.
                let r = if export {
                    web::export(DEFAULT_SHELL, &doc).await
                } else {
                    web::save(DEFAULT_SHELL, &doc, false).await
                };
                // `save`/`export` toast their own outcome; nothing to add.
                if let Err(e) = r {
                    web_sys::console::error_1(&format!("save failed: {e}").into());
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

//! Notes scratchpad on Leptos. The other half of the Phase 0 framework
//! bake-off — deliberately the same app as `../notes_sys`, so the difference in
//! bundled `.html` size is attributable to the framework.

use leptos::prelude::*;
use lrb_monofile::web;
use lrb_monofile::{Payload, DEFAULT_SHELL};
use wasm_bindgen::prelude::*;

const CONTENT_TYPE: &str = "text/plain";

#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
    // Scopes this app's IndexedDB database. Must precede any save or
    // draft call; see lrb_monofile::web::configure.
    web::configure("notes-leptos");
    let mount_point = web_sys::window()
        .and_then(|w| w.document())
        .and_then(|d| d.get_element_by_id("app"))
        .expect("#app is in the shell");
    // `mount_to` returns an `UnmountHandle` whose `Drop` tears the app straight
    // back down — unlike `mount_to_body`, which returns `()`. Dropping it here
    // renders nothing at all, silently and with no console error.
    leptos::mount::mount_to(mount_point.unchecked_into(), App).forget();
}

#[component]
fn App() -> impl IntoView {
    let text = RwSignal::new(String::new());

    // A stored draft may hold edits made after the file was last written.
    wasm_bindgen_futures::spawn_local(async move {
        match web::current_document().await {
            Ok((doc, from_draft)) => {
                text.set(String::from_utf8_lossy(&doc.data).into_owned());
                if from_draft {
                    web::show_toast("Restored unsaved changes");
                    web::set_dirty(true);
                }
            }
            Err(e) => {
                web::show_toast("Couldn't read this file's contents — starting empty.");
                leptos::logging::error!("load failed: {e}");
            }
        }
    });

    let hint = if web::can_save_in_place() {
        "notes (leptos) — Ctrl+S saves this file"
    } else {
        "notes (leptos) — Ctrl+S saves locally, Ctrl+Shift+S downloads a copy"
    };

    let on_keydown = Closure::<dyn FnMut(web_sys::KeyboardEvent)>::new(
        move |e: web_sys::KeyboardEvent| {
            if !(e.ctrl_key() || e.meta_key()) || e.key().to_ascii_lowercase() != "s" {
                return;
            }
            e.prevent_default();
            let export = e.shift_key();
            wasm_bindgen_futures::spawn_local(async move {
                let doc = Payload::new(CONTENT_TYPE, text.get_untracked().into_bytes());
                // Both paths acquire the write target before rendering, so the
                // picker still has the user activation from this keypress.
                let r = if export {
                    web::export(DEFAULT_SHELL, &doc).await
                } else {
                    web::save(DEFAULT_SHELL, &doc, false).await
                };
                // `save`/`export` toast their own outcome; nothing to add.
                if let Err(e) = r {
                    leptos::logging::error!("save failed: {e}");
                }
            });
        },
    );
    if let Some(doc) = web_sys::window().and_then(|w| w.document()) {
        let _ = doc
            .add_event_listener_with_callback("keydown", on_keydown.as_ref().unchecked_ref());
    }
    on_keydown.forget();

    view! {
        <div style="padding:1rem;display:flex;flex-direction:column;gap:.6rem;height:100%;box-sizing:border-box">
            <div style="font-size:12px;opacity:.7">{hint}</div>
            <textarea
                style="flex:1;font:13px/1.5 ui-monospace,monospace;padding:.6rem"
                prop:value=move || text.get()
                on:input:target=move |e| { text.set(e.target().value()); web::set_dirty(true); }
            ></textarea>
        </div>
    }
}

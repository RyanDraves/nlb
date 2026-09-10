//! Notes scratchpad on Leptos. The other half of the Phase 0 framework
//! bake-off — deliberately the same app as `../notes_sys`, so the difference in
//! bundled `.html` size is attributable to the framework.

use leptos::prelude::*;
use lrb_monofile::web;
use lrb_monofile::{Payload, DEFAULT_SHELL};
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast as _;

const CONTENT_TYPE: &str = "text/plain";

#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
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
    let initial = web::current_payload()
        .map(|p| String::from_utf8_lossy(&p.data).into_owned())
        .unwrap_or_default();
    let text = RwSignal::new(initial);

    if !web::can_save_in_place() {
        web::show_toast("Ctrl+S will download a copy \u{2014} this browser can\u{2019}t save in place.");
    }

    let on_keydown = Closure::<dyn FnMut(web_sys::KeyboardEvent)>::new(
        move |e: web_sys::KeyboardEvent| {
            if !(e.ctrl_key() || e.meta_key()) || e.key() != "s" {
                return;
            }
            e.prevent_default();
            wasm_bindgen_futures::spawn_local(async move {
                let doc = Payload::new(CONTENT_TYPE, text.get_untracked().into_bytes());
                // `save` acquires the write target before rendering, so the
                // picker still has the user activation from this keypress.
                match web::save(DEFAULT_SHELL, &doc, false).await {
                    // `save` toasts its own outcome; nothing to add.
                    Ok(_) => {}
                    Err(e) => leptos::logging::error!("save failed: {e}"),
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
            <div style="font-size:12px;opacity:.7">"notes (leptos) — Ctrl+S to save"</div>
            <textarea
                style="flex:1;font:13px/1.5 ui-monospace,monospace;padding:.6rem"
                prop:value=move || text.get()
                on:input:target=move |e| text.set(e.target().value())
            ></textarea>
        </div>
    }
}

//! Leptos CSR browser client for hyd. Polls `/api/progress` every 5s and
//! renders the progress bars; each has a delete button. All rendering is
//! wholesale from the latest fetch — a handful of bars, so fine-grained
//! reactivity would buy nothing.

use gloo_net::http::Request;
use gloo_timers::callback::Interval;
use hyd_shared::{fraction, ProgressBar};
use leptos::prelude::*;
use wasm_bindgen::prelude::*;

const POLL_MS: u32 = 5000;

#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
    leptos::mount::mount_to_body(App);
}

async fn fetch_bars() -> Result<Vec<ProgressBar>, String> {
    let resp = Request::get("/api/progress")
        .send()
        .await
        .map_err(|e| e.to_string())?;
    resp.json::<Vec<ProgressBar>>()
        .await
        .map_err(|e| e.to_string())
}

#[component]
fn App() -> impl IntoView {
    let bars = RwSignal::new(Vec::<ProgressBar>::new());

    let reload = move || {
        wasm_bindgen_futures::spawn_local(async move {
            if let Ok(v) = fetch_bars().await {
                bars.set(v);
            }
        });
    };
    reload();
    // Keep polling for the lifetime of the page. `forget` leaks the handle so
    // the interval isn't cancelled when this scope ends.
    Interval::new(POLL_MS, move || reload()).forget();

    let delete = move |id: i32| {
        wasm_bindgen_futures::spawn_local(async move {
            let _ = Request::delete(&format!("/api/progress/{id}")).send().await;
            if let Ok(v) = fetch_bars().await {
                bars.set(v);
            }
        });
    };

    view! {
        <div class="page">
            <header class="header">
                <span class="hourglass">"⏳"</span>
                "HYD"
            </header>
            <section class="bars">
                {move || {
                    bars.get()
                        .into_iter()
                        .map(|bar| bar_view(bar, delete))
                        .collect_view()
                }}
            </section>
        </div>
    }
}

fn bar_view(bar: ProgressBar, delete: impl Fn(i32) + Copy + 'static) -> impl IntoView {
    let id = bar.id;
    let pct = fraction(bar.value, bar.max_value);
    let caption = format!("{} - {}/{}", bar.label, bar.value, bar.max_value.unwrap_or(0));
    let status = bar.status.clone();
    view! {
        <div class="bar">
            <div class="row">
                <div class="track">
                    <div class="fill" style=format!("width:{pct}%")></div>
                    <div class="caption">{caption}</div>
                </div>
                <button class="del" title="Delete" on:click=move |_| delete(id)>
                    "🗑"
                </button>
            </div>
            {status.map(|s| view! { <div class="status">{s}</div> })}
        </div>
    }
}

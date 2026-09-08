//! Leptos CSR browser client for iir. Fetches `/api/weather` and shows whether
//! it is raining in Boulder, with a Refresh button. No client-side logic beyond
//! rendering the server's answer.

use gloo_net::http::Request;
use iir_shared::{ErrorBody, WeatherStatus};
use leptos::prelude::*;
use wasm_bindgen::prelude::*;

#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
    leptos::mount::mount_to_body(App);
}

/// One request to `/api/weather`. `Ok(raining)` on success, `Err(message)`
/// on any transport/parse error or a server-reported error.
async fn fetch_weather() -> Result<bool, String> {
    let resp = Request::get("/api/weather")
        .send()
        .await
        .map_err(|e| e.to_string())?;
    if resp.ok() {
        let status: WeatherStatus = resp.json().await.map_err(|e| e.to_string())?;
        Ok(status.raining)
    } else {
        match resp.json::<ErrorBody>().await {
            Ok(body) => Err(body.error),
            Err(e) => Err(e.to_string()),
        }
    }
}

#[component]
fn App() -> impl IntoView {
    // `None` = in flight / not yet loaded.
    let result = RwSignal::<Option<Result<bool, String>>>::new(None);

    let load = move || {
        result.set(None);
        wasm_bindgen_futures::spawn_local(async move {
            result.set(Some(fetch_weather().await));
        });
    };
    // Kick off the initial fetch on mount.
    load();

    view! {
        <main class="wrap">
            <h1>"Is it raining in Boulder, CO?"</h1>
            {move || match result.get() {
                None => view! { <p class="status">"Loading..."</p> }.into_any(),
                Some(Ok(true)) => {
                    view! { <p class="status yes">"Yes, it is raining."</p> }.into_any()
                }
                Some(Ok(false)) => {
                    view! { <p class="status no">"No, it is not raining."</p> }.into_any()
                }
                Some(Err(e)) => view! { <p class="status err">{e}</p> }.into_any(),
            }}
            <button on:click=move |_| load()>"Refresh"</button>
        </main>
    }
}

//! "Is it raining in Boulder, CO?" — axum server. Serves the Leptos wasm
//! client and one JSON endpoint that proxies OpenWeatherMap (keeping the API
//! key server-side). Run with `bazel run //apps/iir:serve`; tune with
//! `IIR_PORT`, `IIR_WEB_DIR`, and `OPENWEATHER_API_KEY[_FILE]`.

use std::sync::Arc;

use axum::extract::State;
use axum::http::StatusCode;
use axum::middleware;
use axum::response::{IntoResponse, Response};
use axum::routing::get;
use axum::{Json, Router};
use iir_shared::{is_raining, ErrorBody, OwmResponse, WeatherStatus};
use tower_http::services::ServeDir;

// Boulder, CO.
const LAT: &str = "40.01003";
const LON: &str = "-105.24389";
const OWM_URL: &str = "https://api.openweathermap.org/data/2.5/weather";

struct AppCtx {
    api_key: Option<String>,
    http: reqwest::Client,
}

fn build_router(ctx: Arc<AppCtx>, web_dir: &str) -> Router {
    Router::new()
        .route("/api/weather", get(weather))
        .fallback_service(ServeDir::new(web_dir))
        .layer(middleware::from_fn(lrb_serve::no_cache))
        .with_state(ctx)
}

#[tokio::main]
async fn main() {
    env_logger::init();

    let api_key = lrb_config::env_or_file("OPENWEATHER_API_KEY");
    if api_key.is_none() {
        log::warn!("OPENWEATHER_API_KEY not set — /api/weather will return an error");
    }
    let ctx = Arc::new(AppCtx {
        api_key,
        http: reqwest::Client::new(),
    });

    let web_dir = lrb_serve::web_dir("IIR_WEB_DIR", "apps/iir/web");
    let router = build_router(ctx, &web_dir);

    lrb_serve::serve(router, lrb_config::env_port("IIR_PORT", 3000), "iir", "").await;
}

fn error(status: StatusCode, message: impl Into<String>) -> Response {
    (
        status,
        Json(ErrorBody {
            error: message.into(),
        }),
    )
        .into_response()
}

async fn weather(State(ctx): State<Arc<AppCtx>>) -> Response {
    let Some(key) = ctx.api_key.as_deref() else {
        return error(StatusCode::INTERNAL_SERVER_ERROR, "API key not configured");
    };

    log::info!("fetching weather from {OWM_URL} (lat={LAT}, lon={LON})");
    let resp = ctx
        .http
        .get(OWM_URL)
        .query(&[
            ("lat", LAT),
            ("lon", LON),
            ("units", "metric"),
            ("appid", key),
        ])
        .send()
        .await;

    let resp = match resp {
        Ok(r) => r,
        Err(e) => return error(StatusCode::INTERNAL_SERVER_ERROR, e.to_string()),
    };

    if !resp.status().is_success() {
        let status = StatusCode::from_u16(resp.status().as_u16())
            .unwrap_or(StatusCode::BAD_GATEWAY);
        return error(status, "Failed to fetch weather");
    }

    match resp.json::<OwmResponse>().await {
        Ok(owm) => Json(WeatherStatus {
            raining: is_raining(&owm),
        })
        .into_response(),
        Err(e) => error(StatusCode::INTERNAL_SERVER_ERROR, e.to_string()),
    }
}

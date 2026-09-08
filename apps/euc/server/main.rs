//! Authoritative Euchre server: hosts the lobby of table actors, accepts one
//! WebSocket per client, and serves the static wasm web client. Run with
//! `bazel run //apps/euc:serve`; tune with `EUC_PORT`, `EUC_WEB_DIR`, and the
//! auth env vars (`EUC_SITE_PASSWORD[_FILE]`, `EUC_TOKEN_SECRET[_FILE]` —
//! auth is disabled when no password is configured).

mod auth;
mod lobby;
mod table;
mod ws;

#[cfg(test)]
mod tests;

use std::sync::Arc;

use axum::middleware;
use axum::routing::{get, post};
use axum::Router;
use euc_shared::RuleConfig;
use tower_http::services::ServeDir;

use lobby::Lobby;

pub struct AppCtx {
    pub lobby: Arc<Lobby>,
    pub auth: auth::AuthConfig,
}

fn build_router(ctx: Arc<AppCtx>, web_dir: &str) -> Router {
    Router::new()
        .route("/ws", get(ws::handler))
        .route("/api/login", post(auth::login))
        .route("/api/session", get(auth::session))
        .fallback_service(ServeDir::new(web_dir))
        .layer(middleware::from_fn_with_state(ctx.clone(), auth::middleware))
        .layer(middleware::from_fn(lrb_serve::no_cache))
        .with_state(ctx)
}

#[tokio::main]
async fn main() {
    env_logger::init();

    let lobby = Lobby::new();
    // A standing table so there's always somewhere to sit.
    lobby.create_table_with_id("MAIN".into(), "Main Table".into(), RuleConfig::default(), true);

    let auth = auth::AuthConfig::from_env();
    if !auth.enabled() {
        log::warn!("EUC_SITE_PASSWORD not set — running with auth DISABLED");
    }
    let ctx = Arc::new(AppCtx { lobby, auth });

    let web_dir = lrb_serve::web_dir("EUC_WEB_DIR", "apps/euc/web");
    let router = build_router(ctx, &web_dir);

    let port = lrb_config::env_port("EUC_PORT", 8080);
    lrb_serve::serve(router, port, "euc", " — ws at /ws").await;
}

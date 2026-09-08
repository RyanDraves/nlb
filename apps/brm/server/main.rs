//! Authoritative Bomberman server: one process that runs the simulation, accepts
//! a WebSocket connection per player, and serves the static wasm web client so
//! browser/phone guests can join over the LAN. Run with `bazel run
//! //apps/brm:serve`; tune with `BRM_PORT`, `BRM_WEB_DIR`, `BRM_SEED`.

mod game;
mod ws;

use axum::middleware;
use axum::routing::get;
use axum::Router;
use tower_http::services::ServeDir;

use game::App;

#[tokio::main]
async fn main() {
    env_logger::init();

    let seed = std::env::var("BRM_SEED")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or_else(|| {
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_nanos() as u64)
                .unwrap_or(0x9e3779b9)
        });

    let app = App::new(seed);
    tokio::spawn(game::run(app.clone()));

    let web_dir = lrb_serve::web_dir("BRM_WEB_DIR", "apps/brm/web");
    let router = Router::new()
        .route("/ws", get(ws::handler))
        .fallback_service(ServeDir::new(web_dir))
        .layer(middleware::from_fn(lrb_serve::no_cache))
        .with_state(app);

    let port = lrb_config::env_port("BRM_PORT", 8080);
    let extra = format!(" — open http://<this-machine-ip>:{port} on the LAN, ws at /ws");
    lrb_serve::serve(router, port, "brm", &extra).await;
}

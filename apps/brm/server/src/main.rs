//! Authoritative Bomberman server: one process that runs the simulation, accepts
//! a WebSocket connection per player, and serves the static wasm web client so
//! browser/phone guests can join over the LAN. Run with `bazel run
//! //apps/brm:serve`; tune with `BRM_PORT`, `BRM_WEB_DIR`, `BRM_SEED`.

mod game;
mod ws;

use std::net::SocketAddr;

use axum::extract::Request;
use axum::http::{header, HeaderValue};
use axum::middleware::{self, Next};
use axum::response::Response;
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

    let web_dir = std::env::var("BRM_WEB_DIR").unwrap_or_else(|_| "apps/brm/web".to_owned());
    let router = Router::new()
        .route("/ws", get(ws::handler))
        .fallback_service(ServeDir::new(web_dir))
        // Never let browsers cache the client assets — this is a dev/LAN server
        // and stale wasm/JS otherwise causes confusing "it didn't update" bugs.
        .layer(middleware::from_fn(no_cache))
        .with_state(app);

    let port: u16 = std::env::var("BRM_PORT")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(8080);
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    println!("brm server listening on 0.0.0.0:{port} — open http://<this-machine-ip>:{port} on the LAN, ws at /ws");
    axum::serve(listener, router).await.unwrap();
}

async fn no_cache(req: Request, next: Next) -> Response {
    let mut res = next.run(req).await;
    res.headers_mut().insert(
        header::CACHE_CONTROL,
        HeaderValue::from_static("no-store, max-age=0"),
    );
    res
}

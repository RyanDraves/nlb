//! axum plumbing shared by the Rust web apps under `apps/` (brm, euc, hyd, iir).
//!
//! Each of those servers is a router plus the same three pieces of boilerplate:
//! a no-store cache policy, a `*_WEB_DIR` lookup for the static client bundle,
//! and a bind/serve tail. Keeping them here means the cache policy and the
//! listen address have one definition instead of four.

use std::net::SocketAddr;

use axum::extract::Request;
use axum::http::{header, HeaderValue};
use axum::middleware::Next;
use axum::response::Response;
use axum::Router;

/// Stamp `Cache-Control: no-store` on every response.
///
/// The apps ship a wasm client whose filenames are not content-hashed, so a
/// cached bundle shows up as a confusing "it didn't update" bug. Install with
/// `.layer(middleware::from_fn(lrb_serve::no_cache))`.
pub async fn no_cache(req: Request, next: Next) -> Response {
    let mut res = next.run(req).await;
    res.headers_mut().insert(
        header::CACHE_CONTROL,
        HeaderValue::from_static("no-store, max-age=0"),
    );
    res
}

/// Directory holding the static client bundle: `$var` if set, else `default`.
///
/// The default is the in-repo path so `bazel run //apps/<app>:serve` works from
/// the workspace root; the container images set the env var to `/opt/web`.
pub fn web_dir(var: &str, default: &str) -> String {
    std::env::var(var).unwrap_or_else(|_| default.to_owned())
}

/// Bind `0.0.0.0:port` and serve `router` until the process exits.
///
/// `app` and `extra` build the startup banner:
/// `"{app} server listening on 0.0.0.0:{port}{extra}"`. Pass `""` for `extra`
/// when there is nothing to add.
///
/// Panics if the port cannot be bound — these are foreground servers where a
/// failed bind should be loud and immediate.
pub async fn serve(router: Router, port: u16, app: &str, extra: &str) {
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .unwrap_or_else(|e| panic!("{app}: failed to bind {addr}: {e}"));
    println!("{app} server listening on 0.0.0.0:{port}{extra}");
    axum::serve(listener, router).await.unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::routing::get;
    use tower::ServiceExt;

    #[test]
    fn web_dir_prefers_env_then_default() {
        std::env::remove_var("LRB_SERVE_TEST_DIR");
        assert_eq!(web_dir("LRB_SERVE_TEST_DIR", "apps/x/web"), "apps/x/web");
        std::env::set_var("LRB_SERVE_TEST_DIR", "/opt/web");
        assert_eq!(web_dir("LRB_SERVE_TEST_DIR", "apps/x/web"), "/opt/web");
        std::env::remove_var("LRB_SERVE_TEST_DIR");
    }

    #[tokio::test]
    async fn no_cache_sets_header() {
        let router = Router::new()
            .route("/", get(|| async { "hi" }))
            .layer(axum::middleware::from_fn(no_cache));
        let res = router
            .oneshot(Request::builder().uri("/").body(axum::body::Body::empty()).unwrap())
            .await
            .unwrap();
        assert_eq!(
            res.headers().get(header::CACHE_CONTROL).unwrap(),
            "no-store, max-age=0"
        );
    }
}

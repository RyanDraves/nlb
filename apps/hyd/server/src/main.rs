//! hyd — a Postgres-backed progress-bar dashboard. axum
//! server: three JSON CRUD routes plus static serving of the Leptos wasm
//! client. Run with `bazel run //apps/hyd:serve`; tune with `HYD_PORT`,
//! `HYD_WEB_DIR`, and the `POSTGRES_*` / `DATABASE_URL` env vars.
//!
//! The Python `management/` CLI writes to the same `progress` table directly;
//! it is unaffected by this server.

use std::net::SocketAddr;
use std::str::FromStr;
use std::sync::Arc;

use axum::extract::{Path, Request, State};
use axum::http::{header, HeaderValue, StatusCode};
use axum::middleware::{self, Next};
use axum::response::{IntoResponse, Response};
use axum::routing::get;
use axum::{Json, Router};
use deadpool_postgres::{Manager, ManagerConfig, Pool, RecyclingMethod};
use hyd_shared::{ProgressBar, ProgressUpsert};
use tokio_postgres::{Config as PgConfig, NoTls, Row};
use tower_http::services::ServeDir;

struct AppCtx {
    pool: Pool,
}

fn build_router(ctx: Arc<AppCtx>, web_dir: &str) -> Router {
    Router::new()
        .route("/api/progress", get(list_progress).post(upsert_progress))
        .route("/api/progress/:id", axum::routing::delete(delete_progress))
        .fallback_service(ServeDir::new(web_dir))
        .layer(middleware::from_fn(no_cache))
        .with_state(ctx)
}

/// Build a tokio-postgres config from `DATABASE_URL` if set, else from the
/// individual `POSTGRES_*` vars — matching the old `apps/hyd/lib/db.ts`.
fn pg_config() -> PgConfig {
    if let Some(url) = lrb_config::env_or_file("DATABASE_URL") {
        if let Ok(cfg) = PgConfig::from_str(&url) {
            return cfg;
        }
        log::warn!("DATABASE_URL set but unparseable; falling back to POSTGRES_* vars");
    }
    let user = std::env::var("POSTGRES_USER").unwrap_or_else(|_| "hyd".to_owned());
    let host = std::env::var("POSTGRES_HOST").unwrap_or_else(|_| "localhost".to_owned());
    let port = lrb_config::env_port("POSTGRES_PORT", 5432);
    let dbname = std::env::var("POSTGRES_DB").unwrap_or_else(|_| "hyd".to_owned());
    let password = lrb_config::env_or_file("POSTGRES_PASSWORD").unwrap_or_default();

    let mut cfg = PgConfig::new();
    cfg.user(&user)
        .host(&host)
        .port(port)
        .dbname(&dbname)
        .password(password);
    cfg
}

#[tokio::main]
async fn main() {
    env_logger::init();

    let mgr = Manager::from_config(
        pg_config(),
        NoTls,
        ManagerConfig {
            recycling_method: RecyclingMethod::Fast,
        },
    );
    let pool = Pool::builder(mgr)
        .max_size(8)
        .build()
        .expect("failed to build Postgres pool");
    let ctx = Arc::new(AppCtx { pool });

    let web_dir = std::env::var("HYD_WEB_DIR").unwrap_or_else(|_| "apps/hyd/web".to_owned());
    let router = build_router(ctx, &web_dir);

    let port = lrb_config::env_port("HYD_PORT", 3000);
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    println!("hyd server listening on 0.0.0.0:{port}");
    axum::serve(listener, router).await.unwrap();
}

fn row_to_bar(row: &Row) -> ProgressBar {
    ProgressBar {
        id: row.get("id"),
        label: row.get("label"),
        value: row.try_get("value").unwrap_or(0),
        max_value: row.get("max_value"),
        status: row.get("status"),
    }
}

fn db_error(err: impl std::fmt::Display) -> Response {
    log::error!("db error: {err}");
    (
        StatusCode::INTERNAL_SERVER_ERROR,
        "Database error".to_owned(),
    )
        .into_response()
}

async fn list_progress(State(ctx): State<Arc<AppCtx>>) -> Response {
    let client = match ctx.pool.get().await {
        Ok(c) => c,
        Err(e) => return db_error(e),
    };
    match client
        .query(
            "SELECT id, label, value, max_value, status FROM progress ORDER BY id;",
            &[],
        )
        .await
    {
        Ok(rows) => {
            let bars: Vec<ProgressBar> = rows.iter().map(row_to_bar).collect();
            Json(bars).into_response()
        }
        Err(e) => db_error(e),
    }
}

async fn upsert_progress(
    State(ctx): State<Arc<AppCtx>>,
    Json(body): Json<ProgressUpsert>,
) -> Response {
    let client = match ctx.pool.get().await {
        Ok(c) => c,
        Err(e) => return db_error(e),
    };

    let existing = match client
        .query_opt("SELECT id FROM progress WHERE label = $1", &[&body.label])
        .await
    {
        Ok(row) => row,
        Err(e) => return db_error(e),
    };

    let result = if existing.is_some() {
        // COALESCE keeps the stored max_value when the caller omits it.
        client
            .execute(
                "UPDATE progress SET value=$1, max_value=COALESCE($2, max_value), status=$3 \
                 WHERE label=$4",
                &[&body.value, &body.max_value, &body.status, &body.label],
            )
            .await
    } else {
        client
            .execute(
                "INSERT INTO progress (label, value, max_value, status) VALUES ($1, $2, $3, $4)",
                &[&body.label, &body.value, &body.max_value, &body.status],
            )
            .await
    };
    if let Err(e) = result {
        return db_error(e);
    }

    match client
        .query_opt(
            "SELECT id, label, value, max_value, status FROM progress WHERE label=$1;",
            &[&body.label],
        )
        .await
    {
        Ok(Some(row)) => Json(row_to_bar(&row)).into_response(),
        Ok(None) => db_error("row vanished after upsert"),
        Err(e) => db_error(e),
    }
}

async fn delete_progress(State(ctx): State<Arc<AppCtx>>, Path(id): Path<i32>) -> Response {
    let client = match ctx.pool.get().await {
        Ok(c) => c,
        Err(e) => return db_error(e),
    };
    match client
        .execute("DELETE FROM progress WHERE id = $1", &[&id])
        .await
    {
        Ok(_) => (StatusCode::OK, "OK").into_response(),
        Err(e) => db_error(e),
    }
}

async fn no_cache(req: Request, next: Next) -> Response {
    let mut res = next.run(req).await;
    res.headers_mut().insert(
        header::CACHE_CONTROL,
        HeaderValue::from_static("no-store, max-age=0"),
    );
    res
}

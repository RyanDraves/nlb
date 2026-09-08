//! Shared-site-password auth for the public (Tailscale Funnel) deployment.
//!
//! One password gates everything. A successful login mints an HMAC-signed
//! token `player_id.expiry.sig` delivered as an HttpOnly cookie (browsers)
//! and in the response body (bots, who send it as `Authorization: Bearer`
//! or `?token=`). The player id inside the token is the stable identity used
//! for seat reclaim. With no password configured, auth is disabled (dev mode).

use std::sync::Arc;

use axum::extract::{Request, State};
use axum::http::{header, Method, StatusCode};
use axum::middleware::Next;
use axum::response::{IntoResponse, Redirect, Response};
use axum::Json;
use hmac::{Hmac, Mac};
use serde::{Deserialize, Serialize};
use sha2::Sha256;

use crate::AppCtx;

type HmacSha256 = Hmac<Sha256>;

const TOKEN_TTL_SECS: u64 = 30 * 24 * 3600;
/// Paths reachable without a token: the login page and its dependencies, plus
/// the PWA metadata (Safari fetches icons/manifest without cookies).
const OPEN_PATHS: [&str; 8] = [
    "/login.html",
    "/api/login",
    "/api/session",
    "/style.css",
    "/manifest.webmanifest",
    "/icon-180.png",
    "/icon-192.png",
    "/icon-512.png",
];

pub struct AuthConfig {
    password: Option<String>,
    secret: Vec<u8>,
}

/// Reads `EUC_<name>` or, failing that, the file named by `EUC_<name>_FILE`
/// (the docker-secrets pattern).
fn env_or_file(name: &str) -> Option<String> {
    if let Ok(v) = std::env::var(format!("EUC_{name}")) {
        return Some(v.trim().to_string());
    }
    let path = std::env::var(format!("EUC_{name}_FILE")).ok()?;
    Some(std::fs::read_to_string(path).ok()?.trim().to_string())
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn now_unix() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

pub fn random_player_id() -> String {
    let mut bytes = [0u8; 8];
    getrandom::fill(&mut bytes).expect("OS entropy");
    hex(&bytes)
}

impl AuthConfig {
    pub fn from_env() -> Self {
        let password = env_or_file("SITE_PASSWORD").filter(|p| !p.is_empty());
        let secret = match env_or_file("TOKEN_SECRET").filter(|s| !s.is_empty()) {
            Some(s) => s.into_bytes(),
            None => {
                // Ephemeral secret: sessions won't survive a restart. Fine for
                // dev; production should set EUC_TOKEN_SECRET(_FILE).
                if password.is_some() {
                    log::warn!("EUC_TOKEN_SECRET not set; sessions reset on restart");
                }
                let mut bytes = [0u8; 32];
                getrandom::fill(&mut bytes).expect("OS entropy");
                bytes.to_vec()
            }
        };
        Self { password, secret }
    }

    #[cfg(test)]
    pub fn for_test(password: Option<&str>) -> Self {
        Self {
            password: password.map(String::from),
            secret: b"test-secret".to_vec(),
        }
    }

    pub fn enabled(&self) -> bool {
        self.password.is_some()
    }

    fn sign(&self, payload: &str) -> String {
        let mut mac = HmacSha256::new_from_slice(&self.secret).expect("any key length works");
        mac.update(payload.as_bytes());
        hex(&mac.finalize().into_bytes())
    }

    pub fn mint(&self, player_id: &str) -> String {
        let payload = format!("{player_id}.{}", now_unix() + TOKEN_TTL_SECS);
        let sig = self.sign(&payload);
        format!("{payload}.{sig}")
    }

    /// Returns the token's player id if the signature is valid and unexpired.
    pub fn verify(&self, token: &str) -> Option<String> {
        let (payload, sig) = token.rsplit_once('.')?;
        // Compare HMACs of the signatures rather than the strings directly so
        // the comparison cost doesn't leak a prefix match.
        if self.sign(sig) != self.sign(&self.sign(payload)) {
            return None;
        }
        let (player_id, expiry) = payload.split_once('.')?;
        let fresh = expiry.parse::<u64>().ok()? > now_unix();
        (fresh && !player_id.is_empty()).then(|| player_id.to_string())
    }

    pub fn check_password(&self, given: &str) -> bool {
        match &self.password {
            // HMAC both sides so the comparison is constant-time-ish.
            Some(expected) => self.sign(expected) == self.sign(given),
            None => true,
        }
    }
}

/// Set by the middleware for authenticated requests; the WebSocket handler
/// uses it as the player identity.
#[derive(Clone)]
pub struct AuthedPlayer(pub String);

fn bearer_token(req: &Request) -> Option<String> {
    let value = req.headers().get(header::AUTHORIZATION)?.to_str().ok()?;
    value.strip_prefix("Bearer ").map(str::to_string)
}

fn cookie_token(req: &Request) -> Option<String> {
    let cookies = req.headers().get(header::COOKIE)?.to_str().ok()?;
    cookies.split(';').find_map(|c| {
        c.trim().strip_prefix("euc_auth=").map(str::to_string)
    })
}

fn query_token(req: &Request) -> Option<String> {
    req.uri().query()?.split('&').find_map(|kv| {
        kv.strip_prefix("token=").map(str::to_string)
    })
}

pub async fn middleware(State(ctx): State<Arc<AppCtx>>, mut req: Request, next: Next) -> Response {
    if !ctx.auth.enabled() {
        return next.run(req).await;
    }
    if OPEN_PATHS.contains(&req.uri().path()) {
        return next.run(req).await;
    }
    let token = cookie_token(&req)
        .or_else(|| bearer_token(&req))
        .or_else(|| query_token(&req));
    if let Some(player_id) = token.and_then(|t| ctx.auth.verify(&t)) {
        req.extensions_mut().insert(AuthedPlayer(player_id));
        return next.run(req).await;
    }
    let wants_html = req
        .headers()
        .get(header::ACCEPT)
        .and_then(|a| a.to_str().ok())
        .map(|a| a.contains("text/html"))
        .unwrap_or(false);
    if wants_html && req.method() == Method::GET {
        Redirect::to("/login.html").into_response()
    } else {
        StatusCode::UNAUTHORIZED.into_response()
    }
}

#[derive(Deserialize)]
pub struct LoginReq {
    password: String,
}

#[derive(Serialize)]
pub struct LoginResp {
    token: String,
}

/// POST /api/login — password in, signed token out (cookie + body).
pub async fn login(State(ctx): State<Arc<AppCtx>>, req: Request) -> Response {
    // Re-login keeps the identity from a still-valid cookie so a password
    // rotation doesn't cost anyone their seat.
    let existing = cookie_token(&req).and_then(|t| ctx.auth.verify(&t));
    let body = match axum::body::to_bytes(req.into_body(), 4096).await {
        Ok(b) => b,
        Err(_) => return StatusCode::BAD_REQUEST.into_response(),
    };
    let Ok(login) = serde_json::from_slice::<LoginReq>(&body) else {
        return StatusCode::BAD_REQUEST.into_response();
    };
    if !ctx.auth.check_password(&login.password) {
        return StatusCode::UNAUTHORIZED.into_response();
    }
    let player_id = existing.unwrap_or_else(random_player_id);
    let token = ctx.auth.mint(&player_id);
    let cookie = format!(
        "euc_auth={token}; Path=/; Max-Age={TOKEN_TTL_SECS}; HttpOnly; Secure; SameSite=Lax"
    );
    (
        [(header::SET_COOKIE, cookie)],
        Json(LoginResp { token }),
    )
        .into_response()
}

/// GET /api/session — 200 when the request is authenticated (or auth is
/// disabled); the middleware turns everything else into a 401. The login page
/// and the client use it to decide whether to bounce the user.
pub async fn session(State(ctx): State<Arc<AppCtx>>, req: Request) -> Response {
    if !ctx.auth.enabled()
        || cookie_token(&req)
            .and_then(|t| ctx.auth.verify(&t))
            .is_some()
    {
        StatusCode::OK.into_response()
    } else {
        StatusCode::UNAUTHORIZED.into_response()
    }
}

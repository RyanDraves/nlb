//! End-to-end tests: the real router with auth enabled, exercised over HTTP
//! (tower oneshot) and a real WebSocket (tokio-tungstenite).

use std::sync::Arc;
use std::time::Duration;

use axum::body::Body;
use axum::http::{Request, StatusCode};
use euc_shared::{ClientMsg, Phase, Seat, ServerMsg};
use futures_util::{SinkExt, StreamExt};
use tokio_tungstenite::tungstenite;
use tower::ServiceExt;

use crate::auth::AuthConfig;
use crate::lobby::Lobby;
use crate::{build_router, AppCtx};

fn test_ctx() -> Arc<AppCtx> {
    Arc::new(AppCtx {
        lobby: Lobby::new(),
        auth: AuthConfig::for_test(Some("pw")),
    })
}

#[tokio::test]
async fn auth_gates_http_and_login_mints_tokens() {
    let router = build_router(test_ctx(), "apps/euc/web");

    // No token: API requests get 401, browser page loads bounce to the login page.
    let resp = router
        .clone()
        .oneshot(Request::get("/ws").body(Body::empty()).unwrap())
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    let resp = router
        .clone()
        .oneshot(
            Request::get("/")
                .header("accept", "text/html")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::SEE_OTHER);

    // Wrong password rejected; right password yields a signed token.
    let resp = router
        .clone()
        .oneshot(
            Request::post("/api/login")
                .header("content-type", "application/json")
                .body(Body::from(r#"{"password":"nope"}"#))
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    let resp = router
        .clone()
        .oneshot(
            Request::post("/api/login")
                .header("content-type", "application/json")
                .body(Body::from(r#"{"password":"pw"}"#))
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::OK);
    assert!(resp
        .headers()
        .get("set-cookie")
        .unwrap()
        .to_str()
        .unwrap()
        .starts_with("euc_auth="));
    let body = axum::body::to_bytes(resp.into_body(), 65536).await.unwrap();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
    let token = json["token"].as_str().unwrap();

    // The minted token opens the gate.
    let ctx = test_ctx();
    assert!(ctx.auth.verify(token).is_some());
}

/// One scripted client + three heuristic AIs play until a hand completes,
/// over a real listener. Also checks that an unauthenticated socket is refused
/// and that no view ever contains more cards than one player may hold.
#[tokio::test]
async fn full_hand_over_a_real_websocket() {
    std::env::set_var("EUC_AI_DELAY_MS", "5");
    let ctx = test_ctx();
    let token = ctx.auth.mint("cafebabe12345678");
    let router = build_router(ctx, "apps/euc/web");
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    tokio::spawn(async move {
        axum::serve(listener, router).await.unwrap();
    });

    assert!(
        tokio_tungstenite::connect_async(format!("ws://{addr}/ws")).await.is_err(),
        "unauthenticated websocket must be refused"
    );

    let (mut ws, _) = tokio_tungstenite::connect_async(format!("ws://{addr}/ws?token={token}"))
        .await
        .expect("token opens the socket");

    macro_rules! send {
        ($msg:expr) => {
            ws.send(tungstenite::Message::Text(serde_json::to_string(&$msg).unwrap()))
                .await
                .unwrap()
        };
    }
    send!(ClientMsg::Hello { name: "Test".into() });
    send!(ClientMsg::CreateTable { name: "T".into(), rules: Default::default() });
    send!(ClientMsg::TakeSeat { seat: Seat(0) });
    for s in 1..4 {
        send!(ClientMsg::AddAi { seat: Seat(s) });
    }
    send!(ClientMsg::StartGame);

    let deadline = tokio::time::Instant::now() + Duration::from_secs(30);
    loop {
        let msg = tokio::time::timeout_at(deadline, ws.next())
            .await
            .expect("hand did not complete in 30s")
            .expect("socket stayed open")
            .unwrap();
        let tungstenite::Message::Text(text) = msg else { continue };
        let msg: ServerMsg = serde_json::from_str(&text).unwrap();
        let ServerMsg::TableState { view } = msg else { continue };
        if let Some(game) = &view.game {
            assert!(game.hand.len() <= 6, "redacted view leaked cards");
            if matches!(game.phase, Phase::HandDone { .. } | Phase::GameOver { .. }) {
                return; // a full hand was bid, played, and scored
            }
        }
        // Play like the simplest bot: first legal action.
        if let Some(action) = view.legal.first() {
            send!(ClientMsg::Act { action: *action });
        }
    }
}

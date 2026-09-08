//! Per-connection WebSocket handling: parse JSON `ClientMsg` frames, route
//! lobby-scoped ones here, and forward table-scoped ones to the table actor
//! the connection is attached to.

use std::collections::HashMap;
use std::sync::Arc;

use axum::extract::ws::{Message, WebSocket, WebSocketUpgrade};
use axum::extract::{Query, State};
use axum::response::IntoResponse;
use axum::Extension;
use euc_shared::{ClientMsg, ErrorCode, PlayerId, Role, ServerMsg};
use futures_util::{SinkExt, StreamExt};
use tokio::sync::mpsc;

use crate::auth::AuthedPlayer;
use crate::lobby::{ConnId, Lobby};
use crate::table::TableCmd;
use crate::AppCtx;

pub async fn handler(
    ws: WebSocketUpgrade,
    Query(params): Query<HashMap<String, String>>,
    State(ctx): State<Arc<AppCtx>>,
    authed: Option<Extension<AuthedPlayer>>,
) -> impl IntoResponse {
    let identity = authed.map(|Extension(AuthedPlayer(id))| id);
    ws.on_upgrade(move |socket| handle_socket(socket, ctx.lobby.clone(), params, identity))
}

fn sanitize_name(name: &str) -> String {
    let trimmed: String = name.trim().chars().take(20).collect();
    if trimmed.is_empty() {
        "Anon".to_string()
    } else {
        trimmed
    }
}

async fn handle_socket(
    socket: WebSocket,
    lobby: Arc<Lobby>,
    params: HashMap<String, String>,
    identity: Option<PlayerId>,
) {
    let conn = lobby.next_conn_id();
    // With auth enabled the token dictates identity (no impersonation via
    // query param); without it, the client-remembered `?player=` id keeps
    // seat reclaim working across refreshes in dev.
    let player: PlayerId = identity
        .or_else(|| {
            params
                .get("player")
                .filter(|p| (8..=64).contains(&p.len()) && p.chars().all(|c| c.is_ascii_hexdigit()))
                .cloned()
        })
        .unwrap_or_else(crate::auth::random_player_id);
    let mut name = format!("Player {}", &player[..4]);

    let (tx, mut rx) = mpsc::channel::<ServerMsg>(64);
    let (mut sink, mut stream) = socket.split();

    let send_task = tokio::spawn(async move {
        while let Some(msg) = rx.recv().await {
            let text = serde_json::to_string(&msg).expect("ServerMsg serializes");
            if sink.send(Message::Text(text)).await.is_err() {
                break;
            }
        }
    });

    let _ = tx
        .send(ServerMsg::Welcome { player_id: player.clone(), name: name.clone() })
        .await;
    lobby.add_watcher(conn, tx.clone());
    let _ = tx.send(ServerMsg::LobbyState { tables: lobby.summaries() }).await;

    // The table actor this connection is attached to, if any.
    let mut at_table: Option<mpsc::Sender<TableCmd>> = None;

    // A held seat pulls the player straight back to their table.
    if let Some(tid) = lobby.seat_table(&player) {
        if let Some(handle) = lobby.table(&tid) {
            attach(&lobby, &mut at_table, handle, conn, &player, &name, Role::Spectator, &tx).await;
        }
    }

    while let Some(Ok(msg)) = stream.next().await {
        let text = match msg {
            Message::Text(t) => t,
            Message::Close(_) => break,
            _ => continue,
        };
        let Ok(cmsg) = serde_json::from_str::<ClientMsg>(&text) else {
            let _ = tx
                .send(ServerMsg::Error {
                    code: ErrorCode::BadRequest,
                    message: "unparseable message".into(),
                })
                .await;
            continue;
        };
        match cmsg {
            ClientMsg::Hello { name: n } | ClientMsg::SetName { name: n } => {
                name = sanitize_name(&n);
                if let Some(t) = &at_table {
                    let _ = t
                        .send(TableCmd::Msg {
                            conn,
                            msg: ClientMsg::SetName { name: name.clone() },
                        })
                        .await;
                }
            }
            ClientMsg::Ping => {
                let _ = tx.send(ServerMsg::Pong).await;
            }
            ClientMsg::CreateTable { name: tname, rules } => {
                let tname = sanitize_name(&tname);
                let id = lobby.create_table(tname, rules);
                let handle = lobby.table(&id).expect("just created");
                attach(&lobby, &mut at_table, handle, conn, &player, &name, Role::Spectator, &tx)
                    .await;
            }
            ClientMsg::JoinTable { table_id, role } => match lobby.table(&table_id) {
                Some(handle) => {
                    attach(&lobby, &mut at_table, handle, conn, &player, &name, role, &tx).await;
                }
                None => {
                    let _ = tx
                        .send(ServerMsg::Error {
                            code: ErrorCode::NoSuchTable,
                            message: format!("no table {table_id}"),
                        })
                        .await;
                }
            },
            ClientMsg::LeaveTable => {
                if let Some(t) = at_table.take() {
                    let _ = t.send(TableCmd::Detach { conn }).await;
                }
                let _ = tx.send(ServerMsg::LeftTable).await;
                lobby.add_watcher(conn, tx.clone());
                let _ = tx.send(ServerMsg::LobbyState { tables: lobby.summaries() }).await;
            }
            table_msg => match &at_table {
                Some(t) => {
                    let _ = t.send(TableCmd::Msg { conn, msg: table_msg }).await;
                }
                None => {
                    let _ = tx
                        .send(ServerMsg::Error {
                            code: ErrorCode::NotAtTable,
                            message: "join a table first".into(),
                        })
                        .await;
                }
            },
        }
    }

    if let Some(t) = at_table {
        let _ = t.send(TableCmd::Detach { conn }).await;
    }
    lobby.remove_watcher(conn);
    send_task.abort();
}

#[allow(clippy::too_many_arguments)]
async fn attach(
    lobby: &Arc<Lobby>,
    at_table: &mut Option<mpsc::Sender<TableCmd>>,
    handle: mpsc::Sender<TableCmd>,
    conn: ConnId,
    player: &PlayerId,
    name: &str,
    role: Role,
    tx: &mpsc::Sender<ServerMsg>,
) {
    if let Some(t) = at_table.take() {
        let _ = t.send(TableCmd::Detach { conn }).await;
    }
    lobby.remove_watcher(conn);
    let _ = handle
        .send(TableCmd::Attach {
            conn,
            player: player.clone(),
            name: name.to_string(),
            role,
            tx: tx.clone(),
        })
        .await;
    *at_table = Some(handle);
}

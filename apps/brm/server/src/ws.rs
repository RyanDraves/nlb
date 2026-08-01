//! Per-connection WebSocket handling: one socket == one player.

use std::sync::Arc;

use axum::extract::ws::{Message, WebSocket, WebSocketUpgrade};
use axum::extract::State;
use axum::response::IntoResponse;
use brm_shared::{ClientMsg, PlayerId, PlayerInput, ServerMsg};
use futures_util::{SinkExt, StreamExt};

use crate::game::App;

pub async fn handler(ws: WebSocketUpgrade, State(app): State<Arc<App>>) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_socket(socket, app))
}

async fn handle_socket(socket: WebSocket, app: Arc<App>) {
    let id = {
        let mut game = app.game.lock().unwrap();
        game.add_player()
    };
    app.inputs.lock().unwrap().insert(id, PlayerInput::default());

    let (mut sink, mut stream) = socket.split();

    let welcome = bincode::serialize(&ServerMsg::Welcome { id }).unwrap();
    if sink.send(Message::Binary(welcome)).await.is_err() {
        cleanup(&app, id);
        return;
    }

    // Forward broadcast snapshots to this client.
    let mut rx = app.snapshots.subscribe();
    let mut send_task = tokio::spawn(async move {
        while let Ok(bytes) = rx.recv().await {
            if sink.send(Message::Binary((*bytes).clone())).await.is_err() {
                break;
            }
        }
    });

    // Ingest this client's input.
    let recv_app = app.clone();
    let mut recv_task = tokio::spawn(async move {
        while let Some(Ok(msg)) = stream.next().await {
            if let Message::Binary(b) = msg {
                match bincode::deserialize::<ClientMsg>(&b) {
                    Ok(ClientMsg::Input(inp)) => {
                        let mut inputs = recv_app.inputs.lock().unwrap();
                        let e = inputs.entry(id).or_default();
                        e.dx = inp.dx;
                        e.dy = inp.dy;
                        // Latch presses so a bomb tap between ticks isn't lost.
                        e.place_bomb |= inp.place_bomb;
                    }
                    Ok(ClientMsg::Join { name }) | Ok(ClientMsg::SetName { name }) => {
                        recv_app.game.lock().unwrap().set_name(id, &name);
                    }
                    Err(_) => {}
                }
            }
        }
    });

    tokio::select! {
        _ = &mut send_task => recv_task.abort(),
        _ = &mut recv_task => send_task.abort(),
    }
    cleanup(&app, id);
}

fn cleanup(app: &Arc<App>, id: PlayerId) {
    app.game.lock().unwrap().remove_player(id);
    app.inputs.lock().unwrap().remove(&id);
}

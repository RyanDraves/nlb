//! The lobby: registry of running table actors, lobby-screen watchers, and the
//! seat index that lets a reconnecting player reclaim their chair.

use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};

use euc_shared::{PlayerId, RuleConfig, ServerMsg, TableId, TableSummary};
use tokio::sync::mpsc;

use crate::table::{self, TableCmd};

/// Per-WebSocket-connection id, unique for the process lifetime.
pub type ConnId = u64;

/// Table codes avoid look-alike characters so they survive being read aloud.
const CODE_CHARS: &[u8] = b"ABCDEFGHJKMNPQRSTUVWXYZ23456789";

pub struct Lobby {
    tables: Mutex<HashMap<TableId, mpsc::Sender<TableCmd>>>,
    summaries: Mutex<HashMap<TableId, TableSummary>>,
    /// PlayerId -> table currently holding a seat for them (reconnect target).
    seat_index: Mutex<HashMap<PlayerId, TableId>>,
    /// Connections on the lobby screen, to push table-list updates to.
    watchers: Mutex<HashMap<ConnId, mpsc::Sender<ServerMsg>>>,
    next_conn: AtomicU64,
    next_code: AtomicU64,
}

impl Lobby {
    pub fn new() -> Arc<Self> {
        Arc::new(Self {
            tables: Mutex::new(HashMap::new()),
            summaries: Mutex::new(HashMap::new()),
            seat_index: Mutex::new(HashMap::new()),
            watchers: Mutex::new(HashMap::new()),
            next_conn: AtomicU64::new(1),
            next_code: AtomicU64::new(1),
        })
    }

    pub fn next_conn_id(&self) -> ConnId {
        self.next_conn.fetch_add(1, Ordering::Relaxed)
    }

    pub fn create_table(self: &Arc<Self>, name: String, rules: RuleConfig) -> TableId {
        let id = loop {
            let id = self.fresh_code();
            if !self.tables.lock().unwrap().contains_key(&id) {
                break id;
            }
        };
        self.create_table_with_id(id.clone(), name, rules, false);
        id
    }

    pub fn create_table_with_id(
        self: &Arc<Self>,
        id: TableId,
        name: String,
        rules: RuleConfig,
        persistent: bool,
    ) {
        let handle = table::spawn(id.clone(), name.clone(), rules, self.clone(), persistent);
        self.tables.lock().unwrap().insert(id.clone(), handle);
        self.summaries.lock().unwrap().insert(
            id.clone(),
            TableSummary {
                id,
                name,
                humans: 0,
                ais: 0,
                open_seats: 4,
                spectators: 0,
                in_game: false,
            },
        );
        self.broadcast_lobby();
    }

    fn fresh_code(&self) -> TableId {
        let mut x = self.next_code.fetch_add(1, Ordering::Relaxed)
            ^ std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_nanos() as u64)
                .unwrap_or(0);
        // Mix so consecutive counters don't share a prefix.
        x = x.wrapping_mul(0x9E37_79B9_7F4A_7C15);
        let mut code = String::with_capacity(4);
        for _ in 0..4 {
            code.push(CODE_CHARS[(x % CODE_CHARS.len() as u64) as usize] as char);
            x /= CODE_CHARS.len() as u64;
        }
        code
    }

    pub fn table(&self, id: &str) -> Option<mpsc::Sender<TableCmd>> {
        self.tables.lock().unwrap().get(id).cloned()
    }

    /// Called by a table actor as it shuts down.
    pub fn remove_table(&self, id: &TableId) {
        self.tables.lock().unwrap().remove(id);
        self.summaries.lock().unwrap().remove(id);
        self.seat_index.lock().unwrap().retain(|_, t| t != id);
        self.broadcast_lobby();
    }

    pub fn summaries(&self) -> Vec<TableSummary> {
        let mut list: Vec<_> = self.summaries.lock().unwrap().values().cloned().collect();
        list.sort_by(|a, b| a.name.cmp(&b.name).then_with(|| a.id.cmp(&b.id)));
        list
    }

    pub fn update_summary(&self, summary: TableSummary) {
        self.summaries.lock().unwrap().insert(summary.id.clone(), summary);
        self.broadcast_lobby();
    }

    pub fn add_watcher(&self, conn: ConnId, tx: mpsc::Sender<ServerMsg>) {
        self.watchers.lock().unwrap().insert(conn, tx);
    }

    pub fn remove_watcher(&self, conn: ConnId) {
        self.watchers.lock().unwrap().remove(&conn);
    }

    fn broadcast_lobby(&self) {
        let tables = self.summaries();
        for tx in self.watchers.lock().unwrap().values() {
            let _ = tx.try_send(ServerMsg::LobbyState { tables: tables.clone() });
        }
    }

    pub fn set_seat(&self, player: PlayerId, table: TableId) {
        self.seat_index.lock().unwrap().insert(player, table);
    }

    pub fn clear_seat(&self, player: &PlayerId) {
        self.seat_index.lock().unwrap().remove(player);
    }

    pub fn seat_table(&self, player: &PlayerId) -> Option<TableId> {
        self.seat_index.lock().unwrap().get(player).cloned()
    }
}

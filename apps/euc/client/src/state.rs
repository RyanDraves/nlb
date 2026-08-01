//! Client-side signals, written by the WebSocket callbacks and read by the UI.

use std::cell::Cell;

use euc_shared::{Phase, PlayerId, Role, Seat, ServerMsg, Suit, TableId, TableSummary, TableView};
use leptos::prelude::*;

pub fn storage_get(key: &str) -> Option<String> {
    web_sys::window()?.local_storage().ok()??.get_item(key).ok()?
}

pub fn storage_set(key: &str, value: &str) {
    if let Some(Ok(Some(storage))) = web_sys::window().map(|w| w.local_storage()) {
        let _ = storage.set_item(key, value);
    }
}

/// Seated players can collapse to a cards-only view ("hand mode") when a
/// table-mode tablet is showing the shared state in the middle of the table.
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum ViewMode {
    Full,
    HandOnly,
}

/// A short-lived "Pass" / "Calls ♥" flash next to whoever just bid, derived
/// by diffing consecutive table views (the wire carries state, not events).
#[derive(Clone, PartialEq)]
pub struct BidToast {
    pub seat: Seat,
    pub text: String,
    nonce: u64,
}

thread_local! {
    static TOAST_NONCE: Cell<u64> = const { Cell::new(0) };
}

fn glyph(suit: Suit) -> &'static str {
    match suit {
        Suit::Clubs => "♣",
        Suit::Diamonds => "♦",
        Suit::Hearts => "♥",
        Suit::Spades => "♠",
    }
}

/// What did the player whose turn just ended do?
fn bid_toast_diff(old: Option<&TableView>, new: &TableView) -> Option<(Seat, String)> {
    let og = old.filter(|o| o.table_id == new.table_id)?.game.as_ref()?;
    let ng = new.game.as_ref()?;
    let alone = if ng.alone { " — alone!" } else { "" };
    match (&og.phase, &ng.phase) {
        (Phase::Bidding1 { turn }, Phase::Bidding1 { turn: next }) if turn != next => {
            Some((*turn, "Pass".into()))
        }
        (Phase::Bidding1 { turn }, Phase::Bidding2 { .. }) => Some((*turn, "Pass".into())),
        (Phase::Bidding1 { turn }, Phase::DealerDiscard | Phase::Playing { .. }) => {
            let maker = ng.maker.unwrap_or(*turn);
            Some((maker, format!("Ordered up!{alone}")))
        }
        (Phase::Bidding2 { turn }, Phase::Bidding2 { turn: next }) if turn != next => {
            Some((*turn, "Pass".into()))
        }
        // Dealer passed too: throw-in, fresh deal.
        (Phase::Bidding2 { turn }, Phase::Bidding1 { .. }) => Some((*turn, "Pass".into())),
        (Phase::Bidding2 { turn }, Phase::Playing { .. }) => {
            let maker = ng.maker.unwrap_or(*turn);
            let trump = ng.trump.map(glyph).unwrap_or("");
            Some((maker, format!("Calls {trump}{alone}")))
        }
        _ => None,
    }
}

#[derive(Clone, Copy)]
pub struct AppState {
    pub connected: RwSignal<bool>,
    pub player_id: RwSignal<Option<PlayerId>>,
    pub name: RwSignal<String>,
    pub tables: RwSignal<Vec<TableSummary>>,
    pub table: RwSignal<Option<TableView>>,
    pub error: RwSignal<Option<String>>,
    pub mode: RwSignal<ViewMode>,
    pub bid_toast: RwSignal<Option<BidToast>>,
    /// Set from ?table=&mode= URL params; consumed on the first Welcome so a
    /// bookmarked tablet lands straight on its table.
    pub auto_join: RwSignal<Option<(TableId, Role)>>,
}

fn url_params() -> Option<(Option<String>, Option<String>)> {
    let search = web_sys::window()?.location().search().ok()?;
    let params = web_sys::UrlSearchParams::new_with_str(&search).ok()?;
    Some((params.get("table"), params.get("mode")))
}

/// Reflect the current table (or lack of one) in the address bar so refresh
/// and bookmarks return to the same place.
pub fn sync_url(table: Option<&TableId>, table_display: bool) {
    let Some(window) = web_sys::window() else { return };
    let query = match (table, table_display) {
        (Some(id), true) => format!("?table={id}&mode=table"),
        (Some(id), false) => format!("?table={id}"),
        (None, _) => String::new(),
    };
    let url = format!("/{query}");
    if let Ok(history) = window.history() {
        let _ = history.replace_state_with_url(&wasm_bindgen::JsValue::NULL, "", Some(&url));
    }
}

impl AppState {
    pub fn new() -> Self {
        let (table_param, mode_param) = url_params().unwrap_or((None, None));
        let mode_param = mode_param.as_deref();
        let auto_join = table_param.map(|id| {
            let role = if mode_param == Some("table") {
                Role::TableDisplay
            } else {
                Role::Spectator
            };
            (id.to_uppercase(), role)
        });
        let mode = if mode_param == Some("hand") || storage_get("euc_mode").as_deref() == Some("hand")
        {
            ViewMode::HandOnly
        } else {
            ViewMode::Full
        };
        Self {
            connected: RwSignal::new(false),
            player_id: RwSignal::new(None),
            name: RwSignal::new(storage_get("euc_name").unwrap_or_default()),
            tables: RwSignal::new(Vec::new()),
            table: RwSignal::new(None),
            error: RwSignal::new(None),
            mode: RwSignal::new(mode),
            bid_toast: RwSignal::new(None),
            auto_join: RwSignal::new(auto_join),
        }
    }

    pub fn apply(&self, msg: ServerMsg) {
        match msg {
            ServerMsg::Welcome { player_id, name } => {
                storage_set("euc_player", &player_id);
                self.player_id.set(Some(player_id));
                if self.name.get_untracked().is_empty() {
                    self.name.set(name);
                }
                if let Some((table_id, role)) = self.auto_join.get_untracked() {
                    self.auto_join.set(None);
                    crate::net::send(&euc_shared::ClientMsg::JoinTable { table_id, role });
                }
            }
            ServerMsg::LobbyState { tables } => self.tables.set(tables),
            ServerMsg::TableState { view } => {
                if let Some((seat, text)) =
                    bid_toast_diff(self.table.get_untracked().as_ref(), &view)
                {
                    let nonce = TOAST_NONCE.with(|n| {
                        n.set(n.get() + 1);
                        n.get()
                    });
                    self.bid_toast.set(Some(BidToast { seat, text, nonce }));
                    let toast = self.bid_toast;
                    crate::net::set_timeout(950, move || {
                        // Only clear our own toast; a newer one owns the slot.
                        if toast.get_untracked().is_some_and(|t| t.nonce == nonce) {
                            toast.set(None);
                        }
                    });
                }
                self.table.set(Some(view));
            }
            ServerMsg::Joined { table_id, role } => {
                sync_url(Some(&table_id), matches!(role, Role::TableDisplay));
            }
            ServerMsg::LeftTable => {
                self.table.set(None);
                sync_url(None, false);
            }
            ServerMsg::Error { message, .. } => {
                let error = self.error;
                error.set(Some(message));
                crate::net::set_timeout(4000, move || error.set(None));
            }
            ServerMsg::Pong => {}
        }
    }
}

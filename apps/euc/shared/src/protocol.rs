//! JSON wire protocol: one serde_json text frame per WebSocket message.
//! Everything is internally tagged with `"type"` in snake_case so non-Rust
//! bots (Python etc.) get predictable shapes. Encoding is the caller's job to
//! keep this crate dependency-light. Documented for bots in apps/euc/PROTOCOL.md.

use serde::{Deserialize, Serialize};

use crate::game::{Action, Seat};
use crate::rules::RuleConfig;
use crate::view::{Role, TableView};

/// Short human-shareable table code (also used in URLs).
pub type TableId = String;

/// Stable player identity minted at login and carried in the auth token, so a
/// reconnect (page refresh) reclaims the same seat. Hex string.
pub type PlayerId = String;

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum ClientMsg {
    /// First message after connecting; sets/confirms the display name.
    Hello { name: String },
    SetName { name: String },
    CreateTable {
        name: String,
        #[serde(default)]
        rules: RuleConfig,
    },
    JoinTable { table_id: TableId, role: Role },
    /// Move to (or take) a seat at the current table.
    TakeSeat { seat: Seat },
    /// Leave your seat but stay watching.
    StandUp,
    LeaveTable,
    AddAi { seat: Seat },
    RemoveAi { seat: Seat },
    /// Change table rules; only while no game is running.
    SetRules { rules: RuleConfig },
    StartGame,
    /// A game action: bid, discard, play a card, continue. Must be one of the
    /// actions in your latest `TableView.legal`.
    Act { action: Action },
    Ping,
}

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq)]
pub struct TableSummary {
    pub id: TableId,
    pub name: String,
    pub humans: u8,
    pub ais: u8,
    pub open_seats: u8,
    pub spectators: u8,
    pub in_game: bool,
}

#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ErrorCode {
    NotYourTurn,
    IllegalAction,
    NoSuchTable,
    SeatTaken,
    NotAtTable,
    AlreadyAtTable,
    BadRequest,
}

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum ServerMsg {
    /// Sent once on connect; echoes the identity from the auth token.
    Welcome { player_id: PlayerId, name: String },
    /// Full lobby listing; sent on join and whenever it changes.
    LobbyState { tables: Vec<TableSummary> },
    Joined { table_id: TableId, role: Role },
    /// Your redacted view of the table; resent in full on every change.
    TableState { view: TableView },
    LeftTable,
    Error { code: ErrorCode, message: String },
    Pong,
}

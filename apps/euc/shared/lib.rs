//! Shared, deterministic Euchre rules engine + wire protocol.
//!
//! Pure logic with no I/O, so it compiles identically for the native server,
//! the wasm browser client, and any native bot. The server is authoritative:
//! it owns an [`EuchreGame`] and advances it with [`EuchreGame::apply`], then
//! sends each connection its own redacted [`TableView`] via [`redact`].
//! Message encoding (serde_json) is the caller's job so this crate depends
//! only on serde (plus the first-party `lrb_rng`).

mod ai;
mod cards;
mod game;
mod legal;
mod protocol;
mod rules;
mod score;
mod view;

#[cfg(test)]
mod tests;

pub use ai::{Bot, HeuristicBot, RandomBot};
pub use cards::{deck24, effective_suit, trick_power, Card, Rank, Suit};
pub use game::{Action, EuchreGame, HandSummary, Phase, RuleError, Seat};
pub use protocol::{ClientMsg, ErrorCode, PlayerId, ServerMsg, TableId, TableSummary};
pub use rules::RuleConfig;
pub use score::hand_points;
pub use view::{redact, GameView, Role, SeatInfo, TableMeta, TableView};

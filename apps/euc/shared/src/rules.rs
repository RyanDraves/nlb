//! Per-table rule options. Kept as a struct so future variants (defend alone,
//! farmer's hand, no-trump calls, ...) slot in without protocol breaks —
//! `#[serde(default)]` lets old clients omit new fields.

use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq)]
#[serde(default)]
pub struct RuleConfig {
    /// If everyone passes twice, the dealer must call trump (no redeal).
    pub stick_the_dealer: bool,
    /// First team to reach this score wins. Standard is 10.
    pub win_score: u8,
}

impl Default for RuleConfig {
    fn default() -> Self {
        Self {
            stick_the_dealer: false,
            win_score: 10,
        }
    }
}

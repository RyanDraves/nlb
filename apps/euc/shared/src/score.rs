//! Hand scoring: who gets how many points once all five tricks are played.

use crate::game::Seat;

/// Returns `(scoring_team, points, euchred)`.
///
/// Makers take 3-4 tricks: 1 point. All five (a march): 2, or 4 alone.
/// Fewer than 3: euchred — defenders score 2.
pub fn hand_points(maker: Seat, tricks: [u8; 2], alone: bool) -> (u8, u8, bool) {
    let maker_team = maker.team();
    let taken = tricks[maker_team];
    if taken >= 3 {
        let points = if taken == 5 {
            if alone {
                4
            } else {
                2
            }
        } else {
            1
        };
        (maker_team as u8, points, false)
    } else {
        ((1 - maker_team) as u8, 2, true)
    }
}

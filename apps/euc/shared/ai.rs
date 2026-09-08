//! Built-in bots. They consume the same redacted [`TableView`] a human client
//! or external bot receives — no privileged state, so they cannot cheat — and
//! only ever return an element of `view.legal`.

use crate::cards::{effective_suit, trick_power, Card, Rank, Suit};
use crate::game::{Action, Phase, Seat};
use crate::view::TableView;

pub trait Bot {
    /// Pick one of `view.legal`. Only called when that list is non-empty.
    fn choose(&mut self, view: &TableView) -> Action;
}

/// Uniformly random legal play; used as the rules-engine fuzzer in tests.
pub struct RandomBot {
    pub rng: lrb_rng::Rng,
}

impl Bot for RandomBot {
    fn choose(&mut self, view: &TableView) -> Action {
        view.legal[self.rng.gen_range(view.legal.len())]
    }
}

/// Straightforward heuristic player: counts hand strength to bid, and plays
/// tricks with standard rules of thumb (dump when partner is winning, win as
/// cheaply as possible, save trump).
pub struct HeuristicBot;

/// Worth of a card under a candidate trump, used for both bidding totals and
/// "cheapest card" comparisons.
fn weight(card: Card, trump: Suit) -> u8 {
    if effective_suit(card, trump) == trump {
        if card.rank == Rank::Jack {
            if card.suit == trump {
                30 // right bower
            } else {
                27 // left bower
            }
        } else {
            match card.rank {
                Rank::Ace => 22,
                Rank::King => 20,
                Rank::Queen => 18,
                Rank::Ten => 16,
                _ => 15,
            }
        }
    } else if card.rank == Rank::Ace {
        8
    } else {
        0
    }
}

fn hand_strength(hand: &[Card], trump: Suit) -> u32 {
    hand.iter().map(|&c| weight(c, trump) as u32).sum()
}

const CALL_THRESHOLD: u32 = 50;
const ALONE_THRESHOLD: u32 = 90;

impl Bot for HeuristicBot {
    fn choose(&mut self, view: &TableView) -> Action {
        if view.legal.len() == 1 {
            return view.legal[0];
        }
        let game = view.game.as_ref().expect("legal actions imply a game");
        let me = view.you.expect("bots are always seated");

        match &game.phase {
            Phase::Bidding1 { .. } => {
                let upsuit = game.upcard.expect("upcard in round 1").suit;
                let mut strength = hand_strength(&game.hand, upsuit);
                // The dealer gets the upcard: a boon for their team, a threat
                // otherwise.
                if game.dealer.team() == me.team() {
                    strength += 6;
                } else {
                    strength = strength.saturating_sub(4);
                }
                if strength >= ALONE_THRESHOLD {
                    Action::OrderUp { alone: true }
                } else if strength >= CALL_THRESHOLD {
                    Action::OrderUp { alone: false }
                } else {
                    Action::Pass
                }
            }
            Phase::Bidding2 { .. } => {
                let may_pass = view.legal.contains(&Action::Pass);
                let callable: Vec<Suit> = view
                    .legal
                    .iter()
                    .filter_map(|a| match a {
                        Action::Call { suit, alone: false } => Some(*suit),
                        _ => None,
                    })
                    .collect();
                let (best, strength) = callable
                    .into_iter()
                    .map(|s| (s, hand_strength(&game.hand, s)))
                    .max_by_key(|&(_, str_)| str_)
                    .expect("round 2 always has callable suits");
                if strength >= ALONE_THRESHOLD {
                    Action::Call { suit: best, alone: true }
                } else if strength >= CALL_THRESHOLD || !may_pass {
                    Action::Call { suit: best, alone: false }
                } else {
                    Action::Pass
                }
            }
            Phase::DealerDiscard => {
                let trump = game.trump.expect("trump set at discard");
                let card = *game
                    .hand
                    .iter()
                    .min_by_key(|&&c| (weight(c, trump), c.rank))
                    .expect("dealer holds cards");
                Action::Discard { card }
            }
            Phase::Playing { .. } => Action::Play { card: self.pick_card(view, me) },
            // HandDone has only Continue, handled by the len()==1 fast path;
            // GameOver never produces legal actions.
            _ => view.legal[0],
        }
    }
}

impl HeuristicBot {
    fn pick_card(&self, view: &TableView, me: Seat) -> Card {
        let game = view.game.as_ref().expect("in game");
        let trump = game.trump.expect("trump set while playing");
        let cards: Vec<Card> = view
            .legal
            .iter()
            .filter_map(|a| match a {
                Action::Play { card } => Some(*card),
                _ => None,
            })
            .collect();
        let cheapest = |cs: &[Card]| -> Card {
            *cs.iter()
                .min_by_key(|&&c| (weight(c, trump), c.rank))
                .expect("non-empty")
        };

        if game.current_trick.is_empty() {
            // Leading: press with a bower, cash an off-suit ace, else duck low.
            if let Some(&bower) = cards
                .iter()
                .find(|&&c| trick_power(c, trump, trump) >= 39)
            {
                return bower;
            }
            if let Some(&ace) = cards
                .iter()
                .find(|&&c| c.rank == Rank::Ace && effective_suit(c, trump) != trump)
            {
                return ace;
            }
            return cheapest(&cards);
        }

        let led = effective_suit(game.current_trick[0].1, trump);
        let (win_seat, win_power) = game
            .current_trick
            .iter()
            .map(|&(s, c)| (s, trick_power(c, trump, led)))
            .max_by_key(|&(_, p)| p)
            .expect("non-empty trick");
        if win_seat == me.partner() {
            return cheapest(&cards);
        }
        let winners: Vec<Card> = cards
            .iter()
            .copied()
            .filter(|&c| trick_power(c, trump, led) > win_power)
            .collect();
        if winners.is_empty() {
            cheapest(&cards)
        } else {
            cheapest(&winners)
        }
    }
}

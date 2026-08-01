//! Legal-move computation. This is the single source of truth for what a seat
//! may do: the server validates against it, the client enables UI from it, and
//! bots pick from it verbatim.

use crate::cards::effective_suit;
use crate::game::{Action, EuchreGame, Phase, Seat};
use crate::Suit;

impl EuchreGame {
    /// Every action `seat` may take right now. Empty when it's not their move.
    pub fn legal_actions(&self, seat: Seat) -> Vec<Action> {
        match &self.phase {
            Phase::Bidding1 { turn } if *turn == seat => vec![
                Action::Pass,
                Action::OrderUp { alone: false },
                Action::OrderUp { alone: true },
            ],
            Phase::Bidding2 { turn } if *turn == seat => {
                let turned_down = self.turned_down.expect("turned-down card in round 2").suit;
                let mut actions = Vec::new();
                // Stick the dealer: a stuck dealer must call — no Pass.
                if !(self.rules.stick_the_dealer && seat == self.dealer) {
                    actions.push(Action::Pass);
                }
                for suit in Suit::ALL {
                    if suit != turned_down {
                        actions.push(Action::Call { suit, alone: false });
                        actions.push(Action::Call { suit, alone: true });
                    }
                }
                actions
            }
            Phase::DealerDiscard if seat == self.dealer => self
                .hand(seat)
                .iter()
                .map(|&card| Action::Discard { card })
                .collect(),
            Phase::Playing { turn } if *turn == seat => {
                let hand = self.hand(seat);
                let playable: Vec<_> = match self.current_trick.first() {
                    None => hand.to_vec(),
                    Some(&(_, led_card)) => {
                        let trump = self.trump.expect("trump set while playing");
                        let led = effective_suit(led_card, trump);
                        let follow: Vec<_> = hand
                            .iter()
                            .copied()
                            .filter(|&c| effective_suit(c, trump) == led)
                            .collect();
                        if follow.is_empty() {
                            hand.to_vec()
                        } else {
                            follow
                        }
                    }
                };
                playable.into_iter().map(|card| Action::Play { card }).collect()
            }
            // Any seat may collect the trick / advance past the hand summary
            // (the server does both on a timer).
            Phase::TrickDone { .. } | Phase::HandDone { .. } => vec![Action::Continue],
            _ => Vec::new(),
        }
    }
}

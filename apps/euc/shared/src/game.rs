//! The authoritative Euchre state machine. Pure and deterministic: the only
//! entropy is the seeded RNG handed to [`EuchreGame::new`], so full games are
//! reproducible in tests. Never serialized wholesale — clients only ever see
//! the redacted [`crate::TableView`].

use serde::{Deserialize, Serialize};

use crate::cards::{deck24, effective_suit, trick_power, Card, Suit};
use crate::rules::RuleConfig;
use crate::score::hand_points;

/// One of the four positions at the table, counted clockwise. Seats 0 & 2 are
/// team 0, seats 1 & 3 are team 1.
#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct Seat(pub u8);

impl Seat {
    pub const ALL: [Seat; 4] = [Seat(0), Seat(1), Seat(2), Seat(3)];

    pub fn next(self) -> Seat {
        Seat((self.0 + 1) % 4)
    }

    pub fn partner(self) -> Seat {
        Seat((self.0 + 2) % 4)
    }

    pub fn team(self) -> usize {
        (self.0 % 2) as usize
    }

    pub fn index(self) -> usize {
        self.0 as usize
    }
}

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Phase {
    /// Bid on the upcard: order it up (dealer takes it) or pass.
    Bidding1 { turn: Seat },
    /// Upcard turned down; call any other suit or pass.
    Bidding2 { turn: Seat },
    /// Dealer took the upcard and must discard back to five.
    DealerDiscard,
    Playing { turn: Seat },
    /// The finished trick lies face-up until collected (`Continue`, which the
    /// server issues on a timer), so its last card is actually seen.
    TrickDone { winner: Seat },
    /// Hand scored; shown until someone continues to the next deal.
    HandDone { summary: HandSummary },
    GameOver { winner: u8 },
}

#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq)]
pub struct HandSummary {
    pub maker: Seat,
    pub trump: Suit,
    pub alone: bool,
    /// Tricks taken per team.
    pub tricks: [u8; 2],
    /// Which team scored and how much.
    pub scoring_team: u8,
    pub points: u8,
    pub euchred: bool,
}

/// Everything a player can do. The server validates every action against
/// [`EuchreGame::legal_actions`], and the same list is sent to clients (in
/// `TableView::legal`) so UIs and bots never reimplement the rules.
#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Action {
    Pass,
    /// Round 1: tell the dealer to pick up the upcard; its suit becomes trump.
    OrderUp { alone: bool },
    /// Round 2: name any suit except the turned-down one.
    Call { suit: Suit, alone: bool },
    /// Dealer only, after picking up the upcard.
    Discard { card: Card },
    Play { card: Card },
    /// Acknowledge a finished hand and deal the next one.
    Continue,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum RuleError {
    /// The seat has no legal actions right now.
    NotYourTurn,
    /// The action is not in the seat's legal list.
    IllegalAction,
}

pub struct EuchreGame {
    pub rules: RuleConfig,
    pub dealer: Seat,
    pub phase: Phase,
    pub(crate) hands: [Vec<Card>; 4],
    pub(crate) kitty: Vec<Card>,
    pub upcard: Option<Card>,
    /// The rejected upcard, face-visible history during round 2.
    pub turned_down: Option<Card>,
    pub trump: Option<Suit>,
    pub maker: Option<Seat>,
    pub alone: bool,
    pub current_trick: Vec<(Seat, Card)>,
    pub last_trick: Option<Vec<(Seat, Card)>>,
    /// Tricks taken this hand, per team.
    pub tricks_won: [u8; 2],
    /// Tricks taken this hand, per seat (who actually won each one).
    pub tricks_by_seat: [u8; 4],
    pub scores: [u8; 2],
    pub(crate) rng: lrb_rng::Rng,
}

impl EuchreGame {
    pub fn new(rules: RuleConfig, seed: u64) -> Self {
        let mut rng = lrb_rng::Rng::from_seed(seed);
        let dealer = Seat(rng.gen_range(4) as u8);
        let mut game = Self {
            rules,
            dealer,
            phase: Phase::Bidding1 { turn: dealer.next() },
            hands: Default::default(),
            kitty: Vec::new(),
            upcard: None,
            turned_down: None,
            trump: None,
            maker: None,
            alone: false,
            current_trick: Vec::new(),
            last_trick: None,
            tricks_won: [0, 0],
            tricks_by_seat: [0; 4],
            scores: [0, 0],
            rng,
        };
        game.deal();
        game
    }

    /// Shuffle and deal a fresh hand; resets all within-hand state.
    fn deal(&mut self) {
        let mut deck = deck24();
        self.rng.shuffle(&mut deck);
        for seat in Seat::ALL {
            self.hands[seat.index()] = deck.split_off(deck.len() - 5);
        }
        self.upcard = deck.pop();
        self.kitty = deck; // 3 buried cards
        self.turned_down = None;
        self.trump = None;
        self.maker = None;
        self.alone = false;
        self.current_trick.clear();
        self.last_trick = None;
        self.tricks_won = [0, 0];
        self.tricks_by_seat = [0; 4];
        self.phase = Phase::Bidding1 { turn: self.dealer.next() };
    }

    pub fn hand(&self, seat: Seat) -> &[Card] {
        &self.hands[seat.index()]
    }

    /// The maker's partner, when the maker plays alone.
    pub fn sitting_out(&self) -> Option<Seat> {
        if self.alone {
            self.maker.map(Seat::partner)
        } else {
            None
        }
    }

    /// The seat expected to act, if the phase has a single actor.
    /// `HandDone` accepts `Continue` from any seat and reports seat 0.
    pub fn turn_seat(&self) -> Option<Seat> {
        match &self.phase {
            Phase::Bidding1 { turn } | Phase::Bidding2 { turn } | Phase::Playing { turn } => {
                Some(*turn)
            }
            Phase::DealerDiscard => Some(self.dealer),
            Phase::TrickDone { .. } | Phase::HandDone { .. } => Some(Seat(0)),
            Phase::GameOver { .. } => None,
        }
    }

    fn next_active(&self, seat: Seat) -> Seat {
        let next = seat.next();
        if self.sitting_out() == Some(next) {
            next.next()
        } else {
            next
        }
    }

    fn first_leader(&self) -> Seat {
        let lead = self.dealer.next();
        if self.sitting_out() == Some(lead) {
            lead.next()
        } else {
            lead
        }
    }

    fn trick_size(&self) -> usize {
        if self.alone {
            3
        } else {
            4
        }
    }

    /// Validate and apply one action. On success the phase has advanced (this
    /// may include dealing the next hand or ending the game).
    pub fn apply(&mut self, seat: Seat, action: Action) -> Result<(), RuleError> {
        let legal = self.legal_actions(seat);
        if legal.is_empty() {
            return Err(RuleError::NotYourTurn);
        }
        if !legal.contains(&action) {
            return Err(RuleError::IllegalAction);
        }

        match (self.phase.clone(), action) {
            (Phase::Bidding1 { turn }, Action::Pass) => {
                if turn == self.dealer {
                    // Everyone passed on the upcard; flip it and open bidding.
                    self.turned_down = self.upcard.take();
                    self.phase = Phase::Bidding2 { turn: self.dealer.next() };
                } else {
                    self.phase = Phase::Bidding1 { turn: turn.next() };
                }
            }
            (Phase::Bidding1 { .. }, Action::OrderUp { alone }) => {
                let upcard = self.upcard.take().expect("upcard present in round 1");
                self.trump = Some(upcard.suit);
                self.maker = Some(seat);
                self.alone = alone;
                self.hands[self.dealer.index()].push(upcard);
                if self.sitting_out() == Some(self.dealer) {
                    // Dealer's partner went alone: the dealer's hand is dead,
                    // so the pickup/discard exchange is moot — skip it.
                    self.phase = Phase::Playing { turn: self.first_leader() };
                } else {
                    self.phase = Phase::DealerDiscard;
                }
            }
            (Phase::DealerDiscard, Action::Discard { card }) => {
                let hand = &mut self.hands[self.dealer.index()];
                let i = hand.iter().position(|&c| c == card).expect("legal discard");
                self.kitty.push(hand.remove(i));
                self.phase = Phase::Playing { turn: self.first_leader() };
            }
            (Phase::Bidding2 { turn }, Action::Pass) => {
                if turn == self.dealer {
                    // Thrown in (stick-the-dealer forbids this path): redeal.
                    self.dealer = self.dealer.next();
                    self.deal();
                } else {
                    self.phase = Phase::Bidding2 { turn: turn.next() };
                }
            }
            (Phase::Bidding2 { .. }, Action::Call { suit, alone }) => {
                self.trump = Some(suit);
                self.maker = Some(seat);
                self.alone = alone;
                self.phase = Phase::Playing { turn: self.first_leader() };
            }
            (Phase::Playing { turn }, Action::Play { card }) => {
                let hand = &mut self.hands[turn.index()];
                let i = hand.iter().position(|&c| c == card).expect("legal play");
                hand.remove(i);
                self.current_trick.push((turn, card));
                if self.current_trick.len() == self.trick_size() {
                    self.finish_trick();
                } else {
                    self.phase = Phase::Playing { turn: self.next_active(turn) };
                }
            }
            (Phase::TrickDone { winner }, Action::Continue) => {
                self.last_trick = Some(std::mem::take(&mut self.current_trick));
                if self.tricks_won[0] + self.tricks_won[1] == 5 {
                    self.finish_hand();
                } else {
                    self.phase = Phase::Playing { turn: winner };
                }
            }
            (Phase::HandDone { .. }, Action::Continue) => {
                self.dealer = self.dealer.next();
                self.deal();
            }
            _ => unreachable!("legal_actions only returns phase-consistent actions"),
        }
        Ok(())
    }

    fn finish_trick(&mut self) {
        let trump = self.trump.expect("trump set while playing");
        let led = effective_suit(self.current_trick[0].1, trump);
        let (winner, _) = *self
            .current_trick
            .iter()
            .max_by_key(|(_, card)| trick_power(*card, trump, led))
            .expect("non-empty trick");
        self.tricks_won[winner.team()] += 1;
        self.tricks_by_seat[winner.index()] += 1;
        // The trick stays on the table (TrickDone) until collected.
        self.phase = Phase::TrickDone { winner };
    }

    fn finish_hand(&mut self) {
        let maker = self.maker.expect("maker set while playing");
        let (scoring_team, points, euchred) = hand_points(maker, self.tricks_won, self.alone);
        self.scores[scoring_team as usize] += points;
        let summary = HandSummary {
            maker,
            trump: self.trump.expect("trump set"),
            alone: self.alone,
            tricks: self.tricks_won,
            scoring_team,
            points,
            euchred,
        };
        if self.scores[scoring_team as usize] >= self.rules.win_score {
            self.phase = Phase::GameOver { winner: scoring_team };
        } else {
            self.phase = Phase::HandDone { summary };
        }
    }
}

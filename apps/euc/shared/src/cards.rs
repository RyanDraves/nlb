//! The 24-card Euchre deck and trump-aware card comparisons.

use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq, Hash)]
#[serde(rename_all = "snake_case")]
pub enum Suit {
    Clubs,
    Diamonds,
    Hearts,
    Spades,
}

impl Suit {
    pub const ALL: [Suit; 4] = [Suit::Clubs, Suit::Diamonds, Suit::Hearts, Suit::Spades];

    /// The other suit of the same color: clubs<->spades, diamonds<->hearts.
    /// The Jack of this suit is the left bower when `self` is trump.
    pub fn same_color(self) -> Suit {
        match self {
            Suit::Clubs => Suit::Spades,
            Suit::Spades => Suit::Clubs,
            Suit::Diamonds => Suit::Hearts,
            Suit::Hearts => Suit::Diamonds,
        }
    }

    pub fn is_red(self) -> bool {
        matches!(self, Suit::Diamonds | Suit::Hearts)
    }
}

#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[serde(rename_all = "snake_case")]
pub enum Rank {
    Nine,
    Ten,
    Jack,
    Queen,
    King,
    Ace,
}

impl Rank {
    pub const ALL: [Rank; 6] = [
        Rank::Nine,
        Rank::Ten,
        Rank::Jack,
        Rank::Queen,
        Rank::King,
        Rank::Ace,
    ];
}

#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct Card {
    pub suit: Suit,
    pub rank: Rank,
}

pub fn deck24() -> Vec<Card> {
    let mut deck = Vec::with_capacity(24);
    for suit in Suit::ALL {
        for rank in Rank::ALL {
            deck.push(Card { suit, rank });
        }
    }
    deck
}

/// The suit a card counts as under `trump`: the left bower (Jack of trump's
/// color-mate) is trump for every purpose, including following suit.
pub fn effective_suit(card: Card, trump: Suit) -> Suit {
    if card.rank == Rank::Jack && card.suit == trump.same_color() {
        trump
    } else {
        card.suit
    }
}

/// Strength of `card` in a trick where `led` is the *effective* suit of the
/// led card. Higher wins; off-suit non-trump cards are 0 and can never win
/// (the led card itself always has power > 0).
pub fn trick_power(card: Card, trump: Suit, led: Suit) -> u8 {
    let eff = effective_suit(card, trump);
    if eff == trump {
        if card.rank == Rank::Jack {
            if card.suit == trump {
                40 // right bower
            } else {
                39 // left bower
            }
        } else {
            30 + card.rank as u8
        }
    } else if eff == led {
        10 + card.rank as u8
    } else {
        0
    }
}

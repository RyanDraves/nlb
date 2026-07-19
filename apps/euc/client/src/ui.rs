//! UI components. The table screen is re-rendered wholesale from each
//! `TableView` snapshot — a Euchre table changes state a few times a minute,
//! so fine-grained reactivity would buy nothing.
//!
//! Game state is communicated visually, mirroring a physical table: teams are
//! blue (seats 1&3) and red (seats 2&4), the kitty sits by the dealer with the
//! upcard on top, played cards enter the middle from their player's side of
//! the table (stacked in play order), and won tricks pile up as markers next
//! to whoever took them. The full player view and the table-mode display
//! share this "felt" layout; the full view just rotates it so you sit at the
//! bottom, with your hand below.

use euc_shared::{
    effective_suit, trick_power, Action, Card, ClientMsg, GameView, Phase, Role, Seat, Suit,
    TableView,
};
use leptos::prelude::*;

use crate::net;
use crate::state::{storage_set, AppState, ViewMode};

fn suit_glyph(suit: Suit) -> &'static str {
    match suit {
        Suit::Clubs => "♣",
        Suit::Diamonds => "♦",
        Suit::Hearts => "♥",
        Suit::Spades => "♠",
    }
}

fn rank_glyph(card: Card) -> &'static str {
    use euc_shared::Rank::*;
    match card.rank {
        Nine => "9",
        Ten => "10",
        Jack => "J",
        Queen => "Q",
        King => "K",
        Ace => "A",
    }
}

fn card_text(card: Card) -> String {
    format!("{}{}", rank_glyph(card), suit_glyph(card.suit))
}

fn action_label(action: &Action) -> String {
    match action {
        Action::Pass => "Pass".into(),
        Action::OrderUp { alone: false } => "Order it up".into(),
        Action::OrderUp { alone: true } => "Order up — alone".into(),
        Action::Call { suit, alone: false } => format!("Call {}", suit_glyph(*suit)),
        Action::Call { suit, alone: true } => format!("Call {} — alone", suit_glyph(*suit)),
        Action::Continue => "Next hand".into(),
        Action::Discard { card } => format!("Discard {}", card_text(*card)),
        Action::Play { card } => card_text(*card),
    }
}

fn team_class(seat: Seat) -> &'static str {
    if seat.team() == 0 {
        "team-blue"
    } else {
        "team-red"
    }
}

/// Display order for the player's hand: grouped by suit (alternating colors),
/// descending within each group. Once trump is called, effective trump — the
/// left bower included — moves to the left, bowers first.
fn sorted_hand(hand: &[Card], trump: Option<Suit>) -> Vec<Card> {
    const SUIT_ORDER: [Suit; 4] = [Suit::Spades, Suit::Hearts, Suit::Clubs, Suit::Diamonds];
    let suit_pos = |s: Suit| SUIT_ORDER.iter().position(|&o| o == s).unwrap() as u8;
    let mut cards = hand.to_vec();
    cards.sort_by_key(|&c| match trump {
        Some(t) => {
            let eff = effective_suit(c, t);
            let group = if eff == t { 0 } else { 1 + suit_pos(eff) };
            (group, 255 - trick_power(c, t, eff))
        }
        None => (suit_pos(c.suit), 255 - c.rank as u8),
    });
    cards
}

/// True only in the window right after a deal (round-one bidding, first
/// bidder yet to act) — the cue for the deal-in animations. Scoped this
/// narrowly so later re-renders don't replay them.
fn fresh_deal(game: &GameView) -> bool {
    matches!(&game.phase, Phase::Bidding1 { turn } if *turn == game.dealer.next())
}

fn phase_turn(game: &GameView) -> Option<Seat> {
    match &game.phase {
        Phase::Bidding1 { turn } | Phase::Bidding2 { turn } | Phase::Playing { turn } => Some(*turn),
        Phase::DealerDiscard => Some(game.dealer),
        _ => None,
    }
}

// ---------------------------------------------------------------- cards

/// A standard playing-card face: rank+suit index in the top-left and again,
/// rotated, in the bottom-right, so the card reads correctly from both sides
/// of a table. Large center pip.
#[component]
fn CardFace(card: Card, #[prop(optional)] small: bool) -> impl IntoView {
    view! {
        <span class="card face" class:red=card.suit.is_red() class:small=small>
            <span class="ci ci-tl">
                <span>{rank_glyph(card)}</span>
                <span>{suit_glyph(card.suit)}</span>
            </span>
            <span class="ci-center">{suit_glyph(card.suit)}</span>
            <span class="ci ci-br">
                <span>{rank_glyph(card)}</span>
                <span>{suit_glyph(card.suit)}</span>
            </span>
        </span>
    }
}

#[component]
fn CardBack(#[prop(optional)] mini: bool) -> impl IntoView {
    view! { <span class="card back" class:mini=mini></span> }
}

/// A stationary button (fixed hit area) whose card visual lifts on hover —
/// the hitbox never moves, so hovering at any edge cannot flicker.
#[component]
fn HandCard(card: Card, action: Option<Action>) -> impl IntoView {
    let playable = action.is_some();
    let click = move |_| {
        if let Some(action) = action {
            net::send(&ClientMsg::Act { action });
        }
    };
    view! {
        <button class="hand-card" class:playable=playable disabled=!playable on:click=click>
            <span class="card face" class:red=card.suit.is_red()>
                <span class="ci ci-tl">
                    <span>{rank_glyph(card)}</span>
                    <span>{suit_glyph(card.suit)}</span>
                </span>
                <span class="ci-center">{suit_glyph(card.suit)}</span>
                <span class="ci ci-br">
                    <span>{rank_glyph(card)}</span>
                    <span>{suit_glyph(card.suit)}</span>
                </span>
            </span>
        </button>
    }
}

// ---------------------------------------------------------------- app shell

#[component]
pub fn App() -> impl IntoView {
    let state = AppState::new();
    provide_context(state);
    net::connect(state);
    let is_display = move || {
        state
            .table
            .get()
            .map(|v| matches!(v.role, Role::TableDisplay))
            .unwrap_or(false)
    };
    view! {
        <div class="app" class:wide=is_display>
            <Header/>
            <ErrorBar/>
            <Main/>
        </div>
    }
}

#[component]
fn Header() -> impl IntoView {
    let state = expect_context::<AppState>();
    move || {
        // A tablet lying on the table is nobody's device: no name, no chrome.
        let display = state
            .table
            .get()
            .map(|v| matches!(v.role, Role::TableDisplay))
            .unwrap_or(false);
        (!display).then(|| {
            view! {
                <header>
                    <h1>"Euchre"</h1>
                    <span class="conn" class:ok=move || state.connected.get()>
                        {move || if state.connected.get() { "●" } else { "○ reconnecting…" }}
                    </span>
                    <input
                        class="name-input"
                        placeholder="Your name"
                        prop:value=move || state.name.get()
                        on:change=move |ev| {
                            let name = event_target_value(&ev);
                            state.name.set(name.clone());
                            storage_set("euc_name", &name);
                            net::send(&ClientMsg::SetName { name });
                        }
                    />
                </header>
            }
        })
    }
}

#[component]
fn ErrorBar() -> impl IntoView {
    let state = expect_context::<AppState>();
    move || {
        state
            .error
            .get()
            .map(|message| view! { <div class="error-bar">{message}</div> })
    }
}

#[component]
fn Main() -> impl IntoView {
    let state = expect_context::<AppState>();
    move || {
        if state.table.get().is_some() {
            view! { <TableUi/> }.into_any()
        } else {
            view! { <LobbyUi/> }.into_any()
        }
    }
}

#[component]
fn LobbyUi() -> impl IntoView {
    let state = expect_context::<AppState>();
    let new_name = RwSignal::new(String::new());
    let create = move |_| {
        let name = new_name.get_untracked();
        let name = if name.trim().is_empty() { "Table".to_string() } else { name };
        net::send(&ClientMsg::CreateTable { name, rules: Default::default() });
        new_name.set(String::new());
    };
    view! {
        <div class="lobby">
            <h2>"Tables"</h2>
            {move || {
                let tables = state.tables.get();
                if tables.is_empty() {
                    view! { <p class="muted">"No tables yet — create one below."</p> }.into_any()
                } else {
                    tables
                        .into_iter()
                        .map(|t| {
                            let join_id = t.id.clone();
                            let watch_id = t.id.clone();
                            let status = format!(
                                "{} seated ({} bot{}) · {} open · {} watching{}",
                                t.humans + t.ais,
                                t.ais,
                                if t.ais == 1 { "" } else { "s" },
                                t.open_seats,
                                t.spectators,
                                if t.in_game { " · game on" } else { "" },
                            );
                            view! {
                                <div class="table-row">
                                    <span class="table-name">{t.name.clone()}</span>
                                    <span class="table-id">{t.id.clone()}</span>
                                    <span class="muted">{status}</span>
                                    <button on:click=move |_| net::send(&ClientMsg::JoinTable {
                                        table_id: join_id.clone(),
                                        role: Role::Spectator,
                                    })>"Join"</button>
                                    <button class="ghost" on:click=move |_| net::send(&ClientMsg::JoinTable {
                                        table_id: watch_id.clone(),
                                        role: Role::TableDisplay,
                                    })>"Table display"</button>
                                </div>
                            }
                        })
                        .collect_view()
                        .into_any()
                }
            }}
            <div class="create-row">
                <input
                    placeholder="New table name"
                    prop:value=move || new_name.get()
                    on:input=move |ev| new_name.set(event_target_value(&ev))
                />
                <button on:click=create>"Create table"</button>
            </div>
        </div>
    }
}

// ---------------------------------------------------------------- the felt

/// The kitty on the felt in front of the dealer: buried cards face down, the
/// upcard face up on top while it's being bid on. Once the upcard is turned
/// down or picked-up-and-discarded, the dealer sweeps it off the table
/// (stage exit in their direction).
fn kitty_pool(game: &GameView, dealer_pos: usize) -> Option<impl IntoView> {
    let exiting = match &game.phase {
        Phase::Bidding1 { .. } | Phase::DealerDiscard => false,
        // Turned down: the pile leaves as round two opens.
        Phase::Bidding2 { turn } if *turn == game.dealer.next() => true,
        // Picked up + discarded (or a dead dealer hand): leaves at first lead.
        Phase::Playing { .. }
            if game.current_trick.is_empty()
                && game.tricks_won == [0, 0]
                && game.turned_down.is_none() =>
        {
            true
        }
        _ => return None,
    };
    let upcard = game.upcard.map(|c| view! { <CardFace card=c/> });
    Some(view! {
        <span class=format!("kitty kp-{dealer_pos}") class:exit=exiting class:enter=fresh_deal(game)>
            <span class="card back k0"></span>
            <span class="card back k1"></span>
            {upcard}
        </span>
    })
}

/// The shared table layout: seat plates around a central pool, everything
/// oriented so `anchor`'s seat is at the bottom. `interactive` adds the few
/// in-game controls a player (but not a wall tablet) should see.
fn felt(view: &TableView, game: &GameView, anchor: Seat, interactive: bool) -> impl IntoView {
    let pos_of = move |s: Seat| ((s.0 + 4 - anchor.0) % 4) as usize;
    let turn = phase_turn(game);
    let toast = expect_context::<AppState>().bid_toast.get();

    let plates = Seat::ALL
        .into_iter()
        .map(|seat| {
            let info = &view.seats[seat.index()];
            let pos = ["f-bottom", "f-left", "f-top", "f-right"][pos_of(seat)];
            let away = !info.connected;
            let name = info.name.clone().unwrap_or_else(|| "— open —".into());
            let dealer = game.dealer == seat;
            let maker = game.maker == Some(seat);
            let out = game.sitting_out == Some(seat);
            let backs = (0..game.hand_counts[seat.index()])
                .map(|_| view! { <CardBack mini=true/> })
                .collect_view();
            let taken = game.tricks_by_seat[seat.index()];
            let trick_count =
                (taken > 0).then(|| view! { <span class="trick-count">{taken}</span> });
            let replace_ai = (interactive && away && !info.is_ai && info.name.is_some()).then(|| {
                view! {
                    <button class="ghost tiny" on:click=move |_| net::send(&ClientMsg::AddAi { seat })>
                        "Replace with AI"
                    </button>
                }
            });
            let bid_flash = toast
                .as_ref()
                .filter(|t| t.seat == seat)
                .map(|t| view! { <div class="bid-toast">{t.text.clone()}</div> });
            view! {
                <div class=format!("plate {pos} {}", team_class(seat))
                    class:turn=turn == Some(seat) class:away=away class:you=view.you == Some(seat)>
                    <div class="plate-name">
                        {name}
                        {info.is_ai.then(|| view! { <span class="badge">"🤖"</span> })}
                        {dealer.then(|| view! { <span class="badge">"D"</span> })}
                        {maker.then(|| game.trump.map(|t| view! {
                            <span class="badge" class:red-suit=t.is_red()>{suit_glyph(t)}</span>
                        }))}
                        {out.then(|| view! { <span class="badge">"out"</span> })}
                        {trick_count}
                    </div>
                    <div class="plate-cards" class:dealing=fresh_deal(game)>{backs}</div>
                    {replace_ai}
                    {bid_flash}
                </div>
            }
        })
        .collect_view();

    let pool = match &game.phase {
        Phase::HandDone { summary } => {
            let chip = if summary.scoring_team == 0 { "team-blue" } else { "team-red" };
            let label = if summary.euchred {
                "Euchre!"
            } else if summary.points == 4 {
                "Alone march!"
            } else if summary.points == 2 {
                "March!"
            } else {
                ""
            };
            view! {
                <div class="pool-note">
                    <span class=format!("score-chip {chip}")>{format!("+{}", summary.points)}</span>
                    <div class="pool-label">{label}</div>
                </div>
            }
            .into_any()
        }
        Phase::GameOver { winner } => {
            let chip = if *winner == 0 { "team-blue" } else { "team-red" };
            view! {
                <div class="pool-note">
                    <div class="pool-label">"🏆"</div>
                    <span class=format!("score-chip {chip}")>
                        {format!("{}–{}", game.scores[*winner as usize], game.scores[1 - *winner as usize])}
                    </span>
                </div>
            }
            .into_any()
        }
        _ => {
            // Cards land offset toward whoever threw them, stacked in play
            // order. Once the trick is decided it lies there a beat, then the
            // winner takes it — the cards slide off in their direction.
            let taken_by = match &game.phase {
                Phase::TrickDone { winner } => Some(pos_of(*winner)),
                _ => None,
            };
            let count = game.current_trick.len();
            game.current_trick
                .clone()
                .into_iter()
                .enumerate()
                .map(|(i, (s, c))| {
                    let exit = taken_by.map(|w| format!(" exit-{w}")).unwrap_or_default();
                    // Only the newest card animates in; the rest are already
                    // at rest (re-renders must not replay their entrances).
                    let entered = if i + 1 == count { " entered" } else { "" };
                    view! {
                        <span class=format!("pool-card pc-{}{exit}{entered}", pos_of(s))
                            style=format!("z-index:{}", i + 1)>
                            <CardFace card=c/>
                        </span>
                    }
                })
                .collect_view()
                .into_any()
        }
    };
    let kitty = kitty_pool(game, pos_of(game.dealer));

    let status = felt_status(view, game);
    let trump_chip = game.trump.map(|t| {
        view! { <span class="trump-chip" class:red-suit=t.is_red()>{suit_glyph(t)}</span> }
    });
    view! {
        <div class="felt">
            <div class="felt-top">
                <span class="felt-status">{status}</span>
                {trump_chip}
                <span class="score-corner">
                    <span class="score-chip team-blue">{game.scores[0]}</span>
                    <span class="score-chip team-red">{game.scores[1]}</span>
                </span>
            </div>
            <div class="felt-grid">
                <div class="pool">{kitty}{pool}</div>
                {plates}
            </div>
        </div>
    }
}

/// One short line; everything else about the state is shown, not told.
fn felt_status(view: &TableView, game: &GameView) -> String {
    let name = |s: Seat| {
        view.seats[s.index()]
            .name
            .clone()
            .unwrap_or_else(|| format!("Seat {}", s.0 + 1))
    };
    let your_turn = !view.legal.is_empty();
    match &game.phase {
        Phase::Bidding1 { turn } | Phase::Bidding2 { turn } => {
            if your_turn {
                "Your bid".into()
            } else {
                format!("{} to bid", name(*turn))
            }
        }
        Phase::DealerDiscard => {
            if your_turn {
                "Discard one".into()
            } else {
                format!("{} is discarding", name(game.dealer))
            }
        }
        Phase::Playing { turn } => {
            if your_turn {
                "Your turn".into()
            } else {
                format!("{}'s turn", name(*turn))
            }
        }
        Phase::TrickDone { winner } => format!("{} takes it", name(*winner)),
        Phase::HandDone { .. } => "Hand complete".into(),
        Phase::GameOver { .. } => "Game over".into(),
    }
}

// ---------------------------------------------------------------- bidding

fn is_bid(action: &Action) -> bool {
    matches!(action, Action::Pass | Action::OrderUp { .. } | Action::Call { .. })
}

/// Popup for both bidding rounds: round one shows the upcard with an
/// order-it-up choice; round two offers the callable suits. Going alone is a
/// toggle rather than doubled-up options.
#[component]
fn BidDialog(legal: Vec<Action>, upcard: Option<Card>) -> impl IntoView {
    let round1 = legal.iter().any(|a| matches!(a, Action::OrderUp { .. }));
    let may_pass = legal.contains(&Action::Pass);
    let alone = RwSignal::new(false);
    let suit_buttons = (!round1).then(|| {
        let buttons = Suit::ALL
            .into_iter()
            .map(|suit| {
                let enabled = legal.contains(&Action::Call { suit, alone: false });
                view! {
                    <button class="suit-btn" class:red-suit=suit.is_red() disabled=!enabled
                        on:click=move |_| net::send(&ClientMsg::Act {
                            action: Action::Call { suit, alone: alone.get_untracked() },
                        })>
                        {suit_glyph(suit)}
                    </button>
                }
            })
            .collect_view();
        view! { <div class="suit-row">{buttons}</div> }
    });
    view! {
        <div class="dialog-backdrop">
            <div class="dialog">
                <div class="dialog-title">
                    {if round1 { "Order it up?" } else { "Call trump" }}
                </div>
                {(round1).then(|| upcard.map(|c| view! {
                    <div class="dialog-card"><CardFace card=c/></div>
                }))}
                {suit_buttons}
                <button type="button" class="toggle-row"
                    on:click=move |_| alone.update(|a| *a = !*a)>
                    <span class="toggle" class:on=move || alone.get()>
                        <span class="knob"></span>
                    </span>
                    "Go alone"
                </button>
                <div class="dialog-actions">
                    {round1.then(|| view! {
                        <button class="primary" on:click=move |_| net::send(&ClientMsg::Act {
                            action: Action::OrderUp { alone: alone.get_untracked() },
                        })>"Order it up"</button>
                    })}
                    {may_pass.then(|| view! {
                        <button class="ghost" on:click=|_| net::send(&ClientMsg::Act {
                            action: Action::Pass,
                        })>"Pass"</button>
                    })}
                </div>
            </div>
        </div>
    }
}

// ---------------------------------------------------------------- table screens

#[component]
fn TableUi() -> impl IntoView {
    let state = expect_context::<AppState>();
    move || {
        let Some(view) = state.table.get() else {
            return ().into_any();
        };
        match view.role {
            Role::TableDisplay => table_display(&view).into_any(),
            _ if view.you.is_some()
                && view.game.is_some()
                && state.mode.get() == ViewMode::HandOnly =>
            {
                hand_only(&view, state).into_any()
            }
            _ => full_view(&view, state).into_any(),
        }
    }
}

fn full_view(view: &TableView, state: AppState) -> impl IntoView {
    let in_game = view.game.is_some();
    let hand_mode_toggle = (view.you.is_some() && in_game).then(|| {
        view! {
            <button class="ghost" on:click=move |_| {
                state.mode.set(ViewMode::HandOnly);
                storage_set("euc_mode", "hand");
            }>"Hand mode"</button>
        }
    });
    let display_mode = view.you.is_none().then(|| {
        let table_id = view.table_id.clone();
        view! {
            <button class="ghost" on:click=move |_| net::send(&ClientMsg::JoinTable {
                table_id: table_id.clone(),
                role: Role::TableDisplay,
            })>"Table mode"</button>
        }
    });
    let watching = (!view.spectators.is_empty())
        .then(|| view! { <div class="muted small">"Watching: "{view.spectators.join(", ")}</div> });
    let header = view! {
        <div class="table-header">
            <h2>{view.table_name.clone()}</h2>
            <span class="table-id">{view.table_id.clone()}</span>
            {hand_mode_toggle}
            {display_mode}
            {view.you.map(|_| view! {
                <button class="ghost" on:click=|_| net::send(&ClientMsg::StandUp)>"Stand up"</button>
            })}
            <button class="ghost" on:click=|_| net::send(&ClientMsg::LeaveTable)>"Leave"</button>
        </div>
    };
    let body = if let Some(game) = view.game.clone() {
        let anchor = view.you.unwrap_or(Seat(0));
        let bidding = view.legal.iter().any(is_bid);
        let bid_dialog = bidding.then(|| {
            view! { <BidDialog legal=view.legal.clone() upcard=game.upcard/> }
        });
        let actions = view
            .legal
            .iter()
            .filter(|a| {
                // Continue is timer-driven (trick collection, next deal);
                // cards are played from the hand; bids live in the dialog.
                !bidding
                    && !matches!(
                        a,
                        Action::Play { .. } | Action::Discard { .. } | Action::Continue
                    )
            })
            .map(|a| {
                let action = *a;
                view! {
                    <button class="primary" on:click=move |_| net::send(&ClientMsg::Act { action })>
                        {action_label(&action)}
                    </button>
                }
            })
            .collect_view();
        let play_again = matches!(game.phase, Phase::GameOver { .. }).then(|| {
            view! {
                <button class="primary" on:click=|_| net::send(&ClientMsg::StartGame)>"Play again"</button>
            }
        });
        let legal = view.legal.clone();
        let discarding = matches!(game.phase, Phase::DealerDiscard)
            && legal.iter().any(|a| matches!(a, Action::Discard { .. }));
        let hand = (!game.hand.is_empty()).then(|| {
            let cards = sorted_hand(&game.hand, game.trump)
                .into_iter()
                .map(|card| {
                    let action = legal.iter().copied().find(|a| {
                        matches!(a, Action::Play { card: c } | Action::Discard { card: c } if *c == card)
                    });
                    view! { <HandCard card=card action=action/> }
                })
                .collect_view();
            view! {
                <div class="hand-wrap">
                    {discarding.then(|| view! { <div class="hand-hint muted">"Pick a card to bury:"</div> })}
                    <div class="hand" class:dealing=fresh_deal(&game)>{cards}</div>
                </div>
            }
        });
        view! {
            {felt(view, &game, anchor, true)}
            <div class="actions">{actions}{play_again}</div>
            {hand}
            {bid_dialog}
        }
        .into_any()
    } else {
        let turn = None;
        let seats = view
            .seats
            .iter()
            .enumerate()
            .map(|(i, s)| seat_cell(view, i, s.clone(), turn, None, false))
            .collect_view();
        view! {
            <div class="seats">{seats}</div>
            {seating_area(view)}
        }
        .into_any()
    };
    view! {
        {header}
        {body}
        {watching}
    }
}

/// Minimal cards-in-hand view for players seated around a physical table
/// (paired with a table-mode tablet showing the shared state).
fn hand_only(view: &TableView, state: AppState) -> impl IntoView {
    let game = view.game.clone().expect("hand mode only in game");
    let status = felt_status(view, &game);
    let my_turn = !view.legal.is_empty();
    let trump = game
        .trump
        .map(|t| view! { <span class="hand-trump" class:red=t.is_red()>{suit_glyph(t)}</span> });
    let bidding = view.legal.iter().any(is_bid);
    let bid_dialog = bidding.then(|| {
        view! { <BidDialog legal=view.legal.clone() upcard=game.upcard/> }
    });
    let actions = view
        .legal
        .iter()
        .filter(|a| {
            !bidding
                && !matches!(
                    a,
                    Action::Play { .. } | Action::Discard { .. } | Action::Continue
                )
        })
        .map(|a| {
            let action = *a;
            view! {
                <button class="primary big" on:click=move |_| net::send(&ClientMsg::Act { action })>
                    {action_label(&action)}
                </button>
            }
        })
        .collect_view();
    let legal = view.legal.clone();
    let cards = sorted_hand(&game.hand, game.trump)
        .into_iter()
        .map(|card| {
            let action = legal.iter().copied().find(|a| {
                matches!(a, Action::Play { card: c } | Action::Discard { card: c } if *c == card)
            });
            view! { <HandCard card=card action=action/> }
        })
        .collect_view();
    let upcard = game
        .upcard
        .filter(|_| matches!(game.phase, Phase::Bidding1 { .. }))
        .map(|c| view! { <CardFace card=c small=true/> });
    let bid_flash = state.bid_toast.get().map(|t| {
        let who = view.seats[t.seat.index()].name.clone().unwrap_or_default();
        view! { <div class="bid-toast hand-toast">{who}": "{t.text}</div> }
    });
    view! {
        <div class="hand-mode" class:my-turn=my_turn>
            <div class="hand-mode-top">
                <span class="score-corner">
                    <span class="score-chip team-blue">{game.scores[0]}</span>
                    <span class="score-chip team-red">{game.scores[1]}</span>
                </span>
                {trump}
                {upcard}
                <button class="ghost" on:click=move |_| {
                    state.mode.set(ViewMode::Full);
                    storage_set("euc_mode", "full");
                }>"Full view"</button>
            </div>
            <div class="hand-mode-status">{status}</div>
            {bid_flash}
            <div class="actions">{actions}</div>
            <div class="hand hand-big" class:dealing=fresh_deal(&game)>{cards}</div>
            {bid_dialog}
        </div>
    }
}

/// Shared display for a tablet lying on the physical table: public state only,
/// oriented around the felt like the real table around it.
fn table_display(view: &TableView) -> impl IntoView {
    let table_id = view.table_id.clone();
    let exit = view! {
        <button class="ghost exit-display" on:click=move |_| net::send(&ClientMsg::JoinTable {
            table_id: table_id.clone(),
            role: Role::Spectator,
        })>"✕"</button>
    };
    match view.game.clone() {
        Some(game) => view! {
            <div class="table-display">
                {exit}
                {felt(view, &game, Seat(0), false)}
            </div>
        }
        .into_any(),
        None => {
            let seats = view
                .seats
                .iter()
                .enumerate()
                .map(|(i, s)| {
                    let name = s.name.clone().unwrap_or_else(|| "— open —".into());
                    view! {
                        <div class=format!("muted {}", team_class(Seat(i as u8)))>
                            {format!("Seat {} · ", i + 1)}{name}
                        </div>
                    }
                })
                .collect_view();
            view! {
                <div class="table-display">
                    {exit}
                    <div class="td-waiting">
                        <h2>{view.table_name.clone()}</h2>
                        <div class="table-id">{view.table_id.clone()}</div>
                        {seats}
                        <p class="muted">"Waiting for the game to start…"</p>
                    </div>
                </div>
            }
            .into_any()
        }
    }
}

// ---------------------------------------------------------------- seating

fn seat_title(i: usize) -> String {
    format!("Seat {}", i + 1)
}

fn seat_cell(
    view: &TableView,
    i: usize,
    info: euc_shared::SeatInfo,
    turn: Option<Seat>,
    dealer: Option<Seat>,
    in_game: bool,
) -> impl IntoView {
    let seat = Seat(i as u8);
    let is_you = view.you == Some(seat);
    let is_turn = turn == Some(seat);
    let sit = move |_| net::send(&ClientMsg::TakeSeat { seat });
    let add_ai = move |_| net::send(&ClientMsg::AddAi { seat });
    let remove_ai = move |_| net::send(&ClientMsg::RemoveAi { seat });
    let occupant = match &info.name {
        Some(name) => {
            let flags = format!(
                "{}{}{}{}",
                if info.is_ai { " 🤖" } else { "" },
                if dealer == Some(seat) { " · dealer" } else { "" },
                if !info.connected { " · away" } else { "" },
                if is_you { " · you" } else { "" },
            );
            view! {
                <div class="seat-name">{name.clone()}<span class="muted">{flags}</span></div>
                {(info.is_ai && !in_game).then(|| view! {
                    <button class="ghost" on:click=remove_ai>"Remove AI"</button>
                })}
                {(!info.connected && !info.is_ai).then(|| view! {
                    <button class="ghost" on:click=add_ai>"Replace with AI"</button>
                })}
            }
            .into_any()
        }
        None => view! {
            <button on:click=sit>"Sit here"</button>
            <button class="ghost" on:click=add_ai>"+ AI"</button>
        }
        .into_any(),
    };
    view! {
        <div class=format!("seat {}", team_class(seat)) class:you=is_you class:turn=is_turn>
            <div class="seat-title muted">{seat_title(i)}</div>
            {occupant}
        </div>
    }
}

fn seating_area(view: &TableView) -> impl IntoView {
    let full = view.seats.iter().all(|s| s.name.is_some());
    let stick = view.rules.stick_the_dealer;
    let toggle = move |_| {
        net::send(&ClientMsg::SetRules {
            rules: euc_shared::RuleConfig { stick_the_dealer: !stick, win_score: 10 },
        })
    };
    view! {
        <div class="panel">
            <label class="rule-row">
                <input type="checkbox" prop:checked=stick on:change=toggle />
                "Stick the dealer"
            </label>
            <button class="primary" disabled=!full on:click=|_| net::send(&ClientMsg::StartGame)>
                {if full { "Deal 'em up" } else { "Waiting for four players…" }}
            </button>
        </div>
    }
}

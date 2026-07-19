use crate::*;

fn c(suit: Suit, rank: Rank) -> Card {
    Card { suit, rank }
}

/// A hand-built mid-play state for follow-suit and trick-resolution tests.
fn playing_game(hands: [Vec<Card>; 4], trump: Suit, turn: Seat) -> EuchreGame {
    EuchreGame {
        rules: RuleConfig::default(),
        dealer: Seat(3),
        phase: Phase::Playing { turn },
        hands,
        kitty: Vec::new(),
        upcard: None,
        turned_down: None,
        trump: Some(trump),
        maker: Some(Seat(0)),
        alone: false,
        current_trick: Vec::new(),
        last_trick: None,
        tricks_won: [0, 0],
        tricks_by_seat: [0; 4],
        scores: [0, 0],
        rng: lrb_rng::Rng::from_seed(1),
    }
}

fn pass_around_once(game: &mut EuchreGame) {
    for _ in 0..4 {
        let turn = game.turn_seat().unwrap();
        game.apply(turn, Action::Pass).unwrap();
    }
}

// ---------------------------------------------------------------- cards

#[test]
fn deck_has_24_unique_cards() {
    let deck = deck24();
    assert_eq!(deck.len(), 24);
    for i in 0..deck.len() {
        for j in i + 1..deck.len() {
            assert_ne!(deck[i], deck[j]);
        }
    }
}

#[test]
fn left_bower_counts_as_trump() {
    // Diamonds trump: J♥ is the left bower and IS a diamond for every purpose.
    assert_eq!(effective_suit(c(Suit::Hearts, Rank::Jack), Suit::Diamonds), Suit::Diamonds);
    // The right bower keeps its own suit.
    assert_eq!(effective_suit(c(Suit::Diamonds, Rank::Jack), Suit::Diamonds), Suit::Diamonds);
    // Off-color jacks are unaffected.
    assert_eq!(effective_suit(c(Suit::Spades, Rank::Jack), Suit::Diamonds), Suit::Spades);
    // Non-jacks are unaffected.
    assert_eq!(effective_suit(c(Suit::Hearts, Rank::Ace), Suit::Diamonds), Suit::Hearts);
}

#[test]
fn trick_power_ordering() {
    let t = Suit::Spades;
    let led = Suit::Hearts;
    let right = trick_power(c(Suit::Spades, Rank::Jack), t, led);
    let left = trick_power(c(Suit::Clubs, Rank::Jack), t, led);
    let ace_trump = trick_power(c(Suit::Spades, Rank::Ace), t, led);
    let nine_trump = trick_power(c(Suit::Spades, Rank::Nine), t, led);
    let ace_led = trick_power(c(Suit::Hearts, Rank::Ace), t, led);
    let nine_led = trick_power(c(Suit::Hearts, Rank::Nine), t, led);
    let off = trick_power(c(Suit::Diamonds, Rank::Ace), t, led);
    assert!(right > left);
    assert!(left > ace_trump);
    assert!(ace_trump > nine_trump);
    assert!(nine_trump > ace_led);
    assert!(ace_led > nine_led);
    assert_eq!(off, 0);
    assert!(nine_led > off);
}

// ---------------------------------------------------------------- dealing & bidding

#[test]
fn new_game_deals_correctly() {
    let game = EuchreGame::new(RuleConfig::default(), 42);
    for seat in Seat::ALL {
        assert_eq!(game.hand(seat).len(), 5);
    }
    assert!(game.upcard.is_some());
    assert_eq!(game.kitty.len(), 3);
    assert_eq!(game.phase, Phase::Bidding1 { turn: game.dealer.next() });
    assert_eq!(game.scores, [0, 0]);
    assert_eq!(game.trump, None);
}

#[test]
fn round1_all_pass_turns_down_upcard() {
    let mut game = EuchreGame::new(RuleConfig::default(), 7);
    let upcard = game.upcard.unwrap();
    pass_around_once(&mut game);
    assert_eq!(game.phase, Phase::Bidding2 { turn: game.dealer.next() });
    assert_eq!(game.turned_down, Some(upcard));
    assert_eq!(game.upcard, None);
}

#[test]
fn order_up_gives_dealer_the_card_and_requires_discard() {
    let mut game = EuchreGame::new(RuleConfig::default(), 7);
    let upcard = game.upcard.unwrap();
    let eldest = game.dealer.next();
    game.apply(eldest, Action::OrderUp { alone: false }).unwrap();
    assert_eq!(game.trump, Some(upcard.suit));
    assert_eq!(game.maker, Some(eldest));
    assert_eq!(game.phase, Phase::DealerDiscard);
    assert_eq!(game.hand(game.dealer).len(), 6);
    assert!(game.hand(game.dealer).contains(&upcard));

    // Only the dealer acts, with one discard option per card.
    assert!(game.legal_actions(eldest).is_empty());
    let legal = game.legal_actions(game.dealer);
    assert_eq!(legal.len(), 6);

    let discard = game.hand(game.dealer)[0];
    game.apply(game.dealer, Action::Discard { card: discard }).unwrap();
    assert_eq!(game.hand(game.dealer).len(), 5);
    assert_eq!(game.kitty.len(), 4);
    assert_eq!(game.phase, Phase::Playing { turn: eldest });
}

#[test]
fn round2_cannot_call_turned_down_suit() {
    let mut game = EuchreGame::new(RuleConfig::default(), 7);
    pass_around_once(&mut game);
    let turned = game.turned_down.unwrap().suit;
    let legal = game.legal_actions(game.dealer.next());
    assert!(legal.contains(&Action::Pass));
    for suit in Suit::ALL {
        let should_exist = suit != turned;
        assert_eq!(legal.contains(&Action::Call { suit, alone: false }), should_exist);
        assert_eq!(legal.contains(&Action::Call { suit, alone: true }), should_exist);
    }
}

#[test]
fn round2_all_pass_redeals_with_next_dealer() {
    let mut game = EuchreGame::new(RuleConfig::default(), 7);
    let old_dealer = game.dealer;
    pass_around_once(&mut game);
    pass_around_once(&mut game);
    assert_eq!(game.dealer, old_dealer.next());
    assert_eq!(game.phase, Phase::Bidding1 { turn: game.dealer.next() });
    assert!(game.upcard.is_some());
    assert_eq!(game.turned_down, None);
    assert_eq!(game.trump, None);
    for seat in Seat::ALL {
        assert_eq!(game.hand(seat).len(), 5);
    }
}

#[test]
fn stick_the_dealer_forces_a_call() {
    let rules = RuleConfig { stick_the_dealer: true, ..RuleConfig::default() };
    let mut game = EuchreGame::new(rules, 7);
    pass_around_once(&mut game);
    // Round 2: the three non-dealers may pass...
    for _ in 0..3 {
        let turn = game.turn_seat().unwrap();
        game.apply(turn, Action::Pass).unwrap();
    }
    // ...but the dealer must call.
    let legal = game.legal_actions(game.dealer);
    assert!(!legal.contains(&Action::Pass));
    assert!(!legal.is_empty());
    assert!(game.apply(game.dealer, Action::Pass).is_err());
    let turned = game.turned_down.unwrap().suit;
    let suit = Suit::ALL.into_iter().find(|&s| s != turned).unwrap();
    game.apply(game.dealer, Action::Call { suit, alone: false }).unwrap();
    assert_eq!(game.trump, Some(suit));
    assert_eq!(game.maker, Some(game.dealer));
}

// ---------------------------------------------------------------- following suit

#[test]
fn must_follow_effective_suit_not_printed_suit() {
    // Diamonds trump. Seat 1 holds the left bower (J♥) — nominally a heart,
    // effectively a diamond — plus a real heart. When hearts are led, only the
    // real heart may be played.
    let mut game = playing_game(
        [
            vec![c(Suit::Hearts, Rank::Ace), c(Suit::Clubs, Rank::Nine)],
            vec![c(Suit::Hearts, Rank::Jack), c(Suit::Hearts, Rank::Nine), c(Suit::Clubs, Rank::Ten)],
            vec![c(Suit::Clubs, Rank::King)],
            vec![c(Suit::Clubs, Rank::Queen)],
        ],
        Suit::Diamonds,
        Seat(0),
    );
    game.apply(Seat(0), Action::Play { card: c(Suit::Hearts, Rank::Ace) }).unwrap();
    let legal = game.legal_actions(Seat(1));
    assert_eq!(legal, vec![Action::Play { card: c(Suit::Hearts, Rank::Nine) }]);
}

#[test]
fn left_bower_holder_need_not_follow_its_printed_suit() {
    // Classic trap: diamonds trump, hearts led, and seat 1's only "heart" is
    // the left bower J♥ — which is a diamond, so seat 1 may play anything.
    let mut game = playing_game(
        [
            vec![c(Suit::Hearts, Rank::Ace)],
            vec![c(Suit::Hearts, Rank::Jack), c(Suit::Clubs, Rank::Nine)],
            vec![c(Suit::Clubs, Rank::King)],
            vec![c(Suit::Clubs, Rank::Queen)],
        ],
        Suit::Diamonds,
        Seat(0),
    );
    game.apply(Seat(0), Action::Play { card: c(Suit::Hearts, Rank::Ace) }).unwrap();
    let legal = game.legal_actions(Seat(1));
    assert_eq!(legal.len(), 2);
}

// ---------------------------------------------------------------- tricks

#[test]
fn low_trump_beats_high_led_suit() {
    let mut game = playing_game(
        [
            vec![c(Suit::Hearts, Rank::Ace)],
            vec![c(Suit::Spades, Rank::Nine)],
            vec![c(Suit::Hearts, Rank::King)],
            vec![c(Suit::Hearts, Rank::Ten)],
        ],
        Suit::Spades,
        Seat(0),
    );
    game.apply(Seat(0), Action::Play { card: c(Suit::Hearts, Rank::Ace) }).unwrap();
    game.apply(Seat(1), Action::Play { card: c(Suit::Spades, Rank::Nine) }).unwrap();
    game.apply(Seat(2), Action::Play { card: c(Suit::Hearts, Rank::King) }).unwrap();
    game.apply(Seat(3), Action::Play { card: c(Suit::Hearts, Rank::Ten) }).unwrap();
    // The full trick stays visible until collected...
    assert_eq!(game.phase, Phase::TrickDone { winner: Seat(1) });
    assert_eq!(game.current_trick.len(), 4);
    assert_eq!(game.tricks_won, [0, 1]);
    // ...then the winner leads.
    game.apply(Seat(2), Action::Continue).unwrap();
    assert_eq!(game.phase, Phase::Playing { turn: Seat(1) });
    assert!(game.current_trick.is_empty());
    assert_eq!(game.last_trick.as_ref().unwrap().len(), 4);
}

#[test]
fn right_bower_beats_left_bower_beats_trump_ace() {
    let mut game = playing_game(
        [
            vec![c(Suit::Spades, Rank::Ace)],
            vec![c(Suit::Clubs, Rank::Jack)],  // left bower
            vec![c(Suit::Spades, Rank::Jack)], // right bower
            vec![c(Suit::Spades, Rank::Nine)],
        ],
        Suit::Spades,
        Seat(0),
    );
    for seat in Seat::ALL {
        let card = game.hand(seat)[0];
        game.apply(seat, Action::Play { card }).unwrap();
    }
    assert_eq!(game.tricks_won, [1, 0]); // seat 2 (team 0) won
    assert_eq!(game.phase, Phase::TrickDone { winner: Seat(2) });
    game.apply(Seat(0), Action::Continue).unwrap();
    assert_eq!(game.phase, Phase::Playing { turn: Seat(2) });
}

// ---------------------------------------------------------------- going alone

#[test]
fn going_alone_skips_the_makers_partner() {
    let mut game = EuchreGame::new(RuleConfig::default(), 11);
    let eldest = game.dealer.next();
    game.apply(eldest, Action::OrderUp { alone: true }).unwrap();
    assert_eq!(game.sitting_out(), Some(eldest.partner()));
    let discard = game.hand(game.dealer)[0];
    game.apply(game.dealer, Action::Discard { card: discard }).unwrap();

    // Three plays complete a trick; the sat-out partner never gets a turn.
    let mut plays = 0;
    while matches!(game.phase, Phase::Playing { .. }) && plays < 3 {
        let turn = game.turn_seat().unwrap();
        assert_ne!(Some(turn), game.sitting_out());
        let card = game.legal_actions(turn)[0];
        game.apply(turn, card).unwrap();
        plays += 1;
    }
    assert_eq!(game.tricks_won[0] + game.tricks_won[1], 1);
    assert_eq!(game.hand(eldest.partner()).len(), 5, "partner's hand is untouched");
}

#[test]
fn alone_by_dealers_partner_skips_the_discard() {
    let mut game = EuchreGame::new(RuleConfig::default(), 11);
    let eldest = game.dealer.next();
    game.apply(eldest, Action::Pass).unwrap();
    // Second bidder is the dealer's partner; going alone kills the dealer's
    // hand, so there is no pickup/discard phase.
    let partner = game.dealer.partner();
    game.apply(partner, Action::OrderUp { alone: true }).unwrap();
    assert_eq!(game.sitting_out(), Some(game.dealer));
    assert_eq!(game.phase, Phase::Playing { turn: eldest });
    assert_eq!(game.hand(game.dealer).len(), 6, "dead hand keeps the picked-up card");
}

// ---------------------------------------------------------------- scoring

#[test]
fn scoring_table() {
    // Makers (team 0) take 3 or 4: 1 point.
    assert_eq!(hand_points(Seat(0), [3, 2], false), (0, 1, false));
    assert_eq!(hand_points(Seat(2), [4, 1], false), (0, 1, false));
    // March: 2. Alone march: 4.
    assert_eq!(hand_points(Seat(0), [5, 0], false), (0, 2, false));
    assert_eq!(hand_points(Seat(0), [5, 0], true), (0, 4, false));
    // Alone but only 3-4 tricks is still 1.
    assert_eq!(hand_points(Seat(0), [4, 1], true), (0, 1, false));
    // Euchred: defenders score 2.
    assert_eq!(hand_points(Seat(0), [2, 3], false), (1, 2, true));
    assert_eq!(hand_points(Seat(1), [3, 2], true), (0, 2, true));
    // Team-1 maker wins.
    assert_eq!(hand_points(Seat(3), [1, 4], false), (1, 1, false));
}

#[test]
fn game_ends_at_win_score() {
    let mut game = playing_game(
        [
            vec![c(Suit::Spades, Rank::Ace)],
            vec![c(Suit::Hearts, Rank::Nine)],
            vec![c(Suit::Hearts, Rank::Ten)],
            vec![c(Suit::Hearts, Rank::Jack)],
        ],
        Suit::Spades,
        Seat(0),
    );
    game.scores = [9, 0];
    game.tricks_won = [3, 1];
    for seat in Seat::ALL {
        let card = game.hand(seat)[0];
        game.apply(seat, Action::Play { card }).unwrap();
    }
    game.apply(Seat(0), Action::Continue).unwrap(); // collect the last trick
    assert_eq!(game.scores, [10, 0]);
    assert_eq!(game.phase, Phase::GameOver { winner: 0 });
    assert_eq!(game.turn_seat(), None);
    for seat in Seat::ALL {
        assert!(game.legal_actions(seat).is_empty());
    }
}

#[test]
fn hand_done_then_continue_deals_next_hand() {
    let mut game = playing_game(
        [
            vec![c(Suit::Spades, Rank::Ace)],
            vec![c(Suit::Hearts, Rank::Nine)],
            vec![c(Suit::Hearts, Rank::Ten)],
            vec![c(Suit::Hearts, Rank::Jack)],
        ],
        Suit::Spades,
        Seat(0),
    );
    game.tricks_won = [3, 1];
    let old_dealer = game.dealer;
    for seat in Seat::ALL {
        let card = game.hand(seat)[0];
        game.apply(seat, Action::Play { card }).unwrap();
    }
    game.apply(Seat(0), Action::Continue).unwrap(); // collect the last trick
    match &game.phase {
        Phase::HandDone { summary } => {
            assert_eq!(summary.tricks, [4, 1]);
            assert_eq!(summary.scoring_team, 0);
            assert_eq!(summary.points, 1);
            assert!(!summary.euchred);
        }
        other => panic!("expected HandDone, got {other:?}"),
    }
    game.apply(Seat(2), Action::Continue).unwrap();
    assert_eq!(game.dealer, old_dealer.next());
    assert_eq!(game.phase, Phase::Bidding1 { turn: game.dealer.next() });
    for seat in Seat::ALL {
        assert_eq!(game.hand(seat).len(), 5);
    }
}

// ---------------------------------------------------------------- redaction

#[test]
fn redaction_shows_only_your_hand() {
    let game = EuchreGame::new(RuleConfig::default(), 5);
    let meta = TableMeta::default();

    let seated = redact(&meta, Some(&game), Role::Seated { seat: Seat(1) });
    let gv = seated.game.as_ref().unwrap();
    assert_eq!(gv.hand, game.hand(Seat(1)).to_vec());
    assert_eq!(gv.hand_counts, [5, 5, 5, 5]);

    for role in [Role::Spectator, Role::TableDisplay] {
        let view = redact(&meta, Some(&game), role);
        let gv = view.game.as_ref().unwrap();
        assert!(gv.hand.is_empty(), "{role:?} must not see any hand");
        assert!(view.legal.is_empty());
        // Serialized form contains no card lists other than public ones.
        let json = serde_json::to_string(&view).unwrap();
        assert!(!json.contains("kitty"));
    }

    // Only the seat whose turn it is gets legal actions.
    let turn = game.turn_seat().unwrap();
    assert!(!redact(&meta, Some(&game), Role::Seated { seat: turn }).legal.is_empty());
    let idle = turn.next();
    assert!(redact(&meta, Some(&game), Role::Seated { seat: idle }).legal.is_empty());
}

// ---------------------------------------------------------------- protocol

#[test]
fn protocol_golden_strings() {
    // These strings are the wire format external bots build against
    // (documented in PROTOCOL.md). Changing them is a breaking change.
    let act = ClientMsg::Act {
        action: Action::Play { card: c(Suit::Hearts, Rank::Jack) },
    };
    assert_eq!(
        serde_json::to_string(&act).unwrap(),
        r#"{"type":"act","action":{"type":"play","card":{"suit":"hearts","rank":"jack"}}}"#
    );

    let join = ClientMsg::JoinTable {
        table_id: "AB12".to_string(),
        role: Role::Seated { seat: Seat(2) },
    };
    assert_eq!(
        serde_json::to_string(&join).unwrap(),
        r#"{"type":"join_table","table_id":"AB12","role":{"type":"seated","seat":2}}"#
    );

    let call = Action::Call { suit: Suit::Spades, alone: true };
    assert_eq!(
        serde_json::to_string(&call).unwrap(),
        r#"{"type":"call","suit":"spades","alone":true}"#
    );

    let err = ServerMsg::Error {
        code: ErrorCode::NotYourTurn,
        message: "wait".to_string(),
    };
    assert_eq!(
        serde_json::to_string(&err).unwrap(),
        r#"{"type":"error","code":"not_your_turn","message":"wait"}"#
    );

    let create = ClientMsg::CreateTable { name: "kitchen".to_string(), rules: RuleConfig::default() };
    assert_eq!(
        serde_json::to_string(&create).unwrap(),
        r#"{"type":"create_table","name":"kitchen","rules":{"stick_the_dealer":false,"win_score":10}}"#
    );
}

#[test]
fn protocol_round_trips() {
    let msgs = vec![
        ClientMsg::Hello { name: "ryan".into() },
        ClientMsg::JoinTable { table_id: "XY".into(), role: Role::TableDisplay },
        ClientMsg::Act { action: Action::OrderUp { alone: true } },
        ClientMsg::Act { action: Action::Discard { card: c(Suit::Clubs, Rank::Nine) } },
        ClientMsg::SetRules { rules: RuleConfig { stick_the_dealer: true, win_score: 5 } },
    ];
    for msg in msgs {
        let json = serde_json::to_string(&msg).unwrap();
        let back: ClientMsg = serde_json::from_str(&json).unwrap();
        assert_eq!(back, msg);
    }

    // CreateTable rules default when omitted.
    let msg: ClientMsg = serde_json::from_str(r#"{"type":"create_table","name":"t"}"#).unwrap();
    assert_eq!(
        msg,
        ClientMsg::CreateTable { name: "t".into(), rules: RuleConfig::default() }
    );

    let game = EuchreGame::new(RuleConfig::default(), 3);
    let view = redact(&TableMeta::default(), Some(&game), Role::Seated { seat: Seat(0) });
    let server = ServerMsg::TableState { view };
    let json = serde_json::to_string(&server).unwrap();
    let back: ServerMsg = serde_json::from_str(&json).unwrap();
    assert_eq!(back, server);
}

// ---------------------------------------------------------------- self-play

/// The rules-engine fuzz: 1000 random-legal-move games must all run to
/// completion without a RuleError or a stuck state.
#[test]
fn random_bots_complete_1000_games() {
    let mut rng = lrb_rng::Rng::from_seed(0xE0C);
    for seed in 0..1000 {
        let mut game = EuchreGame::new(RuleConfig { stick_the_dealer: seed % 2 == 0, ..RuleConfig::default() }, seed);
        let mut steps = 0;
        while let Some(turn) = game.turn_seat() {
            let legal = game.legal_actions(turn);
            assert!(!legal.is_empty(), "actor with no legal moves at {:?}", game.phase);
            let action = legal[rng.gen_range(legal.len())];
            game.apply(turn, action).unwrap();
            steps += 1;
            assert!(steps < 100_000, "game did not terminate (seed {seed})");
        }
        let Phase::GameOver { winner } = game.phase else {
            panic!("expected GameOver (seed {seed})");
        };
        let w = winner as usize;
        assert!(game.scores[w] >= game.rules.win_score);
        assert!(game.scores[1 - w] < game.scores[w]);
    }
}

/// The heuristic bot must always pick a legal action, across full games.
#[test]
fn heuristic_bots_complete_games_legally() {
    let meta = TableMeta::default();
    for seed in 0..200 {
        let mut game = EuchreGame::new(RuleConfig { stick_the_dealer: seed % 2 == 0, ..RuleConfig::default() }, seed);
        let mut bot = HeuristicBot;
        let mut steps = 0;
        while let Some(turn) = game.turn_seat() {
            let view = redact(&meta, Some(&game), Role::Seated { seat: turn });
            let action = bot.choose(&view);
            assert!(
                view.legal.contains(&action),
                "bot chose illegal {action:?} at {:?} (seed {seed})",
                game.phase
            );
            game.apply(turn, action).unwrap();
            steps += 1;
            assert!(steps < 100_000, "game did not terminate (seed {seed})");
        }
        assert!(matches!(game.phase, Phase::GameOver { .. }));
    }
}

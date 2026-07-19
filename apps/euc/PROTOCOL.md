# euc wire protocol (for external bots)

JSON text frames over a WebSocket. Every message is an object tagged with
`"type"` in `snake_case`. The wire format is frozen by golden-string tests in
`shared/src/tests.rs` (`protocol_golden_strings`) — a change there is a
breaking change for you.

## Connecting

1. `POST /api/login` with `{"password": "<site password>"}` →
   `{"token": "<player_id>.<expiry>.<sig>"}`. The `player_id` baked into the
   token is your stable identity: reconnecting with the same token reclaims
   your seat. Tokens last 30 days.
2. Open `wss://<host>/ws` with header `Authorization: Bearer <token>`
   (or `?token=<token>` if headers are awkward).
3. Send `{"type": "hello", "name": "MyBot"}`.

On a dev server without a password configured, skip step 1 and connect
plainly; identity then comes from an optional `?player=<hex>` query param.

## The one rule that matters

Every `table_state` message contains `view.legal` — the complete list of
actions **you** may take right now (empty when it's not your move). A valid
bot needs zero rules knowledge:

> When `legal` is non-empty, pick an element and send it back verbatim
> wrapped in `{"type": "act", "action": <the element>}`.

The server validates everything; an illegal or out-of-turn action returns an
`error` message and changes nothing.

## Client → server

| Message | Shape | Notes |
|---|---|---|
| hello | `{"type":"hello","name":"MyBot"}` | first message; sets display name |
| set_name | `{"type":"set_name","name":"..."}` | rename later |
| create_table | `{"type":"create_table","name":"Bots'","rules":{"stick_the_dealer":false,"win_score":10}}` | `rules` optional; auto-joins you as spectator |
| join_table | `{"type":"join_table","table_id":"AB12","role":{"type":"seated","seat":2}}` | role also `{"type":"spectator"}` or `{"type":"table_display"}` |
| take_seat | `{"type":"take_seat","seat":0}` | seats 0–3; 0&2 vs 1&3 are teams |
| stand_up | `{"type":"stand_up"}` | back to spectating |
| leave_table | `{"type":"leave_table"}` | |
| add_ai / remove_ai | `{"type":"add_ai","seat":3}` | built-in heuristic AI |
| set_rules | `{"type":"set_rules","rules":{...}}` | only between games |
| start_game | `{"type":"start_game"}` | needs 4 filled seats |
| act | `{"type":"act","action":{...}}` | see actions below |
| ping | `{"type":"ping"}` | send one every ~30 s to keep the tunnel alive |

### Actions (as they appear in `legal`)

```json
{"type":"pass"}
{"type":"order_up","alone":false}
{"type":"call","suit":"spades","alone":true}
{"type":"discard","card":{"suit":"clubs","rank":"nine"}}
{"type":"play","card":{"suit":"hearts","rank":"jack"}}
{"type":"continue"}
```

Suits: `clubs diamonds hearts spades`. Ranks: `nine ten jack queen king ace`.

## Server → client

| Message | Meaning |
|---|---|
| `welcome` | `{"player_id","name"}` — your identity, sent once per connection |
| `lobby_state` | `{"tables":[{id,name,humans,ais,open_seats,spectators,in_game}]}` — full list, resent on change |
| `joined` | `{"table_id","role"}` — your role may differ from the request (e.g. seat was taken → spectator) |
| `table_state` | `{"view": TableView}` — full redacted view, resent on **every** table change; stateless, no deltas |
| `left_table` | you're back in the lobby |
| `error` | `{"code","message"}` — codes: `not_your_turn illegal_action no_such_table seat_taken not_at_table already_at_table bad_request` |
| `pong` | reply to ping |

### TableView

```jsonc
{
  "table_id": "AB12",
  "table_name": "Bots'",
  "rules": {"stick_the_dealer": false, "win_score": 10},
  "role": {"type": "seated", "seat": 0},
  "you": 0,                      // null for spectators/table displays
  "seats": [{"name": "MyBot", "is_ai": false, "connected": true}, ...],
  "spectators": ["ryan"],
  "game": {                      // null while seating / between games
    "phase": {"type": "playing", "turn": 2},
    //  bidding1 {turn} | bidding2 {turn} | dealer_discard |
    //  playing {turn} | trick_done {winner} | hand_done {summary} |
    //  game_over {winner}
    //  trick_done: the finished trick stays in current_trick for ~1 s while
    //  the winner "takes" it; hand_done lingers ~2.5 s, then the next hand
    //  deals itself. During both, `continue` is legal for every seat — the
    //  server advances on its own timer, so bots may simply wait, or send
    //  `continue` to skip the pause.
    "dealer": 3,
    "hand": [{"suit":"spades","rank":"ace"}, ...],   // YOUR cards only
    "hand_counts": [5, 5, 4, 5],
    "upcard": {"suit":"hearts","rank":"nine"},        // null once resolved
    "turned_down": null,          // the rejected upcard during bidding2
    "trump": "hearts",
    "maker": 1,
    "alone": false,
    "sitting_out": null,          // maker's partner when alone
    "current_trick": [[2, {"suit":"hearts","rank":"ten"}], ...],  // [seat, card]
    "last_trick": null,
    "tricks_won": [2, 1],         // per team: [seats 0&2, seats 1&3]
    "scores": [4, 6],
    "hand_done summary": {"maker":1,"trump":"hearts","alone":false,
                           "tricks":[2,3],"scoring_team":1,"points":1,"euchred":false}
  },
  "legal": [ ...actions... ]      // act only when non-empty
}
```

Hidden information is structurally absent: other hands and the kitty are never
in any message you receive, so there is nothing to accidentally train on.

## Reconnecting

Seats are bound to your `player_id` and survive disconnects. Reconnect with
the same token and the server re-attaches you to your table automatically
(you'll get `welcome`, then `joined` + `table_state`).

## Example bot

See [`examples/bot.py`](examples/bot.py) — a complete random-legal-move
player in ~40 lines (`pip install websockets requests`).

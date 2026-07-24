# euc — multiplayer Euchre

A web Euchre game for friends: browser clients (phone/tablet/laptop), a lobby
of concurrent tables with seat picking and spectating, built-in AI opponents,
a **table mode** (tablet lying on the physical table showing the shared state)
paired with a **hand mode** (minimal cards-only phone view) for hybrid
in-person/remote play, and a JSON WebSocket protocol external bots can join
through ([PROTOCOL.md](PROTOCOL.md)).

## Run it

```sh
bazel run //apps/euc:serve        # http://localhost:8080
EUC_PORT=8090 bazel run //apps/euc:serve
bazel test //apps/euc/... //lrb/rng:rng_test
```

Auth is disabled unless `EUC_SITE_PASSWORD` (or `EUC_SITE_PASSWORD_FILE`) is
set; then every request needs the signed session cookie minted by the login
page (`/login.html`), and bots authenticate per PROTOCOL.md. Set
`EUC_TOKEN_SECRET[_FILE]` too or sessions reset on every server restart.

## Architecture

Three crates in one Cargo workspace (deps resolved by the `@euc_crates`
crate_universe hub in `//:MODULE.bazel`; first-party deps are Bazel-only —
see the comment in `shared/Cargo.toml`):

- **`shared/` (`euc_shared`)** — pure, deterministic rules engine + wire
  protocol + the built-in `HeuristicBot`. The server owns an `EuchreGame` and
  advances it with `apply(seat, action)`; every action is validated against
  `legal_actions(seat)`, and that same list ships to clients/bots in their
  view, so UIs and bots never re-implement rules. Hidden information never
  leaves the server: each connection gets a per-role **redacted** `TableView`
  (`view.rs`) — your own hand only, card counts for everyone else, kitty
  never. Seeded RNG (`//lrb/rng`, shared with brm) makes full games
  reproducible; see the 1000-game fuzz in `src/tests.rs`.
- **`server/` (`euc_server`)** — axum. One actor task per table owns the game
  and its subscribers (no shared locks on game state); an event-driven
  full-view broadcast goes out on every change (no tick loop — it's a card
  game). The lobby registry tracks tables, pushes summaries to lobby watchers,
  reaps empty tables, and maps `player_id → table` so a reconnect reclaims the
  seat. AI seats are driven inside the actor through the exact same `apply`
  path as humans, acting on the same redacted view (they cannot cheat).
  `auth.rs` holds the shared-password + HMAC-token layer.
- **`client/` (`euc_client`)** — Leptos (CSR) compiled to wasm via
  `rust_wasm_bindgen(target = "web")`. One WebSocket into signals; the UI is
  re-rendered wholesale from each `TableView`. View modes: full (default),
  hand mode (seated players; big cards, minimal chrome), table display (a
  seatless role — public info laid out around a virtual felt). URL params
  `?table=ID&mode=table|hand` let a tablet bookmark its table.

`web/` is the static shell (index.html + login.html + CSS; no bundler — the
wasm-bindgen ES module is imported directly).

## Deploy

```sh
bazel run //apps/euc:euc_push     # multi-arch image → ghcr.io/ryandraves/euc
```

`services/euc/` runs it behind a Tailscale sidecar with **Funnel enabled**
(public internet), which is why the site password exists. Secrets (setec:
`euc/password`, `euc/token_secret`, plus the Tailscale authkey) are mounted as
docker secrets; the image reads them via `EUC_*_FILE`.

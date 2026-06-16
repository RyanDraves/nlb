# brm — Bomberman

A small Bomberman for playing with friends. Written entirely in
Rust on the repo's Bazel/`rules_rust` setup, with a deliberately simple game and
a deliberately universal-compatibility networking story.

## How it fits together

Every player — couch players on the host keyboard, controller players, and
browser/phone guests over the LAN — is a networked client of **one authoritative
local server**. That single design choice collapses "local" and "LAN" into one
code path.

```
apps/brm/
  shared/   brm_shared  — pure, deterministic game model + sim (step) + wire
                          protocol (serde). No I/O; compiles for native AND wasm.
  server/   brm_server  — headless: axum HTTP (serves the web client) + WebSocket
                          + a 30 Hz authoritative sim loop. Broadcasts snapshots.
  client/   brm_client  — macroquad render + input. Builds two ways from one
                          source: a native binary (couch players) and a wasm32
                          binary (browser guests). Transport: quad-net (native),
                          brm_net.js (web).
  web/      index.html + macroquad's JS loader + the brm_net.js WebSocket plugin.
```

The server is authoritative: clients send `ClientMsg::Input`, the server steps
the sim and broadcasts `ServerMsg::Snapshot(GameState)` to everyone. Each local
player opens its own WebSocket, so the native client running two split-keyboard
players simply holds two connections.

## Controls (native client)

- Player 1: **WASD** to move, **Space** to drop a bomb.
- Player 2: **Arrow keys** to move, **Enter** to drop a bomb.

Browser/phone guests are one player each (currently keyboard; touch controls are
a fast-follow).

## Match flow

`Lobby → Countdown → Playing → RoundOver → Lobby`. Connecting drops you in the
**lobby**; press your bomb key to toggle **ready** (it also un-readies). When all
participants are ready a **3-2-1 countdown** runs over the freshly generated
arena, then the round goes live. A 2+ player round ends when one is left standing
(shown as the **winner**); a solo round ends when the lone player dies — either
way everyone auto-returns to the lobby. Joining mid-round makes you a
**spectator** until the next one. The whole flow lives in `brm_shared`'s `step()`
so it's deterministic and the client just renders by `Phase`. During a round each
player's collected power-ups (and name) show in the margin by their spawn corner.

## Run it

The server hosts the game and serves the browser client in one process:

```sh
# One-command launcher (builds wasm + server + bundle, then serves on :8080):
bazel run //apps/brm:serve
# Override the port: BRM_PORT=9000 bazel run //apps/brm:serve
```

Then:
- **Couch players** on the host: `bazel run //apps/brm/client` (defaults to two
  split-keyboard players against `ws://127.0.0.1:8080/ws`). Choose the count with
  `bazel run //apps/brm/client -- --players 1` (or `2`), and point elsewhere with
  `--server ws://host:port/ws` (`BRM_PLAYERS` / `BRM_SERVER` also work).
- **LAN guests**: open `http://<host-LAN-ip>:8080` in a browser on a laptop or
  phone on the same network. The page auto-connects back to the host.

Everyone names themselves in the lobby: press **E** to edit, type (15 char max),
then press your action key to confirm and ready up.

## Build & test

```sh
bazel test //apps/brm/shared:brm_shared_test          # deterministic sim tests
bazel build //apps/brm/...                            # shared, server, native client
bazel build //apps/brm:client_wasm_for_web            # the wasm client
```

## Dependency & toolchain notes

The repo is on `rules_rust` / `rules_rust_wasm_bindgen` 0.70.0 (Rust 1.95), so
the dependency tree is plain — no version gymnastics:

- **`@brm_crates` is generated from this app's own `Cargo.toml`/`Cargo.lock`**
  (a `from_cargo` hub in `//:MODULE.bazel`), kept separate from the repo's
  hand-specced `@crates` hub because the game's tree (macroquad/axum/tokio/…) is
  far too large to hand-list.
- To change dependencies: edit the manifests, regenerate the lock with
  `bazel run @rules_rust//tools/upstream_wrapper:cargo -- generate-lockfile
  --manifest-path apps/brm/Cargo.toml`, then **delete `//:MODULE.bazel.lock`** so
  the `@brm_crates` hub regenerates from the new lock on the next build (Bazel
  otherwise reuses the cached hub).
- The wasm client links with `-Clink-arg=--allow-undefined` so macroquad/miniquad's
  JS-provided functions become wasm imports resolved by the loader at runtime.

### Web assets

macroquad's wasm uses its own JS loader (not wasm-bindgen). `web/` holds:

- `mq_js_bundle.js`: vendored verbatim from the macroquad 0.4.15 crate (matches
  miniquad 0.4.10); the only change is `preserveDrawingBuffer:true` so the canvas
  can be screenshotted.
- `brm_net.js`: a small first-party WebSocket plugin implementing the `brm_ws_*`
  imports from `client/src/main.rs`. It talks to the browser WebSocket via raw
  `wasm_memory` and resolves the relative `/ws` path against the page origin (so
  LAN guests connect back to the host). We don't use the abandoned `quad-net` on
  the web because its JS depends on a sapp_jsutils API current macroquad dropped;
  native still uses quad-net.

## Verifying in a browser

`.claude/launch.json` defines a `brm` preview server that runs
`bazel run //apps/brm:serve`. With it up, the wasm client boots, connects over
WebSocket, and renders the map fed by live 30 Hz snapshots.

## Power-ups

Destroyed blocks may reveal a power-up (`POWERUP_CHANCE`). Six kinds, drawn from
the embedded sprite sheet `assets/powerups.png` (placeholder art — swap the PNG
and rebuild): **ExtraBomb**, **Range**, **Speed**, **Kick** (push bombs by
walking into them), **Pierce** (your bombs' blast punches through blocks), and
**Shield** (absorb one otherwise-fatal blast).

## Not done yet (fast-follows)

Player character animation, controller (gamepad) support, on-screen touch
controls for phones, player name entry in the lobby, and real (hand-drawn) art
assets are the next steps. Internet/NAT play is out of scope (LAN only).

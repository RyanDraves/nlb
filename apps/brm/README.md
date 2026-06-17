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
                          binary (browser guests). Transport: the `ws` crate
                          (native), brm_net.js (web).
  web/      index.html + macroquad's JS loader + the brm_net.js WebSocket plugin.
```

The server is authoritative: clients send `ClientMsg::Input`, the server steps
the sim and broadcasts `ServerMsg::Snapshot(GameState)` to everyone. Each local
player opens its own WebSocket, so the native client running two split-keyboard
players simply holds two connections.

## Controls (native client)

- Player 1: **WASD** to move, **Space** to drop a bomb.
- Player 2: **Arrow keys** to move, **Enter** to drop a bomb.
- **Controllers**: left stick or D-pad to move, **A / Cross** to drop a bomb.

**Controllers** work on both clients. On the native (couch) host, every plugged-in
controller becomes its own player, hot-plugged in and out at runtime (via gilrs).
In the browser, a connected gamepad drives the single web player (via the
Gamepad API). Controller players keep their default `Player N` name (you can't
type on a pad); the **A** button readies them up.

Browser/laptop guests without a controller use the same keyboard scheme as
Player 1. On a **touch device** the web client switches to on-screen controls: a
**floating joystick** (drag anywhere on the left half) to move and a **bomb
button** (lower right) to drop bombs — the bomb button also readies up in the
lobby. Name entry on touch uses a real HTML text field that raises the soft
keyboard when tapped.

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
  split-keyboard players against `ws://127.0.0.1:8080/ws`). Choose the keyboard
  count with `bazel run //apps/brm/client -- --players 1` (or `0`/`2`), and point
  elsewhere with `--server ws://host:port/ws` (`BRM_PLAYERS` / `BRM_SERVER` also
  work). Plugged-in **controllers** add players on top of the keyboard ones, so
  use `--players 0` for a controller-only session.
- **LAN guests**: open `http://<host-LAN-ip>:8080` in a browser on a laptop or
  phone on the same network. The page auto-connects back to the host.

Everyone names themselves in the lobby: press **E** to edit (or tap the name
field on a phone), type (15 char max), then press your action key — or the
on-screen bomb button — to confirm and ready up. Players are named in turn (the
first not-yet-ready one takes typed input), so the host keyboard also names the
**controller** players, who can't type for themselves; finish a controller's name
with **E**, then ready it up with **A**.

On the native client, the lobby shows a menu line with the number of connected
controllers and the active **keyboard-player count — press 0, 1, or 2** to change
it on the fly (controllers are players on top of these).

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
- The native client depends on **gilrs** for controllers (a `cfg(not(wasm))`
  dependency; the wasm client uses the browser Gamepad API instead). gilrs reads
  joysticks via the OS — on Linux that needs `libudev` available at build/run
  time (already present on macOS). The native `client` target is `manual`, so it
  isn't part of `bazel build //apps/brm/...` and won't break wildcard builds on a
  host without it.

### Web assets

macroquad's wasm uses its own JS loader (not wasm-bindgen). `web/` holds:

- `mq_js_bundle.js`: vendored verbatim from the macroquad 0.4.15 crate (matches
  miniquad 0.4.10); the only change is `preserveDrawingBuffer:true` so the canvas
  can be screenshotted.
- `brm_net.js`: a small first-party WebSocket plugin implementing the `brm_ws_*`
  imports from `client/src/net.rs` (plus touch/name/gamepad bridges). It talks to
  the browser WebSocket via raw `wasm_memory` and resolves the relative `/ws` path
  against the page origin (so LAN guests connect back to the host).

The native client runs the `ws` crate's event loop on a background thread per
connection (see `client/src/net.rs`). We replaced the abandoned `quad-net`:
its wasm side needed a sapp_jsutils API current macroquad dropped, and its native
handler `unwrap()`s a channel send in `on_message`, so dropping a socket (e.g. a
controller unplugging) panicked its still-running thread. Our handler ignores a
closed receiver and shuts the loop down cleanly on `Drop`.

## Verifying in a browser

`.claude/launch.json` defines a `brm` preview server that runs
`bazel run //apps/brm:serve`. With it up, the wasm client boots, connects over
WebSocket, and renders the map fed by live 30 Hz snapshots.

## Power-ups

Destroyed blocks may reveal a power-up (`POWERUP_CHANCE`). Six kinds, drawn from
the embedded sprite sheet `assets/powerups.png`: **ExtraBomb**, **Range**,
**Speed**, **Kick** (push bombs by walking into them), **Pierce** (your bombs'
blast punches through blocks), and **Shield** (absorb one otherwise-fatal blast).

The sheet is generated by `assets/gen_powerups.py` (pure standard-library pixel
art, no pip installs) — edit the icon functions and rerun `python3
gen_powerups.py` (add `--preview` for an 8× zoom) to redraw, then rebuild.

## Visuals

The board is drawn procedurally in `client/src/render.rs` for a pixel-art 2.5D
look — beveled walls and plank crates with front faces, a tiled floor, lit-fuse
bombs, flickering flames, and characters that face their movement direction and
play a walk cycle (facing/animation state is tracked render-side in `Assets`,
since snapshots only carry positions). Power-up icons are the one bitmap asset
(`assets/powerups.png`).

## Not done yet (fast-follows)

Audio (SFX + music) and optional hand-drawn art to replace the procedural board
are the next steps; client-side snapshot interpolation would smooth motion
between the 30 Hz ticks. Internet/NAT play is out of scope (LAN only).

# Punbox carrier bringup

Per-board bringup procedure for the v1 JLCPCB-assembled carriers, run with
[TofuPilot](https://www.tofupilot.com/docs)'s native framework. It walks an
operator through DESIGN.md's bring-up plan — visual inspection, short check,
Pico soldering, provisioning, flashing, and the functional checks — and
records every measurement per unit serial.

## One-time setup

The TofuPilot CLI is a standalone binary:

```sh
curl -fsSL https://tofupilot.sh/install | sh
tofupilot login
```

## Running a board

From the repo root, with the multimeter handy and the board NOT yet
connected:

```sh
tofupilot run emb/project/punbox/bringup
```

The operator UI opens in the browser and walks through the phases in order.
Automated phases (`provision`, `flash_punbox`, `hil_test`, the button
verification) shell out to the repo's Bazel targets via `plugs.py`; keep
exactly one board plugged in at a time (`PicoSerial` grabs the first
`2e8a:000a` USB device it finds).

## Files

- `procedure.yaml`: phase sequence, operator UI components, measurements
  and pass/fail validators
- `phases.py`: phase implementations (framework injects `ui`,
  `measurements`, `phase`, `logs`, and plugs by parameter name)
- `plugs.py`: the Bazel runner plug

Note the concurrency rule that shaped the phase list: a phase's Python runs
*concurrently* with its operator UI, so "instruct the operator, then check
the result" is always two phases (e.g. `button_baseline` → `button_press` →
`button_verify`).

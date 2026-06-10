# Punbox

A small USB-powered box: tell a pun, press the button on top, and a
"buh dum tsss" plays through the speakers.

## Development hardware

- Raspberry Pi Pico (RP2040)
- [Waveshare Pico-Audio](https://www.waveshare.com/pico-audio.htm) (original
  revision): PCM5101A I2S DAC + APA2068 speaker amp
- 8Ω 2W speakers
- Momentary pushbutton

### Pinout

| Signal | GPIO | Notes |
| --- | --- | --- |
| I2S DIN | GP26 | Wired by the Pico-Audio module |
| I2S BCK | GP27 | Wired by the Pico-Audio module |
| I2S LRCK | GP28 | Wired by the Pico-Audio module |
| Button | GP6 | Active-low against an internal pull-up; other leg to GND |

## Architecture

- `logic.{hpp,cc}`: `PunboxLogic`, the platform-free core (button debounce →
  clip playback). Unit-tested in `logic_test.cc`.
- `punbox.cc`: the buffham `Punbox` handlers (`play_sound`, `get_state`) plus
  `tick()`, a buffham `svr_method` the main loop calls to poll the button.
- `//emb/yaal:audio`: PIO + DMA I2S driver; clips stream from flash with no
  CPU involvement.
- `:rimshot`: the sound clip, embedded at build time by
  `//nlb/wav:wav2cc` as 16-bit stereo PCM (see `wav_cc_library`).

## Sound clip

`data/rimshot.wav`:

- Source: ["Ba Dum Tss! (classic edition)" by DJczyszy on Freesound](https://freesound.org/people/DJczyszy/sounds/431811/)
- License: CC0 1.0

## Flashing

Provision a fresh Pico (BOOTSEL mode) with the bootloader and base image:

```sh
bazel run //emb/project/bootloader:provision_pico
```

Then flash (and re-flash) punbox over USB serial:

```sh
bazel run //emb/project/punbox:punbox_flash
```

## Hardware smoke test

1. `bazel test //emb/project/punbox:hil_test` — pings the board, triggers
   playback, and verifies the state; the rimshot should play through the
   speakers (the target is tagged `manual`, so CI skips it)
2. Press the physical button — the rimshot should play again
3. Re-run `:hil_test` (or use `:shell` and `client.get_state()`) —
   `press_count` should reflect both the RPC triggers and the physical press

For interactive poking, `bazel run //emb/project/punbox:shell` opens an
IPython shell with `client` connected over USB serial.

## Tests

```sh
bazel test //emb/project/punbox/...   # unit + host integration tests
bazel test //nlb/wav/...              # clip embedding tool
```

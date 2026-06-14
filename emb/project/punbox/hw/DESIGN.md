# Punbox carrier board — design doc

A small 2-layer PCB that replaces the dev-bench stack (Pico + Waveshare
Pico-Audio + breakout board) with one board sized for the enclosure. The
firmware is **unchanged**: same I2S pins, same button pin.

Decisions locked (2026-06-12): JLCPCB SMT assembly, Pico soldered flat via
castellated pads, one 4-pin 1.25mm speaker connector (matches the Waveshare
2030 cavity speaker pair).

## Block diagram

```
                  ┌──────────────────────────────────────────┐
   USB cable ──►  │  Raspberry Pi Pico (soldered flat,       │
  (power+flash)   │  USB port hanging off the board edge)    │
                  └──┬───────────┬───────────┬───────────────┘
                     │ VBUS (5V) │ I2S       │ GP6 + GND
                     │           │ GP26 DIN  │
                     ▼           │ GP27 BCK  ▼
              5V rail            │ GP28 LRCK J3: button connector (JST PH 2-pin)
              (+ bulk cap)       │             → panel-mount button in the lid
                     │           ▼
            ┌────────┴───────────────────┐
            │                            │
   ┌────────▼─────────┐        ┌─────────▼────────┐
   │ U1 MAX98357A     │        │ U2 MAX98357A     │
   │ (strapped LEFT)  │        │ (strapped RIGHT) │
   └────────┬─────────┘        └─────────┬────────┘
            │ L+  L−                     │ R+  R−
            └──────────┬─────────────────┘
                       ▼
            J2: speaker connector (4-pin, 1.25mm pitch)
            → both speakers on the existing Waveshare harness
```

## Why a MAX98357A (and why two)

The dev setup uses the Pico-Audio's PCM5101A **DAC** (digital → line-level
analog) followed by an APA2068 **amplifier** (line-level → speaker power).
The MAX98357A collapses both jobs into one chip: it takes I2S digital audio
directly and drives a speaker with a Class-D output stage. One chip, four
passives, no analog signal routing to get wrong — ideal for a first board.

It's a **mono** amp: each chip outputs one channel. Two chips give us
left + right. Which channel a chip plays is set by a resistor "strap" on its
`SD_MODE` pin (details below), so both chips are identical parts placed
twice — the BOM stays tiny.

Power math: at 5V into our 8Ω speakers the MAX98357A delivers ~1.8W max,
which matches the speakers' 2W rating. Volume is also adjustable in firmware
(`wav_cc_library(gain_db = ...)`), so the analog gain can stay at a fixed,
safe default.

## Circuit walkthrough (net by net)

**Power.** The Pico's own USB port supplies everything: its `VBUS` pin
carries the raw 5V from the cable. We run a `5V` net from VBUS to both amps.
Decoupling (the capacitors that supply the chip's fast current spikes that
the long USB cable can't): one 100nF ceramic + one 10µF ceramic *right next
to* each amp's VDD pin, plus one ~100µF bulk capacitor on the 5V rail —
Class-D amps draw current in bursts at the audio rate, and the bulk cap
keeps the rail from sagging on loud hits. `GND` is a solid copper pour on
the bottom layer (standard 2-layer practice).

**I2S bus.** Three traces from the Pico to *both* amps in parallel:
`GP26 → DIN`, `GP27 → BCLK`, `GP28 → LRC`. Both amps hear the same data;
the SD_MODE strap decides which channel each one plays. These are ~1MHz
digital signals over a few centimeters — no special routing needed beyond
keeping them reasonably short and over the ground pour.

**Channel select straps (`SD_MODE`).** The chip reads a *voltage level* on
this pin at power-up (it has an internal 100kΩ pull-down, so an external
pull-up to 5V forms a voltage divider):

| External pull-up to 5V | Voltage at pin | Behavior |
| --- | --- | --- |
| none (pin grounded) | ~0V | shutdown |
| 1MΩ | ~0.45V | plays (L+R)/2 mono mix |
| 390kΩ | ~1.0V | plays RIGHT |
| 100kΩ | ~2.5V | plays LEFT |

U1 gets 100kΩ (left), U2 gets 390kΩ (right). Our rimshot is mono duplicated
into both channels so this doesn't matter *today*, but true L/R straps cost
the same two resistors and keep real stereo clips possible later.
**Verify these threshold bands against the MAX98357A datasheet during
schematic capture** — the table above is from memory + the Adafruit guide.

**Gain strap (`GAIN_SLOT`).** Left floating = 9dB, a sensible default for
2W/8Ω speakers on 5V (other strap options span 3–15dB if hardware testing
says otherwise). Floating means: no component. Nice.

**Speaker outputs.** Each amp has a bridge-tied (+/−) output pair that goes
straight to the connector — no coupling caps, no filters needed for the
~10cm of wire inside the box. J2 pinout matches the Waveshare 4-pin harness:
L+, L−, R+, R− (verify wire order against the actual harness with a
multimeter before finalizing — cheap insurance).

**Button.** J3 is a 2-pin JST PH (2.0mm — bigger than the speaker connector
on purpose: impossible to mix up, easy to buy pre-crimped pigtails). One pin
to `GP6`, one to `GND`. The firmware's internal pull-up does the rest, same
as the dev board.

**The Pico itself.** Its castellated edge pads solder to matching pads on
the carrier (the "module as a component" pattern). Place it so the USB
connector overhangs the board edge → the enclosure gets one USB cutout and
that port does power, flashing, and the serial shell. BOOTSEL stays
reachable (it's on top of the module) for bootloader recovery.

**Mechanical.** 4× M2.5 mounting holes for enclosure standoffs; target
roughly 55×45mm. Exact outline comes after parts are placed.

## Bill of materials

LCSC part numbers to be confirmed in the JLCPCB parts library at schematic
time ("Basic" parts avoid the $3/part feeder fee; the amp and connector will
be "Extended").

| Ref | Part | Package | Qty | Note |
| --- | --- | --- | --- | --- |
| U1, U2 | MAX98357AETE+T | TQFN-16 | 2 | I2S Class-D amp (Extended) |
| C1, C2 | 100nF ceramic | 0603 | 2 | per-amp decoupling (Basic) |
| C3, C4 | 10µF ceramic | 0805 | 2 | per-amp decoupling (Basic) |
| C5 | 100µF | electrolytic/polymer | 1 | 5V bulk |
| R1 | 100kΩ | 0603 | 1 | U1 SD_MODE strap → LEFT |
| R2 | 390kΩ | 0603 | 1 | U2 SD_MODE strap → RIGHT |
| J2 | 4-pin 1.25mm wafer, vertical | SMT | 1 | speaker harness |
| J3 | JST PH 2-pin, vertical | THT | 1 | button pigtail |
| A1 | Raspberry Pi Pico | castellated module | 1 | hand-soldered after assembly |

Hand-assembly per board: solder the Pico (8–10 castellated pads actually
used; tack the corners first), and J3 if we keep it through-hole.

## KiCad crash course (the flow we'll follow)

KiCad separates *what's connected* from *where things go*:

1. **Schematic** (`.kicad_sch`, the Eeschema editor): place **symbols**
   (abstract chip drawings), draw wires, name nets. This captures the
   circuit above. Run **ERC** (electrical rule check) — catches unconnected
   pins, missing power, etc.
2. **Footprint assignment**: map each symbol to a **footprint** (the real
   copper pad pattern — e.g. "TQFN-16 3x3mm"). The Pico has a ready-made
   module footprint in KiCad's library (`RPi_Pico_SMD_TH`).
3. **PCB layout** (`.kicad_pcb`, the Pcbnew editor): pull in the netlist,
   place footprints, route copper traces, pour the ground plane. Run
   **DRC** (design rule check) against JLCPCB's manufacturing limits.
4. **Outputs**: gerbers + drill file (the fab's input), BOM + CPL/placement
   file (the assembly input), and a **STEP** 3D model (`kicad-cli pcb
   export step`) that imports straight into Onshape for the enclosure.

Steps 1–3 are interactive in the KiCad GUI; step 4 is scriptable with
`kicad-cli`, which is what the CI job will run (ERC + DRC as tests,
gerber/BOM/CPL/STEP as build artifacts).

## Bring-up plan (per assembled board)

1. Inspect solder joints; check 5V↔GND for shorts with a multimeter.
2. Solder the Pico; plug in USB → BOOTSEL drive appears.
3. `bazel run //emb/project/bootloader:provision_pico`
4. `bazel run //emb/project/punbox:punbox_flash`
5. `bazel test //emb/project/punbox:hil_test` → rimshot through the real
   speakers, button press counts.

Same firmware, same tools, same test as the dev board — that's the payoff
of keeping the pinout identical.

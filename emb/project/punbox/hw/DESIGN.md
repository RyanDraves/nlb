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
(Threshold bands verified against the MAX98357A datasheet: shutdown <0.16V,
mono mix 0.16–0.77V, right 0.77–1.4V, left >1.4V. `punbox_test.py` asserts
the divider math lands inside these bands.)

**Gain strap (`GAIN_SLOT`).** Left floating = 9dB, a sensible default for
2W/8Ω speakers on 5V (other strap options span 3–15dB if hardware testing
says otherwise). Floating means: no component. Nice.

**Speaker outputs.** Each amp has a bridge-tied (+/−) output pair that goes
straight to the connector — no coupling caps, no filters needed for the
~10cm of wire inside the box. J2 pinout matches the Waveshare 4-pin harness:
L+, L−, R+, R− (verify wire order against the actual harness with a
multimeter before finalizing — cheap insurance).

**Button.** J3 is a 2-pin JST XH (2.5mm — bigger than the speaker
connector on purpose: impossible to mix up). One pin to `GP6`, one to `GND`;
the firmware's internal pull-up does the rest. The whole button chain is
solderless: J3 (machine-assembled) → Adafruit 1152 quick-connect wire pair →
Adafruit 1503 16mm panel button's lugs.

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

**Assembled by JLCPCB** (in the fab BOM/CPL; LCSC numbers live in
`punbox.py`'s `LCSC` table):

| Ref | Part | Package | Qty | Note |
| --- | --- | --- | --- | --- |
| U1, U2 | MAX98357AETE+T | TQFN-16 | 2 | C910544 (Extended) |
| C1, C2 | 100nF ceramic X7R ≥16V | 0603 | 2 | C14663 (Basic) |
| C3, C4 | 10µF ceramic X5R 25V | 0805 | 2 | C15850 (Basic) |
| C5 | 100µF 16V | SMD electrolytic 6.3×5.4 | 1 | C970684 |
| R1 | 100kΩ | 0603 | 1 | C25803 (Basic); U1 strap → LEFT |
| R2 | 390kΩ | 0603 | 1 | C23150 (Basic); U2 strap → RIGHT |
| J2 | Molex 53398-0471 (genuine) | 1.25mm 4P vertical SMT | 1 | C17617036; speaker harness |
| J3 | JST B2B-XH-A (genuine) | XH 2.5mm 2P vertical THT | 1 | C158012; button pigtail socket (THT: JLC hand-solders it) |

**Hand-soldered** (excluded from the fab BOM/CPL — no `lcsc` attribute):

| Ref | Part | Note |
| --- | --- | --- |
| A1 | Raspberry Pi Pico | tack the corner castellations first |

**Off-board shopping list** (not on the PCB; order from LCSC in the same
checkout, or elsewhere):

| Part | Qty/box | Source | Note |
| --- | --- | --- | --- |
| Panel button: Adafruit 1503 (16mm momentary, burgundy) | 1 | adafruit.com/product/1503 | mounts in the lid; $0.95 |
| Wire pair: Adafruit 1152 (10-pack) | 1 pack total | adafruit.com/product/1152 | JST 2.5mm plug mates with J3; quick-connects slide onto the 1503's lugs — no soldering anywhere in the button chain |
| Waveshare 2030 speaker pair (4-pin 1.25mm harness) | 1 | Waveshare/Amazon | already owned for dev; buy per box |
| M2.5 screws + standoffs for the mounting holes | 4 | Amazon | length depends on enclosure |

## Layout placement guide

The netlist can't express *pairing* on shared nets (any way of connecting a
net is electrically identical), so the intended clusters are recorded here.
Place clusters first; route signals second; do GND/+5V with zones, not
traces.

| Cluster | Parts | Placement intent |
| --- | --- | --- |
| Left amp | U1 + C1 (100nF) + C3 (10µF) + R1 | Caps against U1's VDD pins (7, 8), 100nF closest; R1 anywhere nearby |
| Right amp | U2 + C2 (100nF) + C4 (10µF) + R2 | Same, mirrored |
| Bulk | C5 | Between the Pico's VBUS pin and the amps |
| Speakers | J2 | Near both amps' OUTP/OUTN, at a board edge for the harness |
| Button | J3 | Any edge convenient for the lid pigtail |
| Pico | A1 | USB connector overhanging a board edge |

- Bottom layer: one GND zone over the whole board. Top: route signals; a
  small +5V zone (or a wide, ≥0.5mm trace) feeds C5 → both amps.
- Net classes: only `+5V` belongs to the Power class (0.5mm tracks). GND is
  *not* in it — GND connects through zones and short stubs-to-vias, and a
  netclass width would make DRC reject those stubs.
- The amps' thermal pads (pin 17, the big center pad) each get one via, dead
  center, into the bottom GND zone — both their ground connection and their
  heatsink. (The EP is only 1.23×1.23mm; a standard 0.6mm via fits singly,
  not as a grid.) Set the pad's zone connection to Solid, not thermal
  relief. The perimeter GND pins (3, 11, 15) just need any nearby path to
  GND; the NC pins (5, 6, 12, 13) stay unconnected.
- Keep each OUTP/OUTN pair routed side-by-side (they're a differential-ish
  Class-D pair; ~0.4mm width for the ~1A peaks).

## The SKiDL workflow (code-first, no graphical schematic)

Connectivity is code: `punbox.py` declares the parts and nets above using
[SKiDL](https://github.com/devbisme/skidl), with footprints assigned inline
and pin numbers imported from `punbox_bh` (generated from `punbox.bh`) so
firmware and hardware share one source of truth. `punbox_test.py` replaces
the graphical schematic review: ERC plus assertions on every net (I2S
reaching both amps, strap divider voltages landing in the datasheet bands,
decoupling on the rail, connector pinouts).

The loop:

1. Edit `punbox.py` → `bazel test //emb/project/punbox/hw:punbox_test`
2. `bazel run //emb/project/punbox/hw:netlist` → writes `punbox.net`
3. In the KiCad PCB editor: **File → Import Netlist** → pick `punbox.net`.
   Existing placement and routing survive re-imports; new/changed nets show
   up as fresh ratsnest lines.
4. Place footprints, route traces, pour the ground plane, and run **DRC**
   (design rule check) against JLCPCB's manufacturing limits — this part is
   interactive in the GUI and stays the human's job.
5. Outputs (manual, once the layout settles):
   `bazel run //emb/project/punbox/hw:fab` generates `fab/punbox_bom.csv` +
   `fab/punbox_cpl.csv` (JLCPCB assembly), `fab/punbox_gerbers.zip` (the
   fab), and `punbox.step` (the Onshape enclosure model). The BOM comes from
   the SKiDL design's `LCSC` table; parts without an LCSC number (the Pico,
   J3) are hand-soldered and excluded from both the BOM and CPL. Off-board
   parts (speakers, panel button, screws) are a shopping list, not a fab
   BOM — see the bill of materials section above.

Vendored symbols/footprints/3D models live in `lib/` (see `lib/NOTICE.md`);
`sym-lib-table`/`fp-lib-table` register them for the KiCad GUI, and
`punbox.py` points SKiDL at the same files — the design has no dependency
on the machine's installed KiCad libraries.

## Bring-up plan (per assembled board)

1. Inspect solder joints; check 5V↔GND for shorts with a multimeter.
2. Solder the Pico; plug in USB → BOOTSEL drive appears.
3. `bazel run //emb/project/bootloader:provision_pico`
4. `bazel run //emb/project/punbox:punbox_flash`
5. `bazel test //emb/project/punbox:hil_test` → rimshot through the real
   speakers, button press counts.

Same firmware, same tools, same test as the dev board — that's the payoff
of keeping the pinout identical.

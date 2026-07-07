"""SKiDL design for the punbox carrier board.

`DESIGN.md` is the narrative version of this circuit. Pin assignments are
imported from `punbox.bh` so the firmware and hardware always agree.

Run `bazel run //emb/project/punbox/hw:netlist` to generate `punbox.net` for
import into the KiCad PCB editor (File -> Import Netlist).
"""

import builtins
import pathlib

import skidl

from emb.project.punbox import punbox_bh

LIB_DIR = pathlib.Path(__file__).parent / 'lib'

# Vendored footprints; see `lib/NOTICE.md`
FP_AMP = 'punbox_parts:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm'
FP_R = 'punbox_parts:R_0603_1608Metric'
FP_C_100N = 'punbox_parts:C_0603_1608Metric'
FP_C_10U = 'punbox_parts:C_0805_2012Metric'
FP_C_BULK = 'punbox_parts:CP_Elec_6.3x5.4'
FP_SPEAKER = 'punbox_parts:Molex_PicoBlade_53398-0471_1x04-1MP_P1.25mm_Vertical'
FP_BUTTON = 'punbox_parts:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical'
FP_PICO = 'punbox_parts:RPi_Pico_SMD_TH'

# MAX98357A SD_MODE channel-select straps: the chip has an internal 100k
# pull-down, so a pull-up to 5V forms a divider read at power-up.
# >1.4V selects LEFT; 0.77-1.4V selects RIGHT (MAX98357A datasheet).
#   100k -> 5V * 100/200 = 2.5V  (left)
#   390k -> 5V * 100/490 = 1.02V (right)
SD_MODE_PULLUPS = {'left': '100k', 'right': '390k'}


def circuit() -> skidl.Circuit:
    """The SKiDL default circuit (injected into builtins by skidl)."""
    return builtins.default_circuit  # type: ignore


def pico_pin(gpio: int) -> str:
    """Map a GPIO number to the Pico symbol's pin name."""
    if gpio >= 26:
        return f'GPIO{gpio}_ADC{gpio - 26}'
    return f'GPIO{gpio}'


def build() -> None:
    """Build the punbox carrier circuit into SKiDL's default circuit."""
    skidl.set_default_tool(skidl.KICAD)
    skidl.lib_search_paths[skidl.KICAD] = [str(LIB_DIR)]

    five_v = skidl.Net('+5V')
    gnd = skidl.Net('GND')
    five_v.drive = skidl.POWER
    gnd.drive = skidl.POWER

    # The Pico's USB port is the power source: VBUS carries the cable's 5V
    pico = skidl.Part('MCU_RaspberryPi_and_Boards', 'Pico', ref='A1', footprint=FP_PICO)
    five_v += pico['VBUS']
    gnd += pico['GND']

    # 5V bulk capacitance for Class-D current bursts
    bulk = skidl.Part(
        'punbox_parts', 'C_Polarized', ref='C5', value='100uF', footprint=FP_C_BULK
    )
    five_v += bulk[1]
    gnd += bulk[2]

    # I2S bus, shared by both amps
    i2s_din = skidl.Net('I2S_DIN')
    i2s_bclk = skidl.Net('I2S_BCLK')
    i2s_lrclk = skidl.Net('I2S_LRCLK')
    i2s_din += pico[pico_pin(punbox_bh.I2S_DATA_PIN)]
    i2s_bclk += pico[pico_pin(punbox_bh.I2S_CLOCK_PIN_BASE)]
    i2s_lrclk += pico[pico_pin(punbox_bh.I2S_CLOCK_PIN_BASE + 1)]

    # Button pigtail: GP6 + GND; the firmware enables an internal pull-up
    button = skidl.Part(
        'punbox_parts', 'Conn_01x02', ref='J3', value='Button', footprint=FP_BUTTON
    )
    button_net = skidl.Net('BUTTON')
    button_net += pico[pico_pin(punbox_bh.BUTTON_PIN)], button[1]
    gnd += button[2]

    # Speaker harness (Waveshare 2030 pair): L+, L-, R+, R-
    speakers = skidl.Part(
        'punbox_parts', 'Conn_01x04', ref='J2', value='Speakers', footprint=FP_SPEAKER
    )

    amps = {
        'left': ('U1', 'C1', 'C3', 'R1', speakers[1], speakers[2]),
        'right': ('U2', 'C2', 'C4', 'R2', speakers[3], speakers[4]),
    }
    for channel, (amp_ref, c100n_ref, c10u_ref, r_ref, out_p, out_n) in amps.items():
        amp = skidl.Part('punbox_parts', 'MAX98357A', ref=amp_ref, footprint=FP_AMP)

        five_v += amp['VDD']  # pins 7 and 8
        gnd += amp['GND'], amp['PAD']

        i2s_din += amp['DIN']
        i2s_bclk += amp['BCLK']
        i2s_lrclk += amp['LRCLK']

        # GAIN_SLOT floats: 9dB, a safe default for the 2W/8ohm speakers.
        # Clip volume is tuned in firmware (`wav_cc_library(gain_db = ...)`).
        amp['GAIN_SLOT'] += circuit().NC

        # Per-amp decoupling, placed against the VDD pins in layout
        for cap_ref, value, footprint in (
            (c100n_ref, '100nF', FP_C_100N),
            (c10u_ref, '10uF', FP_C_10U),
        ):
            cap = skidl.Part(
                'punbox_parts', 'C', ref=cap_ref, value=value, footprint=footprint
            )
            five_v += cap[1]
            gnd += cap[2]

        # Channel-select strap (pin 4, ~{SD_MODE})
        strap = skidl.Part(
            'punbox_parts',
            'R',
            ref=r_ref,
            value=SD_MODE_PULLUPS[channel],
            footprint=FP_R,
        )
        sd_mode = skidl.Net(f'{amp_ref}_SD_MODE')
        sd_mode += amp[4], strap[1]
        five_v += strap[2]

        # Bridge-tied Class-D outputs straight to the connector
        out_p += amp['OUTP']
        out_n += amp['OUTN']

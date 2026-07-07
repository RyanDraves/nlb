import unittest

import skidl

from emb.project.punbox import punbox_bh
from emb.project.punbox.hw import punbox


def _part(ref: str):
    return next(part for part in punbox.circuit().parts if part.ref == ref)


def _pins_on(net_name: str) -> set[tuple[str, str]]:
    """Set of (part ref, pin number) attached to a net, across net segments."""
    net = next(net for net in punbox.circuit().get_nets() if net.name == net_name)
    return {(pin.part.ref, pin.num) for pin in net.pins}


class PunboxDesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        skidl.reset()
        punbox.build()

    def test_erc_clean(self):
        skidl.ERC()
        self.assertEqual(skidl.erc_logger.error.count, 0)

    def test_i2s_bus_reaches_both_amps(self):
        # The bh constants are the source of truth for the Pico pins
        din = _pins_on('I2S_DIN')
        self.assertIn(('U1', '1'), din)
        self.assertIn(('U2', '1'), din)

        pico_pins = {
            pin.num
            for pin in _part('A1').pins
            if pin.nets and pin.nets[0].name == 'I2S_DIN'
        }
        expected = {
            pin.num
            for pin in _part('A1').pins
            if pin.name == punbox.pico_pin(punbox_bh.I2S_DATA_PIN)
        }
        self.assertEqual(pico_pins, expected)

        self.assertIn(('U1', '16'), _pins_on('I2S_BCLK'))
        self.assertIn(('U2', '16'), _pins_on('I2S_BCLK'))
        self.assertIn(('U1', '14'), _pins_on('I2S_LRCLK'))
        self.assertIn(('U2', '14'), _pins_on('I2S_LRCLK'))

    def test_button_wired_to_bh_pin(self):
        button = _pins_on('BUTTON')
        self.assertIn(('J3', '1'), button)

        pico = _part('A1')
        expected_pin_name = punbox.pico_pin(punbox_bh.BUTTON_PIN)
        pico_button_pins = [
            pin for pin in pico.pins if ('A1', pin.num) in button and pin.num != '0'
        ]
        self.assertEqual(len(pico_button_pins), 1)
        self.assertEqual(pico_button_pins[0].name, expected_pin_name)

    def test_channel_straps(self):
        # Internal 100k pull-down divider: >1.4V = left, 0.77-1.4V = right
        for amp_ref, strap_ref, value, min_v, max_v in (
            ('U1', 'R1', '100k', 1.4, 5.0),
            ('U2', 'R2', '390k', 0.77, 1.4),
        ):
            strap = _part(strap_ref)
            self.assertEqual(strap.value, value)

            sd_mode = _pins_on(f'{amp_ref}_SD_MODE')
            self.assertIn((amp_ref, '4'), sd_mode)
            self.assertIn((strap_ref, '1'), sd_mode)

            pullup_ohms = float(value.replace('k', '')) * 1000
            divider_v = 5.0 * 100_000 / (100_000 + pullup_ohms)
            self.assertGreater(divider_v, min_v)
            self.assertLessEqual(divider_v, max_v)

    def test_amp_power_and_decoupling(self):
        five_v = _pins_on('+5V')
        gnd = _pins_on('GND')

        for amp_ref in ('U1', 'U2'):
            # Both VDD pins powered; all GND pins and the thermal pad grounded
            self.assertIn((amp_ref, '7'), five_v)
            self.assertIn((amp_ref, '8'), five_v)
            for gnd_pin in ('3', '11', '15', '17'):
                self.assertIn((amp_ref, gnd_pin), gnd)

        # Decoupling and bulk caps across the rail
        for cap_ref in ('C1', 'C2', 'C3', 'C4', 'C5'):
            self.assertIn((cap_ref, '1'), five_v)
            self.assertIn((cap_ref, '2'), gnd)

        # The Pico feeds the rail from its USB VBUS
        self.assertIn(('A1', '40'), five_v)

    def test_speaker_connector_pinout(self):
        # J2: L+, L-, R+, R- (matches the Waveshare harness)
        connections = {
            ('U1', '9'): ('J2', '1'),  # left OUTP
            ('U1', '10'): ('J2', '2'),  # left OUTN
            ('U2', '9'): ('J2', '3'),  # right OUTP
            ('U2', '10'): ('J2', '4'),  # right OUTN
        }
        for amp_pin, conn_pin in connections.items():
            nets = [
                {(pin.part.ref, pin.num) for pin in net.pins}
                for net in punbox.circuit().get_nets()
            ]
            joined = [net for net in nets if amp_pin in net]
            self.assertEqual(len(joined), 1)
            self.assertIn(conn_pin, joined[0])

    def test_netlist_generation(self):
        netlist = skidl.generate_netlist()
        self.assertIn('MAX98357A', netlist)
        self.assertIn('RPi_Pico_SMD_TH', netlist)


if __name__ == '__main__':
    unittest.main()

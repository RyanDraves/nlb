"""Hardware-in-the-loop test: requires a punbox board connected over USB.

Run manually with:
    bazel test //emb/project/punbox:hil_test
"""

import unittest

from emb.network.transport import usb
from emb.project.punbox import client
from emb.project.punbox import punbox_bh


class HilTest(unittest.TestCase):
    def setUp(self) -> None:
        transporter = usb.PicoSerial()
        self.client = client.PunboxClient(
            punbox_bh.PunboxNode(
                comms_transporter=transporter, log_transporter=transporter
            )
        )

    def test_ping(self):
        with self.client:
            self.client.base.ping()

    def test_play_sound(self):
        with self.client:
            initial = self.client.get_state()

            state = self.client.play_sound()
            self.assertEqual(state.press_count, initial.press_count + 1)
            self.assertEqual(state.playing, 1)

            state = self.client.get_state()
            self.assertEqual(state.press_count, initial.press_count + 1)

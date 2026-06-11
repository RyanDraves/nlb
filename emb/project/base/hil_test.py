"""Hardware-in-the-loop test: requires a provisioned board connected over USB.

Any image extending the base project works (e.g. punbox).

Run manually with:
    bazel test //emb/project/base:hil_test
"""

import time
import unittest

from emb.network.transport import usb
from emb.project.base import base_bh
from emb.project.base import client


class HilTest(unittest.TestCase):
    def setUp(self) -> None:
        transporter = usb.PicoSerial()
        self.client = client.BaseClient(
            base_bh.BaseNode(
                comms_transporter=transporter, log_transporter=transporter
            )
        )

    def test_ping(self):
        with self.client:
            self.client.ping()

    def test_reset_reconnect(self):
        """The client should ride through a device reset on the same connection."""
        with self.client:
            self.client.ping()
            self.client.reset()

            # The device drops off the bus and re-enumerates (twice: once
            # for the bootloader, once for the application); the transport
            # reconnects in the background
            deadline = time.monotonic() + 30.0
            while True:
                try:
                    self.client.ping()
                    break
                except (TimeoutError, OSError):
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.5)

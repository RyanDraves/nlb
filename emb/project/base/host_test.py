import os
import pathlib
import random
import subprocess
import tempfile
import unittest

from emb.network.transport import tcp
from emb.project.base import base_bh
from emb.project.base import client
from emb.project.bootloader import bootloader_bh


class HostTest(unittest.TestCase):

    def setUp(self) -> None:
        host_bin = pathlib.Path(os.environ['HOST_BIN'])

        self.host = subprocess.Popen(
            [str(host_bin)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.addCleanup(self.host.terminate)

        self.node = base_bh.BaseNode(transporter=tcp.Zmq(tcp.Zmq.DEFAULT_ADDRESS))
        self.client = client.BaseClient(self.node)

        # Generate a random file a little over 16kB
        self.image = pathlib.Path(tempfile.mktemp())
        # Make it deterministic
        random.seed(0)
        with self.image.open('wb') as f:
            for _ in range(16):
                # Write a little over 1kB
                f.write(bytes([random.randint(0, 255) for _ in range(1024 + 4)]))

    def test_ping(self):
        with self.client:
            self.client.ping()

    def test_read_write_flash(self):
        with self.client:
            # Tell the firmware we're on side 0
            self.client.write_system_page(
                page=bootloader_bh.SystemFlashPage(boot_side=0, boot_count=1)
            )

            self.client.write_flash_image(self.image, swap_boot_side=False)

            outpath = pathlib.Path(tempfile.mktemp())
            self.client.read_flash_image(outpath, read_size=self.image.stat().st_size)

            self.assertEqual(outpath.stat().st_size, self.image.stat().st_size)
            self.assertEqual(outpath.read_bytes(), self.image.read_bytes())

    def test_flash_sector(self):
        with self.client:
            self.client.write_system_page(
                bootloader_bh.SystemFlashPage(boot_side=1, boot_count=123)
            )

            resp = self.client.read_system_page()

        self.assertEqual(resp.boot_side, 1)
        self.assertEqual(resp.boot_count, 123)

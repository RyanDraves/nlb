import pathlib
import random
import tempfile

from emb.project import host_test_base
from emb.project.base import base_bh
from emb.project.base import client
from emb.project.bootloader import bootloader_bh


class HostTest(host_test_base.HostTestBase[client.BaseClient, base_bh.BaseNode]):
    CLIENT_CLS = client.BaseClient
    NODE_CLS = base_bh.BaseNode

    def setUp(self) -> None:
        super().setUp()

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
                page=bootloader_bh.SystemFlashPage(
                    boot_count=1,
                    image_size_a=self.image.stat().st_size,
                    image_size_b=0,
                    new_image_flashed=0,
                )
            )

            self.client.write_flash_image(self.image)

            outpath = pathlib.Path(tempfile.mktemp())
            self.client.read_flash_image(
                outpath, boot_side=1, read_size=self.image.stat().st_size
            )

            self.assertEqual(outpath.stat().st_size, self.image.stat().st_size)
            self.assertEqual(outpath.read_bytes(), self.image.read_bytes())

            system_page = self.client.read_system_page()
            self.assertEqual(system_page.image_size_b, self.image.stat().st_size)
            self.assertEqual(system_page.new_image_flashed, 1)

    def test_flash_sector(self):
        with self.client:
            self.client.write_system_page(
                bootloader_bh.SystemFlashPage(
                    boot_count=123, image_size_a=0, image_size_b=0, new_image_flashed=0
                )
            )

            resp = self.client.read_system_page()

        self.assertEqual(resp.boot_count, 123)
        self.assertEqual(resp.image_size_a, 0)
        self.assertEqual(resp.image_size_b, 0)
        self.assertEqual(resp.new_image_flashed, 0)

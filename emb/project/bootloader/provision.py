"""Provision a Pico board with a bootloader and base image."""

import pathlib
import struct
import subprocess
import sys
import tempfile

import rich_click as click

from emb.network.transport import usb
from emb.project.base import base_bh
from emb.project.base import client
from emb.project.bootloader import bootloader_bh
from nlb.util import console_utils


@click.command()
@click.argument(
    'bootloader_path',
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
@click.argument(
    'base_image_path',
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
@click.argument(
    'picotool_path',
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
def main(
    bootloader_path: pathlib.Path,
    base_image_path: pathlib.Path,
    picotool_path: pathlib.Path,
) -> None:
    console = console_utils.Console()

    c = client.BaseClient(base_bh.BaseNode(transporter=usb.PicoSerial()))
    try:
        with c:
            console.error('Board is already provisioned')
            exit(1)
    except RuntimeError:
        # Correct behavior
        pass

    console.info('Flashing bootloader')
    result = subprocess.run(
        [str(picotool_path), 'load', str(bootloader_path)],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    if result.returncode:
        console.error('Failed to flash bootloader. Did you press the BOOTSEL button?')
        exit(1)

    console.info('Flashing base image')
    subprocess.run(
        [
            str(picotool_path),
            'load',
            str(base_image_path),
            '--offset',
            hex(bootloader_bh.PICO_FLASH_BASE_ADDR + bootloader_bh.PICO_APP_ADDR_A),
        ],
        check=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    console.info('Writing system page')
    init_system_page = bootloader_bh.SystemFlashPage(
        boot_count=0,
        image_size_a=base_image_path.stat().st_size,
        image_size_b=0,
        new_image_flashed=False,
    )
    with tempfile.NamedTemporaryFile() as temp_file:
        buffer = bytes()
        serialized = init_system_page.serialize()
        # Write the size of the serialized data as the first 2 bytes of the buffer
        buffer += struct.pack('<H', len(serialized))
        buffer += serialized
        temp_file.write(buffer)
        temp_file.flush()
        subprocess.run(
            [
                str(picotool_path),
                'load',
                temp_file.name,
                '-t',
                'bin',
                '--offset',
                hex(
                    bootloader_bh.PICO_FLASH_BASE_ADDR
                    + bootloader_bh.PICO_SCRATCHPAD_ADDR
                ),
            ],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    console.success(
        'Provisioning complete. Power cycle the board to boot the new image.'
    )


if __name__ == '__main__':
    main()

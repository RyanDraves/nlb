import logging
import pathlib
import time

import rich_click as click
import serial
from rich import progress

from emb.network.transport import usb
from emb.project import shell
from emb.project.base import base_bh
from emb.project.base import client
from emb.project.bootloader import bootloader_bh
from emb.project.bootloader import stamp


def _watch_bootloader_progress(timeout_s: float = 120.0) -> None:
    """Follow the bootloader's image swap over its USB serial output.

    Best-effort: if the bootloader's port never enumerates (e.g. an older
    bootloader without serial output), fall through to the reconnect poll.
    """
    port = usb.wait_for_port(usb.PicoSerial.VENDOR_PRODUCT_ID, timeout_s=10.0)
    if port is None:
        logging.warning('Bootloader port never showed up; waiting for the app')
        return

    deadline = time.monotonic() + timeout_s
    try:
        with (
            serial.Serial(port, usb.PicoSerial.BAUD_RATE, timeout=1) as ser,
            progress.Progress() as progress_bar,
        ):
            task = progress_bar.add_task('Swapping image banks', total=None)
            while time.monotonic() < deadline:
                line = ser.readline().decode('ascii', errors='replace').strip()
                if line == 'DONE':
                    return
                if line.startswith('FLASH '):
                    _, done, total = line.split()
                    progress_bar.update(task, completed=int(done), total=int(total))
    except (OSError, serial.SerialException):
        # The bootloader finished and jumped to the application, dropping
        # the port mid-read
        return


def _reconnect(timeout_s: float = 60.0) -> client.BaseClient:
    """Reconnect to the application after the bootloader hands off to it."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        port = usb.wait_for_port(
            usb.PicoSerial.VENDOR_PRODUCT_ID, timeout_s=deadline - time.monotonic()
        )
        if port is None:
            break

        transporter = usb.PicoSerial(port)
        c = client.BaseClient(
            base_bh.BaseNode(comms_transporter=transporter, log_transporter=transporter)
        )
        try:
            c.__enter__()
            c.ping()
            return c
        except (TimeoutError, RuntimeError, serial.SerialException):
            # Not up yet (or we raced the bootloader's port); try again
            c.__exit__(None, None, None)
            time.sleep(0.5)

    raise click.ClickException('Device did not come back up after reset')


def _verify(
    c: client.BaseClient,
    bin_filepath: pathlib.Path,
    old_page: bootloader_bh.SystemFlashPage,
) -> None:
    """Check that the device actually booted into the image we sent."""
    page = c.read_system_page()
    expected_hash = stamp.compute_hash(bin_filepath.read_bytes())

    failures = []
    if page.new_image_flashed:
        failures.append('Bootloader did not apply the new image')
    if page.image_size_a != bin_filepath.stat().st_size:
        failures.append(
            f'Image size mismatch: bank A holds {page.image_size_a} bytes, '
            f'sent {bin_filepath.stat().st_size}'
        )
    if page.boot_count != old_page.boot_count + 1:
        failures.append(
            f'Boot count went from {old_page.boot_count} to {page.boot_count}, '
            'expected exactly one boot'
        )
    if bytes(page.image_hash) != expected_hash:
        failures.append(
            f'Image hash mismatch: device reports '
            f'{bytes(page.image_hash).hex() or "(empty)"}, '
            f'expected {expected_hash.hex()}'
        )

    if failures:
        raise click.ClickException(
            'Flash verification failed:\n' + '\n'.join(f'- {f}' for f in failures)
        )


@click.command()
@click.argument(
    'bin_filepath', type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path)
)
@shell.common_shell_options
def main(
    bin_filepath: pathlib.Path,
    connection: shell.ConnectionType,
    log_connection: shell.ConnectionType | None,
    port: str | None,
    address: str,
    log_level: int,
) -> None:
    comms_transporter, log_transporter = shell.resolve_shell_options(
        connection, log_connection, port, address, log_level
    )

    c = client.BaseClient(
        base_bh.BaseNode(
            comms_transporter=comms_transporter, log_transporter=log_transporter
        )
    )

    start = time.monotonic()
    with c:
        old_page = c.write_flash_image(bin_filepath)
        c.reset()
    transferred = time.monotonic()
    logging.info(f'Image transferred in {transferred - start:.1f}s')

    if connection is not shell.ConnectionType.SERIAL:
        # Following the device through its reboot is only wired up for USB
        # serial connections
        logging.info('Success!')
        return

    # The device drops off the bus and the bootloader re-enumerates to
    # report its progress swapping the image banks
    if usb.wait_for_removal(usb.PicoSerial.VENDOR_PRODUCT_ID, timeout_s=5.0):
        _watch_bootloader_progress()
    else:
        logging.warning('Device never dropped off the bus; did it reset?')
    swapped = time.monotonic()
    logging.info(f'Image swapped in {swapped - transferred:.1f}s')

    with _reconnect() as c:
        _verify(c, bin_filepath, old_page)

    logging.info(f'New image up and verified in {time.monotonic() - swapped:.1f}s')
    logging.info('Success!')


if __name__ == '__main__':
    main()

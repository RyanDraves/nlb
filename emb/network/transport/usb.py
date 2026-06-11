import abc
import logging
import threading
import time
from typing import Callable, ClassVar, cast

import serial
from serial.tools import list_ports
from serial.tools import list_ports_common


def find_ports(vendor_product_id: str) -> list[str]:
    """Find the serial ports of all connected devices matching the ID."""
    devices = cast(
        list[list_ports_common.ListPortInfo],
        list(list_ports.grep(vendor_product_id)),
    )
    return [device.device for device in devices]


def wait_for_port(vendor_product_id: str, timeout_s: float) -> str | None:
    """Wait for a device matching the ID to enumerate, returning its port."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if ports := find_ports(vendor_product_id):
            return ports[0]
        time.sleep(0.2)
    return None


def wait_for_removal(vendor_product_id: str, timeout_s: float) -> bool:
    """Wait for all devices matching the ID to drop off the bus."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not find_ports(vendor_product_id):
            return True
        time.sleep(0.1)
    return False


class Serial(abc.ABC):
    VENDOR_PRODUCT_ID: ClassVar[str]
    BAUD_RATE: ClassVar[int]
    STOP_BYTES: ClassVar[bytes]
    DEVICE_NAME: ClassVar[str]

    # Bounded by `kBufSize = 1536` in `bh_cobs.hpp` less message overhead
    MAX_PAYLOAD_SIZE: ClassVar[int] = 1024

    # How long `send` will wait for the device to (re)connect
    SEND_TIMEOUT_S: ClassVar[float] = 10.0

    def __init__(self, port: str | None = None):
        self._serial = serial.Serial(None, self.BAUD_RATE, timeout=1)
        self._stop_byte = self.STOP_BYTES
        # An explicitly requested port; otherwise resolved (and re-resolved
        # on reconnects, as the path may change) by `_find_device`
        self._port = port
        self._started = False
        self._connected = threading.Event()
        self._read_thread: threading.Thread | None = None
        self._read_callback: Callable[[bytes], None] = lambda _: None

    def _find_device(self) -> str:
        devices: list[list_ports_common.ListPortInfo] = cast(
            list[list_ports_common.ListPortInfo],
            list(list_ports.grep(self.VENDOR_PRODUCT_ID)),
        )
        if not devices:
            raise RuntimeError(f'{self.DEVICE_NAME} not found')
        elif len(devices) > 1:
            device = devices[0]
            # TODO: Handle multiple devices found / stop using WSL
            # raise RuntimeError(f'Multiple {self.DEVICE_NAME}s found')
        device = devices[0]

        logging.debug(f'{self.DEVICE_NAME} found at {device.device}')
        return device.device

    @property
    def port(self) -> str:
        return self._port if self._port is not None else self._find_device()

    def _open(self) -> None:
        self._serial.port = self.port
        self._serial.open()
        self._connected.set()

    def start(self) -> None:
        if self._started:
            return
        # Fail fast if the device isn't present; reconnects are only handled
        # in the background once a connection has been established
        self._open()
        self._started = True
        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()

    def stop(self) -> None:
        if not self._started:
            return
        self._started = False
        self._connected.clear()
        self._serial.close()
        self._read_thread = None

    def send(self, data: bytes) -> None:
        # Wait out any in-progress reconnection, e.g. a device reset
        if not self._connected.wait(timeout=self.SEND_TIMEOUT_S):
            raise serial.SerialException(f'{self.DEVICE_NAME} is not connected')
        logging.debug('Serial Tx: ' + ' '.join(f'{byte:02x}' for byte in data))
        self._serial.write(data)

    def register_read_callback(self, callback: Callable[[bytes], None]) -> None:
        self._read_callback = callback

    def _reconnect(self) -> None:
        """Poll for the device to re-enumerate and reopen it."""
        logging.info(f'{self.DEVICE_NAME} disconnected; waiting for its return')
        while self._started and threading.current_thread() is self._read_thread:
            try:
                self._open()
                logging.info(f'{self.DEVICE_NAME} reconnected at {self._serial.port}')
                return
            except (RuntimeError, OSError):
                time.sleep(0.2)

    def _read_loop(self) -> None:
        buffer = bytes()
        # A stop/start cycle spawns a fresh thread; let any old one retire
        while self._started and threading.current_thread() is self._read_thread:
            try:
                buffer += self._serial.read_until(self._stop_byte, size=255)
            except (serial.SerialException, OSError):
                if (
                    not self._started
                    or threading.current_thread() is not self._read_thread
                ):
                    # Deliberately stopped
                    return
                # USB unplug or device reset; reconnect in the background
                self._connected.clear()
                self._serial.close()
                buffer = bytes()
                self._reconnect()
                continue
            if buffer.endswith(self._stop_byte):
                logging.debug(
                    'Serial Rx: ' + ' '.join(f'{byte:02x}' for byte in buffer)
                )
                self._read_callback(buffer)
                buffer = bytes()


class PicoSerial(Serial):
    VENDOR_PRODUCT_ID = '2e8a:000a'
    BAUD_RATE = 115200
    STOP_BYTES = b'\x00'
    DEVICE_NAME = 'Pico'


class Esp32Serial(Serial):
    ESP32S3_VENDOR_PRODUCT_ID = '303a:1001'
    BAUD_RATE = 460800
    STOP_BYTES = b'\r\n'
    DEVICE_NAME = 'ESP32'

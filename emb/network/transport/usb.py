import abc
import logging
import threading
from typing import Callable, ClassVar, cast

import serial
from serial.tools import list_ports
from serial.tools import list_ports_common


class Serial(abc.ABC):
    VENDOR_PRODUCT_ID: ClassVar[str]
    BAUD_RATE: ClassVar[int]
    STOP_BYTES: ClassVar[bytes]
    DEVICE_NAME: ClassVar[str]

    def __init__(self, port: str | None = None):
        # TODO: Make this automatically handle disconnects/reconnects
        self._serial = serial.Serial(None, self.BAUD_RATE, timeout=1)
        self._stop_byte = self.STOP_BYTES
        self._port = port
        self._started = False
        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
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
        if self._port is None:
            self._port = self._find_device()
        return self._port

    def start(self) -> None:
        if self._started:
            return
        # Deferred port assignment to allow for context manager usage
        self._serial.port = self.port
        if not self._serial.is_open:
            self._serial.open()
        if not self._read_thread.is_alive():
            self._read_thread.start()
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        self._serial.close()
        self._started = False

    def send(self, data: bytes) -> None:
        logging.debug('Tx: ' + ' '.join(f'{byte:02x}' for byte in data))
        self._serial.write(data)

    def register_read_callback(self, callback: Callable[[bytes], None]) -> None:
        self._read_callback = callback

    def _read_loop(self) -> None:
        buffer = bytes()
        while True:
            buffer += self._serial.read_until(self._stop_byte, size=255)
            if buffer.endswith(self._stop_byte):
                logging.debug('Rx: ' + ' '.join(f'{byte:02x}' for byte in buffer))
                self._read_callback(buffer)


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

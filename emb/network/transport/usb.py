import abc
import logging
from typing import cast

import serial
from serial.tools import list_ports
from serial.tools import list_ports_common


class Serial(abc.ABC):
    def __init__(self, baudrate: int, stop_byte: bytes):
        self._serial = serial.Serial(None, baudrate, timeout=1)
        self._stop_byte = stop_byte
        self._started = False

    @property
    @abc.abstractmethod
    def port(self) -> str: ...

    def start(self) -> None:
        if self._started:
            return
        # Deferred port assignment to allow for context manager usage
        self._serial.port = self.port
        if not self._serial.is_open:
            self._serial.open()
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        self._serial.close()
        self._started = False

    def send(self, data: bytes) -> None:
        logging.debug('Tx: ' + ' '.join(f'{byte:02x}' for byte in data))
        self._serial.write(data)

    def receive(self) -> bytes:
        buffer = bytes()
        while True:
            buffer += self._serial.read_until(self._stop_byte, size=255)
            if buffer.endswith(self._stop_byte):
                logging.debug('Rx: ' + ' '.join(f'{byte:02x}' for byte in buffer))
                return buffer


class PicoSerial(Serial):
    PICO_VENDOR_PRODUCT_ID = '2e8a:000a'

    def __init__(self, port: str | None = None):
        super().__init__(baudrate=115200, stop_byte=b'\x00')

        self._port = port

    def _find_pico(self) -> str:
        devices: list[list_ports_common.ListPortInfo] = cast(
            list[list_ports_common.ListPortInfo],
            list(list_ports.grep(self.PICO_VENDOR_PRODUCT_ID)),
        )
        if not devices:
            raise RuntimeError('Pico not found')
        elif len(devices) > 1:
            device = devices[0]
            # TODO: Handle multiple Picos found / stop using WSL
            # raise RuntimeError('Multiple Picos found')
        device = devices[0]

        logging.debug(f'Pico found at {device.device}')
        return device.device

    @property
    def port(self) -> str:
        if self._port is None:
            self._port = self._find_pico()
        return self._port

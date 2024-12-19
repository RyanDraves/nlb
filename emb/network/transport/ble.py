import abc
import asyncio
import logging
import threading
from typing import Awaitable, Callable, ClassVar

import bleak
from bleak import exc
from bleak.backends import characteristic
from bleak.backends import device

from emb.network.transport import nus_bh


class Ble(abc.ABC):
    ADDRESS: ClassVar[str]
    WRITE_CHAR_UUID: ClassVar[str]
    NOTIFY_CHAR_UUID: ClassVar[str]
    DEVICE_NAME: ClassVar[str]

    def __init__(self):
        self._started = False
        self.__client: bleak.BleakClient | None = None
        self._read_callback: Callable[[bytes], None] = lambda _: None
        self._device: device.BLEDevice | None = None

        # Start the event loop in a background thread
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._loop_thread.start()

    def __del__(self):
        # Properly close the event loop
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._loop_thread.join()

    def _run_coroutine_threadsafe[T](self, coro: Awaitable[T]) -> T:
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        # Wait for the coroutine to finish and get result
        return future.result()

    async def _find_device(self) -> None:
        """Currently unused & not exposed"""
        if self._device is not None:
            return
        devices = await bleak.BleakScanner.discover()
        if not devices:
            raise RuntimeError(f'{self.DEVICE_NAME} not found')

        device = next(
            (device for device in devices if device.address == self.ADDRESS), None
        )
        if device is None:
            raise RuntimeError(f'{self.DEVICE_NAME} not found')

        logging.debug(f'{self.DEVICE_NAME} found at {device.address}')
        self._device = device

    @property
    def _client(self) -> bleak.BleakClient:
        if self.__client is None:
            self.__client = bleak.BleakClient(self.ADDRESS)
        return self.__client

    def start(self) -> None:
        if self._started:
            return
        self._run_coroutine_threadsafe(self._start())
        self._started = True

    async def _start(self) -> None:
        if not self._client.is_connected:
            await self._client.connect()
        await self._client.start_notify(
            self.NOTIFY_CHAR_UUID, self._notification_handler
        )

    def stop(self) -> None:
        if not self._started:
            return
        self._run_coroutine_threadsafe(self._stop())
        self._started = False

    async def _stop(self) -> None:
        try:
            await self._client.stop_notify(self.NOTIFY_CHAR_UUID)
            await self._client.disconnect()
        except exc.BleakError:
            # Probably already disconnected, one way or another
            pass

    def send(self, data: bytes) -> None:
        logging.debug('Ble Tx: ' + ' '.join(f'{byte:02x}' for byte in data))
        self._run_coroutine_threadsafe(
            self._client.write_gatt_char(self.WRITE_CHAR_UUID, data, response=False)
        )

    def register_read_callback(self, callback: Callable[[bytes], None]) -> None:
        self._read_callback = callback

    def _notification_handler(
        self, char: characteristic.BleakGATTCharacteristic, data: bytearray
    ) -> None:
        logging.debug('Ble Rx: ' + ' '.join(f'{byte:02x}' for byte in data))
        self._read_callback(bytes(data))


class PicoBle(Ble):
    ADDRESS = 'D8:3A:DD:73:7F:C4'
    WRITE_CHAR_UUID = nus_bh.WRITE_CHARACTERISTIC_UUID
    NOTIFY_CHAR_UUID = nus_bh.NOTIFY_CHARACTERISTIC_UUID
    DEVICE_NAME = 'Pico'

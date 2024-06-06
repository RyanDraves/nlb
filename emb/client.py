import dataclasses
import pathlib
from typing import Protocol, Type, TypeVar, Generic

import cbor2
import serial
from serial.tools import list_ports
from serial.tools import list_ports_common

from emb.bindings import util

PICO_VENDOR_PRODUCT_ID = '2e8a:000a'

S = TypeVar('S', bound='DataclassLike')
R = TypeVar('R', bound='DataclassLike')

class DataclassLike(Protocol):
    def __init__(self, **kwargs) -> None:
        ...

    def __dict__(self) -> dict:
        ...

@dataclasses.dataclass
class Ping:
    ping: int


@dataclasses.dataclass
class FlashPage:
    address: int
    read_size: int
    data: list[int]

@dataclasses.dataclass
class LogMessage:
    message: str


MESSAGE_ID_MAP: dict[int, Type[DataclassLike]] = {
    0: Ping,
    1: FlashPage,
    2: LogMessage
}

MESSAGE_TYPE_MAP: dict[Type[DataclassLike], int] = {
    Ping: 0,
    FlashPage: 1,
    LogMessage: 2
}


def find_pico() -> str:
    devices: list[list_ports_common.ListPortInfo] = list(list_ports.grep(PICO_VENDOR_PRODUCT_ID))
    if not devices:
        raise RuntimeError('Pico not found')
    elif len(devices) > 1:
        device = devices[0]
        # raise RuntimeError('Multiple Picos found')
    device = devices[0]
    print(device.device, device.description, device.hwid, device.vid, device.pid, device.serial_number, device.location, device.manufacturer, device.product, device.interface, sep='\n')
    return device.device


class SerialNode:
    def __init__(self, port: str, baudrate: int = 115200):
        self._serial = serial.Serial(None, baudrate, timeout=1)
        self._port = port
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        # Deferred port assignment to allow for context manager usage
        self._serial.port = self._port
        if not self._serial.is_open:
            self._serial.open()
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        self._serial.close()
        self._started = False

    def __enter__(self) -> 'SerialNode':
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()

    def send(self, msg: DataclassLike) -> None:
        buffer = cbor2.dumps(dataclasses.asdict(msg))
        # Add the message ID to the beginning of the buffer
        message_id = MESSAGE_TYPE_MAP[type(msg)]
        encoded_msg = util.cobsEncode(message_id.to_bytes() + buffer) + b'\x00'
        # Print the encoded message in hex
        # print('Tx: ' + ' '.join(f'{b:02x}' for b in encoded_msg))
        self._serial.write(encoded_msg)

    def recv(self) -> DataclassLike:
        buffer = bytes()
        while True:
            buffer += self._serial.read_until(b'\x00', size=255)
            if buffer.endswith(b'\x00'):
                print('----')
                print(buffer.hex())
                print('----')
                # print('Rx: ' + ' '.join(f'{b:02x}' for b in buffer))
                decoded_buffer = util.cobsDecode(buffer[:-1])
                # Get the message type from the first byte
                try:
                    message_cls = MESSAGE_ID_MAP[decoded_buffer[0]]
                    print(decoded_buffer.hex())
                except:
                    print(decoded_buffer.hex())
                print('++++')
                msg = message_cls(**cbor2.loads(decoded_buffer[1:]))
                return msg


class Transaction(Generic[S, R]):
    @classmethod
    def transact(cls, node: SerialNode, msg: S) -> R:
        node.send(msg)
        return node.recv()

class Hello:
    def __init__(self, node: SerialNode) -> None:
        self._node = node

    def __enter__(self) -> 'Hello':
        self._node.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._node.stop()

    def ping(self) -> None:
        msg = Ping(ping=0)
        resp = Transaction[Ping, LogMessage].transact(self._node, msg)
        print(resp.message)

    def _write_flash_page(self, address: int, data: list[int]) -> None:
        msg = FlashPage(address=address, read_size=16, data=data)
        resp = Transaction[FlashPage, LogMessage].transact(self._node, msg)
        print(resp)
        print(resp.message)

    def _read_flash_page(self, address: int, size: int) -> FlashPage:
        msg = FlashPage(address=address, read_size=size, data=[])
        resp = Transaction[FlashPage, FlashPage].transact(self._node, msg)
        return resp

    def read_flash(self, outpath: pathlib.Path) -> None:
        address = 0
        flash_size = 2 * 1024 * 1024
        with outpath.open('wb') as f:
            while address < flash_size:
                print(address)
                page = self._read_flash_page(address, 256)
                if not page.data:
                    break
                f.write(bytes(page.data))
                address += len(page.data)
        print(f'Flash read to {outpath}')


def main() -> None:
    port = find_pico()
    print(f'Pico found at {port}')
    serial_node = SerialNode(port)
    client = Hello(serial_node)
    with client:
        client.ping()
        start_addr = 123658
        for i in range(0, 256, 16):
            client._write_flash_page(start_addr + i, [])
        # client._write_flash_page(123648, [])
        client._read_flash_page(123648, 256)
        # client.read_flash(pathlib.Path('/tmp/flash.bin'))


if __name__ == '__main__':
    main()

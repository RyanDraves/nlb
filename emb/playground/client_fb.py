import serial
from serial.tools import list_ports
from serial.tools import list_ports_common

from emb import system_generated as system_fbs
from emb.bindings import util

PICO_VENDOR_PRODUCT_ID = '2e8a:000a'

def find_pico() -> str:
    devices: list[list_ports_common.ListPortInfo] = list(list_ports.grep(PICO_VENDOR_PRODUCT_ID))
    if not devices:
        raise RuntimeError('Pico not found')
    elif len(devices) > 1:
        raise RuntimeError('Multiple Picos found')
    print(devices[0].device, devices[0].description, devices[0].hwid, devices[0].vid, devices[0].pid, devices[0].serial_number, devices[0].location, devices[0].manufacturer, devices[0].product, devices[0].interface, sep='\n')
    return devices[0].device


class SerialNode:
    def __init__(self, port: str, baudrate: int = 115200):
        self._serial = serial.Serial(None, baudrate, timeout=1)
        self._port = port

    def __enter__(self) -> 'SerialNode':
        # Deferred port assignment to allow for context manager usage
        self._serial.port = self._port
        if not self._serial.is_open:
            self._serial.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._serial.close()

    def send(self, msg: system_fbs.Config) -> None:
        encoded_msg = util.cobsEncode(msg.SerializeToString()) + b'\x00'
        decoded_buffer = util.cobsDecode(encoded_msg[:-1])
        # Print the encoded message in hex
        # print('Tx: ' + ' '.join(f'{b:02x}' for b in encoded_msg))
        self._serial.write(encoded_msg)

    def recv(self) -> system_fbs.Config:
        buffer = bytes()
        while True:
            buffer += self._serial.read_until(b'\x00', size=255)
            if buffer.endswith(b'\x00'):
                # print('Rx: ' + ' '.join(f'{b:02x}' for b in buffer))
                decoded_buffer = util.cobsDecode(buffer[:-1])
                msg = system_fbs.Config()
                msg.ParseFromString(decoded_buffer)
                return msg


def main() -> None:
    port = find_pico()
    print(f'Pico found at {port}')
    serial_node = SerialNode(port)
    with serial_node as node:
        msg = system_fbs.Config()
        while True:
            node.send(msg)
            return_msg = node.recv()
            assert msg.ping + 1 == return_msg.ping
            print(msg.ping, return_msg.ping)
            # print('')
            msg.ping += 1
            # time.sleep(0.5)


if __name__ == '__main__':
    main()

import sys
import serial
from serial.tools import list_ports

PICO_VENDOR_PRODUCT_ID = '2e8a:000a'

def find_pico() -> str:
    devices = list(list_ports.grep(PICO_VENDOR_PRODUCT_ID))
    if not devices:
        raise RuntimeError('Pico not found')
    elif len(devices) > 1:
        raise RuntimeError('Multiple Picos found')
    return devices[0].device


def main() -> None:
    port = find_pico()
    print(f'Pico found at {port}')
    with serial.Serial(port, 115200, timeout=1) as ser:
        while True:
            print(ser.read(100).decode('utf-8'), end='')


if __name__ == '__main__':
    main()

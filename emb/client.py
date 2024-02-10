import serial
from serial.tools import list_ports
from serial.tools import list_ports_common

PICO_VENDOR_PRODUCT_ID = '2e8a:000a'

def find_pico() -> str:
    devices: list[list_ports_common.ListPortInfo] = list(list_ports.grep(PICO_VENDOR_PRODUCT_ID))
    if not devices:
        raise RuntimeError('Pico not found')
    elif len(devices) > 1:
        raise RuntimeError('Multiple Picos found')
    print(devices[0].device, devices[0].description, devices[0].hwid, devices[0].vid, devices[0].pid, devices[0].serial_number, devices[0].location, devices[0].manufacturer, devices[0].product, devices[0].interface, sep='\n')
    return devices[0].device


def main() -> None:
    port = find_pico()
    print(f'Pico found at {port}')
    with serial.Serial(port, 115200, timeout=1) as ser:
        while True:
            print(ser.read(100).decode('utf-8'), end='')


if __name__ == '__main__':
    main()

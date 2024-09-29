import logging
from typing import cast

from emb.network.transport import usb
from emb.project.base import base_bh


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    serializer = base_bh.BaseSerializer()
    transporter = usb.PicoSerial()

    transporter.start()

    while True:
        try:
            msg = cast(
                base_bh.LogMessage, serializer.deserialize(transporter.receive())
            )
            logging.info(msg.message)
        except KeyboardInterrupt:
            break

    transporter.stop()


if __name__ == '__main__':
    main()

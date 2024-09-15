import enum
import logging

import rich_click as click
from IPython.terminal import embed
from IPython.terminal import ipapp

from emb.network.transport import tcp
from emb.network.transport import usb
from emb.project.base import base_bh
from emb.project.base import client
from nlb.util import click_utils


class ConnectionType(enum.Enum):
    SERIAL = 'serial'
    ZMQ = 'zmq'


@click.command()
@click.option(
    '--connection',
    '-c',
    type=click_utils.EnumChoice(ConnectionType),
    default=ConnectionType.SERIAL,
    help='Connection type',
)
@click.option('--port', '-p', default=None, help='Serial port')
@click.option('--address', '-a', default=tcp.Zmq.DEFAULT_ADDRESS, help='ZMQ address')
@click.option('--log', '-l', default='INFO', help='Log level')
def main(connection: ConnectionType, port: str | None, address: str, log: str) -> None:
    logging.basicConfig(level=log.upper())

    if connection is ConnectionType.SERIAL:
        transporter = usb.PicoSerial(port)
    else:
        transporter = tcp.Zmq(address)

    c = client.BaseClient(base_bh.BaseNode(transporter=transporter))

    with c:
        config = ipapp.load_default_config()
        config.InteractiveShellEmbed.colors = 'Linux'

        embed.embed(header='Base Shell', config=config)


if __name__ == '__main__':
    main()

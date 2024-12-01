import dataclasses
import enum
import logging
from typing import Callable, Type

import rich_click as click
from IPython.terminal import embed
from IPython.terminal import ipapp

from emb.network.transport import tcp
from emb.network.transport import usb
from emb.project import client
from nlb.buffham import bh
from nlb.util import click_utils


class ConnectionType(enum.Enum):
    SERIAL = 'serial'
    ZMQ = 'zmq'


@dataclasses.dataclass
class ShellContext:
    client_cls: Type[client.ClientLike]
    node_cls: Type[bh.BhNode]
    description: str


def common_shell_options(func: Callable) -> Callable:
    func = click.option(
        '--connection',
        '-c',
        type=click_utils.EnumChoice(ConnectionType),
        default=ConnectionType.SERIAL,
        help='Connection type',
    )(func)
    func = click.option('--port', '-p', default=None, help='Serial port')(func)
    func = click.option(
        '--address', '-a', default=tcp.Zmq.DEFAULT_ADDRESS, help='ZMQ address'
    )(func)
    func = click.option('--log', '-l', default='INFO', help='Log level')(func)
    return func


def shell_entry(
    connection: ConnectionType,
    port: str | None,
    address: str,
    log: str,
    ctx: ShellContext,
) -> None:
    logging.basicConfig(
        level=log.upper(), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if connection is ConnectionType.SERIAL:
        transporter = usb.PicoSerial(port)
    else:
        transporter = tcp.Zmq(address)

    c = ctx.client_cls(ctx.node_cls(transporter=transporter))

    with c:
        config = ipapp.load_default_config()
        config.InteractiveShellEmbed.colors = 'Linux'

        embed.embed(header=ctx.description, config=config)

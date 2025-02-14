import dataclasses
import enum
import logging
from typing import Callable, Type

import rich_click as click
from IPython.terminal import embed
from IPython.terminal import ipapp

from emb.network.transport import ble
from emb.network.transport import tcp
from emb.network.transport import transporter
from emb.network.transport import usb
from emb.project import client
from nlb.buffham import bh
from nlb.util import click_utils


class ConnectionType(enum.Enum):
    BLE = 'ble'
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
    func = click.option(
        '--log-connection',
        '-lc',
        type=click_utils.EnumChoice(ConnectionType),
        help='Log connection type',
    )(func)
    func = click.option('--port', '-p', default=None, help='Serial port')(func)
    func = click.option(
        '--address', '-a', default=tcp.Zmq.DEFAULT_ADDRESS, help='ZMQ address'
    )(func)
    func = click_utils.log_level(func)
    return func


def resolve_shell_options(
    connection: ConnectionType,
    log_connection: ConnectionType | None,
    port: str | None,
    address: str,
    log_level: int,
) -> tuple[transporter.TransporterLike, transporter.TransporterLike]:
    logging.basicConfig(
        level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    comms_transporter = _get_transporter(connection, port, address)
    log_transporter = (
        comms_transporter
        if log_connection is None
        else _get_transporter(log_connection, port, address)
    )

    return comms_transporter, log_transporter


def _get_transporter(
    connection: ConnectionType, port: str | None, address: str
) -> transporter.TransporterLike:
    if connection is ConnectionType.SERIAL:
        return usb.PicoSerial(port)
    elif connection is ConnectionType.BLE:
        return ble.PicoBle()
    else:
        return tcp.Zmq(address)


def shell_entry(
    connection: ConnectionType,
    log_connection: ConnectionType | None,
    port: str | None,
    address: str,
    log_level: int,
    ctx: ShellContext,
) -> None:
    comms_transporter, log_transporter = resolve_shell_options(
        connection, log_connection, port, address, log_level
    )

    c = ctx.client_cls(
        ctx.node_cls(
            comms_transporter=comms_transporter, log_transporter=log_transporter
        )
    )

    with c:
        config = ipapp.load_default_config()
        config.InteractiveShellEmbed.colors = 'Linux'

        embed.embed(header=ctx.description, config=config)

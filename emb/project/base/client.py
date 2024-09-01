import dataclasses
import logging
import pathlib
from typing import Self

from emb.network.node import dataclass_node
from emb.network.serialize import cbor2_cobs
from emb.network.transport import transporter
from nlb.datastructure import bidirectional_dict


# TODO: Generate everything below up until the client methods
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


class BaseSerializer(cbor2_cobs.Cbor2Cobs):
    def __init__(self, registry: cbor2_cobs.Registry | None = None):
        registry = registry or bidirectional_dict.BidirectionalMap()
        registry.update(
            {
                Ping: 0,
                FlashPage: 1,
                LogMessage: 2,
            }
        )
        super().__init__(registry)


class BaseNode[Transporter: transporter.TransporterLike](
    dataclass_node.DataclassNode[BaseSerializer, Transporter]
):
    def __init__(
        self,
        serializer: BaseSerializer | None = None,
        transporter: Transporter | None = None,
    ):
        super().__init__(serializer or BaseSerializer(), transporter)


class BaseClient:
    PING = dataclass_node.Transaction[Ping, LogMessage]
    FLASH_PAGE = dataclass_node.Transaction[FlashPage, FlashPage]
    READ_FLASH_PAGE = dataclass_node.Transaction[FlashPage, FlashPage]

    def __init__(self, node: BaseNode) -> None:
        self._node = node

    def __enter__(self) -> Self:
        self._node.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._node.stop()

    def ping(self) -> None:
        msg = Ping(ping=0)
        resp = self.PING.transact(self._node, msg)
        logging.info(resp.message)

    def _write_flash_page(self, address: int, data: list[int]) -> None:
        msg = FlashPage(address=address, read_size=0, data=data)
        resp = self.FLASH_PAGE.transact(self._node, msg)
        logging.info(resp.address)

    def _read_flash_page(self, address: int, size: int) -> FlashPage:
        msg = FlashPage(address=address, read_size=size, data=[])
        resp = self.READ_FLASH_PAGE.transact(self._node, msg)
        return resp

    def read_flash(self, outpath: pathlib.Path) -> None:
        address = 0
        flash_size = 2 * 1024 * 1024
        with outpath.open('wb') as f:
            while address < flash_size:
                # TODO: rm
                print(address)
                page = self._read_flash_page(address, 256)
                if not page.data:
                    break
                f.write(bytes(page.data))
                address += len(page.data)
        logging.info(f'Flash read to {outpath}')

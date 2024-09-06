import dataclasses
from typing import Self

from emb.network.node import dataclass_node
from emb.network.serialize import cbor2_cobs
from emb.network.transport import transporter

@dataclasses.dataclass
class Ping:
    ping: int

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> Self: ...

@dataclasses.dataclass
class FlashPage:
    address: int
    read_size: int
    data: list[int]

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> Self: ...

@dataclasses.dataclass
class LogMessage:
    message: str

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> Self: ...

class BaseSerializer(cbor2_cobs.Cbor2Cobs):
    def __init__(self, registry: cbor2_cobs.Registry | None = None): ...

class BaseNode[Transporter: transporter.TransporterLike](dataclass_node.DataclassNode[BaseSerializer, Transporter]):
    def __init__(self, serializer: BaseSerializer | None = None, transporter: Transporter | None = None): ...

PING: dataclass_node.Transaction[Ping,LogMessage] = ...
FLASH_PAGE: dataclass_node.Transaction[FlashPage,FlashPage] = ...
READ_FLASH_PAGE: dataclass_node.Transaction[FlashPage,FlashPage] = ...

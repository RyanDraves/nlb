# @generated by Buffham
import dataclasses
from typing import Self

from emb.network.serialize import bh_cobs
from emb.network.transport import transporter
from nlb.buffham import bh

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
class FlashSector:
    sector: int
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

class BaseSerializer(bh_cobs.BhCobs):
    def __init__(self, registry: bh_cobs.Registry | None = None): ...

class BaseNode[Transporter: transporter.TransporterLike](bh.BhNode[BaseSerializer, Transporter]):
    def __init__(self, serializer: BaseSerializer | None = None, transporter: Transporter | None = None): ...

PING: bh.Transaction[Ping, LogMessage] = ...
WRITE_FLASH_IMAGE: bh.Transaction[FlashPage, FlashPage] = ...
READ_FLASH: bh.Transaction[FlashPage, FlashPage] = ...
WRITE_FLASH_SECTOR: bh.Transaction[FlashSector, FlashSector] = ...
READ_FLASH_SECTOR: bh.Transaction[FlashSector, FlashSector] = ...
RESET: bh.Transaction[Ping, Ping] = ...

# @generated by Buffham
import dataclasses
import enum
from typing import Self, Type

from emb.network.serialize import bh_cobs
from emb.network.transport import transporter
from nlb.buffham import bh

@dataclasses.dataclass
class Ping:
    # Pong!
    ping: int

    def serialize(self) -> bytes: ...
    @classmethod
    def deserialize(cls, buffer: bytes) -> tuple[Self, int]: ...

@dataclasses.dataclass
class FlashPage:
    """A page from the app flash image"""

    # Address to work with
    #
    # On writes, it's relative to the start of the opposite side's firmware address
    # On reads, it's relative to the start of flash
    address: int
    # Number of bytes to read. Be mindful of `kBufSize = 1536` in `bh_cobs.hpp`
    # and the stack size of the microcontroller (2kB for the Pico)
    read_size: int
    data: list[int]

    def serialize(self) -> bytes: ...
    @classmethod
    def deserialize(cls, buffer: bytes) -> tuple[Self, int]: ...

@dataclasses.dataclass
class FlashSector:
    """A scratchpad sector of flash memory"""

    # Sector [0, 31] to work with
    sector: int
    data: list[int]

    def serialize(self) -> bytes: ...
    @classmethod
    def deserialize(cls, buffer: bytes) -> tuple[Self, int]: ...

@dataclasses.dataclass
class LogMessage:
    message: str

    def serialize(self) -> bytes: ...
    @classmethod
    def deserialize(cls, buffer: bytes) -> tuple[Self, int]: ...

REGISTRY: dict[int, Type[bh.BuffhamLike]] = ...

class BaseSerializer(bh_cobs.BhCobs):
    def __init__(self, registry: bh_cobs.Registry | None = None): ...

class BaseNode[
    CommsTransporter: transporter.TransporterLike,
    LogTransporter: transporter.TransporterLike,
](bh.BhNode[BaseSerializer, CommsTransporter, LogTransporter]):
    def __init__(
        self,
        serializer: BaseSerializer | None = None,
        comms_transporter: CommsTransporter | None = None,
        log_transporter: LogTransporter | None = None,
    ): ...

# Pong!
PING: bh.Transaction[Ping, LogMessage] = ...
# Write data to the opposite flash app image
WRITE_FLASH_IMAGE: bh.Transaction[FlashPage, FlashPage] = ...
# Read from anywhere in flash
READ_FLASH: bh.Transaction[FlashPage, FlashPage] = ...
# Write flash sector contents
WRITE_FLASH_SECTOR: bh.Transaction[FlashSector, FlashSector] = ...
# Read flash flash sector contents
READ_FLASH_SECTOR: bh.Transaction[FlashSector, FlashSector] = ...
# Reset the device (needs a type to send/receive; both unused)
RESET: bh.Transaction[Ping, Ping] = ...

class PublishIds(enum.Enum):
    # Logging macros output over this
    LOG_MESSAGE = 6

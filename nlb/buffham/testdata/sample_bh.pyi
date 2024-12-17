# @generated by Buffham
import dataclasses
import enum
from typing import Self, Type

from emb.network.serialize import bh_cobs
from emb.network.transport import transporter
from nlb.buffham import bh

from nlb.buffham.testdata import other_bh

# This is a constant in the global scope
MY_CONSTANT = 4
CONSTANT_STRING = "Hello, world!"  # constants can have inline comments
# Constants may reference other constants with {brackets}
COMPOSED_CONSTANT = 2 + MY_CONSTANT + other_bh.OTHER_CONSTANT


@dataclasses.dataclass
class Ping:
    """A message comment
    """

    # Add some comments here
    ping: int

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> tuple[Self, int]: ...

@dataclasses.dataclass
class FlashPage:
    """
    A bunch of message comments,
    in a block-like pattern.

    All of these belong to `FlashPage`

    """

    address: int
    # Another field comment
    data: list[int]  # What about some in-line comments for fields?
    # This comment belongs to `read_size`
    read_size: int

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> tuple[Self, int]: ...

@dataclasses.dataclass
class LogMessage:
    message: str

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> tuple[Self, int]: ...

@dataclasses.dataclass
class NestedMessage:
    flag: int
    message: LogMessage
    numbers: list[int]
    pong: Ping
    other_pong: other_bh.Pong

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> tuple[Self, int]: ...

REGISTRY: dict[int, Type[bh.BuffhamLike]] = ...

class SampleSerializer(bh_cobs.BhCobs):
    def __init__(self, registry: bh_cobs.Registry | None = None): ...

class SampleNode[Transporter: transporter.TransporterLike](bh.BhNode[SampleSerializer, Transporter]):
    def __init__(self, serializer: SampleSerializer | None = None, transporter: Transporter | None = None): ...

PING: bh.Transaction[other_bh.Pong, LogMessage] = ...
# Transaction comment
FLASH_PAGE: bh.Transaction[FlashPage, FlashPage] = ...
READ_FLASH_PAGE: bh.Transaction[FlashPage, FlashPage] = ...

class PublishIds(enum.Enum):
    # Publish comment
    LOG_MESSAGE = 4
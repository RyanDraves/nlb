"""Utilities for Buffham."""

import dataclasses
import pathlib
from typing import Protocol, Self, Type, cast

from emb.network.node import node
from emb.network.transport import transporter
from nlb.util import dataclass


class BuffhamLike(dataclass.DataclassLike, Protocol):
    """Protocol for Buffham-like objects."""

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> tuple[Self, int]: ...


class BhSerializer(Protocol):
    def serialize(self, msg: BuffhamLike, request_id: int) -> bytes: ...

    def deserialize(self, data: bytes) -> tuple[int, BuffhamLike]: ...


class BhNode[
    Bh_Serializer: BhSerializer,
    CommsTransporter: transporter.TransporterLike,
    LogTransporter: transporter.TransporterLike,
](node.NlbNode[Bh_Serializer, CommsTransporter, LogTransporter]):
    """Generic node that uses buffham datatypes for messages."""

    def _transact(
        self, message: dataclass.DataclassLike, request_id: int
    ) -> dataclass.DataclassLike:
        return super()._transact(message, request_id)


@dataclasses.dataclass
class Transaction[S: BuffhamLike, R: BuffhamLike]:
    """A typed transaction in a buffham node"""

    request_id: int

    def transact(self, node: BhNode, msg: S) -> R:
        return cast(R, node._transact(msg, self.request_id))


def read_file(path: pathlib.Path, schema: Type[BuffhamLike]) -> BuffhamLike:
    """Read a binary Buffham file (.bhb) from a schema"""
    return schema.deserialize(path.read_bytes())[0]


def write_file(path: pathlib.Path, msg: BuffhamLike) -> None:
    """Write a message to a binary Buffham file (.bhb)"""
    path.write_bytes(msg.serialize())

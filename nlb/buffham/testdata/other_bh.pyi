# @generated by Buffham
import dataclasses
from typing import Self

from emb.network.serialize import bh_cobs
from emb.network.transport import transporter
from nlb.buffham import bh

OTHER_CONSTANT = 2


@dataclasses.dataclass
class Ping:
    """This file shares a message name with `sample.bh`
    """

    pong: int

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> tuple[Self, int]: ...

class OtherSerializer(bh_cobs.BhCobs):
    def __init__(self, registry: bh_cobs.Registry | None = None): ...

class OtherNode[Transporter: transporter.TransporterLike](bh.BhNode[OtherSerializer, Transporter]):
    def __init__(self, serializer: OtherSerializer | None = None, transporter: Transporter | None = None): ...

PONG: bh.Transaction[Ping, Ping] = ...

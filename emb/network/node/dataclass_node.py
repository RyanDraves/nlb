from typing import cast

from emb.network.node import node
from emb.network.serialize import serializer
from emb.network.transport import transporter
from nlb.util import dataclass


class DataclassNode[
    DataclassSerializer: serializer.DataclassSerializer,
    Transporter: transporter.TransporterLike,
](node.NlbNode[DataclassSerializer, Transporter]):
    """Generic node that uses dataclasses for message types."""

    def _transact(self, message: dataclass.DataclassLike) -> dataclass.DataclassLike:
        return super()._transact(message)


class Transaction[S: dataclass.DataclassLike, R: dataclass.DataclassLike]:
    """A typed transaction in a dataclass node"""

    @classmethod
    def transact(cls, node: DataclassNode, msg: S) -> R:
        return cast(R, node._transact(msg))
        return cast(R, node._transact(msg))

import dataclasses
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

    def _transact(
        self, message: dataclass.DataclassLike, request_id: int
    ) -> dataclass.DataclassLike:
        return super()._transact(message, request_id)


@dataclasses.dataclass
class Transaction[S: dataclass.DataclassLike, R: dataclass.DataclassLike]:
    """A typed transaction in a dataclass node"""

    request_id: int

    def transact(self, node: DataclassNode, msg: S) -> R:
        return cast(R, node._transact(msg, self.request_id))

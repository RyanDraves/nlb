import dataclasses

import cbor2

from emb.network.frame import cobs
from nlb.datastructure import bidirectional_dict
from nlb.util import dataclass

type Registry = bidirectional_dict.BidirectionalMap[type[dataclass.DataclassLike], int]


class Cbor2Cobs:
    def __init__(self, registry: Registry):
        self._registry = registry

    def serialize(self, msg: dataclass.DataclassLike) -> bytes:
        buffer = cbor2.dumps(dataclasses.asdict(msg))
        # Add the message ID to the beginning of the buffer
        message_id = self._registry[type(msg)]
        return cobs.cobs_encode(message_id.to_bytes() + buffer) + b'\x00'

    def deserialize(self, data: bytes) -> dataclass.DataclassLike:
        # Drop the null byte
        decoded_buffer = cobs.cobs_decode(data[:-1])
        # Get the message type from the first byte
        message_cls = self._registry[decoded_buffer[0]]
        return message_cls(**cbor2.loads(decoded_buffer[1:]))

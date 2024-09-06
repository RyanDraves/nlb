import dataclasses

import cbor2

from emb.network.frame import cobs
from nlb.util import dataclass

type Registry = dict[int, type[dataclass.DataclassLike]]


class Cbor2Cobs:
    def __init__(self, registry: Registry):
        self._registry = registry

    def serialize(self, msg: dataclass.DataclassLike, request_id: int) -> bytes:
        buffer = cbor2.dumps(dataclasses.asdict(msg))
        # Add the request ID to the beginning of the buffer
        return (
            cobs.cobs_encode(
                request_id.to_bytes(length=1, byteorder='big', signed=False) + buffer
            )
            + b'\x00'
        )

    def deserialize(self, data: bytes) -> dataclass.DataclassLike:
        # Drop the null byte
        decoded_buffer = cobs.cobs_decode(data[:-1])
        # Get the message type from the first byte
        message_cls = self._registry[decoded_buffer[0]]
        return message_cls(**cbor2.loads(decoded_buffer[1:]))

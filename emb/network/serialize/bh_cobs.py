from emb.network.frame import cobs
from nlb.buffham import bh

type Registry = dict[int, type[bh.BuffhamLike]]


class BhCobs:
    def __init__(self, registry: Registry):
        self._registry = registry

    def serialize(self, msg: bh.BuffhamLike, request_id: int) -> bytes:
        buffer = msg.serialize()

        # Add the request ID to the beginning of the buffer
        return (
            cobs.cobs_encode(
                request_id.to_bytes(length=1, byteorder='little', signed=False) + buffer
            )
            + b'\x00'
        )

    def deserialize(self, data: bytes) -> bh.BuffhamLike:
        # Drop the null byte
        decoded_buffer = cobs.cobs_decode(data[:-1])

        # Get the message type from the first byte
        message_cls = self._registry[decoded_buffer[0]]
        return message_cls.deserialize(decoded_buffer[1:])

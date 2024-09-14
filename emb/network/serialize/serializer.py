from typing import Any, Protocol

from nlb.util import dataclass


class SerializerLike(Protocol):
    """Protocol for serializing and deserializing data."""

    def serialize(self, msg: Any, request_id: int) -> bytes: ...

    def deserialize(self, data: bytes) -> Any: ...


class DataclassSerializer(Protocol):
    def serialize(self, msg: dataclass.DataclassLike, request_id: int) -> bytes: ...

    def deserialize(self, data: bytes) -> dataclass.DataclassLike: ...

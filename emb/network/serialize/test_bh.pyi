import dataclasses
from typing import Self

@dataclasses.dataclass
class Foo:
    bar: int
    baz: str
    qux: list[int]

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> Self: ...


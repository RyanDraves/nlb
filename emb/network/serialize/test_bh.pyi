import dataclasses
from typing import Self

@dataclasses.dataclass
class Foo:
    bar: int
    qux: list[int]
    baz: str

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> Self: ...


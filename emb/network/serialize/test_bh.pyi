# @generated by Buffham
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

@dataclasses.dataclass
class Unaligned:
    a: int
    b: int
    c: int
    d: int
    e: str
    f: list[int]
    g: list[int]
    h: list[int]
    i: list[int]

    def serialize(self) -> bytes: ...

    @classmethod
    def deserialize(cls, buffer: bytes) -> Self: ...


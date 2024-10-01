from typing import Protocol, Self

from nlb.buffham import bh


class ClientLike(Protocol):
    def __init__(self, node: bh.BhNode) -> None: ...

    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type, exc_value, traceback) -> None: ...


class Client:
    def __init__(self, node: bh.BhNode) -> None:
        self._node = node

    def __enter__(self) -> Self:
        self._node.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._node.stop()

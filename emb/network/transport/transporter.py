from typing import Protocol


class TransporterLike(Protocol):
    """Protocol for sending and receiving data."""
    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def send(self, data: bytes) -> None:
        ...

    def receive(self) -> bytes:
        ...

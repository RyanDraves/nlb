from typing import Callable, Protocol


class TransporterLike(Protocol):
    """Protocol for sending and receiving data."""

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def send(self, data: bytes) -> None: ...

    def register_read_callback(self, callback: Callable[[bytes], None]) -> None:
        """Register a callback to be called when data is received.

        Callbacks are invoked on the read thread. Keep them short to avoid
        blocking the read loop.
        """

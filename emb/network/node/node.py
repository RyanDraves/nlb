import logging
import threading
from typing import Any, Callable, Self, get_args

from emb.network.serialize import serializer
from emb.network.transport import transporter


class NlbNode[
    Serializer: serializer.SerializerLike, Transporter: transporter.TransporterLike
]:
    """A generic client node"""

    def __init__(
        self,
        serializer: Serializer | None = None,
        transporter: Transporter | None = None,
    ):
        self.__serializer = serializer
        self.__transporter = transporter

        self._cv = threading.Condition()
        self._request_id = -1
        self._msg: Any | None = None

        self._publish_callbacks: dict[int, Callable[[Any], None]] = {}

    @property
    def _serializer(self) -> Serializer:
        # Introspect the generic type; hidden as a property so the object
        # can be initialized first.
        if self.__serializer is None:
            self.__serializer = get_args(self.__orig_class__)[0]  # type: ignore
        return self.__serializer  # type: ignore

    @property
    def _transporter(self) -> Transporter:
        # Introspect the generic type; hidden as a property so the object
        # can be initialized first.
        if self.__transporter is None:
            self.__transporter = get_args(self.__orig_class__)[1]  # type: ignore
        return self.__transporter  # type: ignore

    def start(self) -> None:
        self._transporter.register_read_callback(self._on_receive)
        self._transporter.start()

    def stop(self) -> None:
        self._transporter.stop()

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()

    def register_publish_callback[
        Send
    ](self, request_id: int, callback: Callable[[Send], None]) -> None:
        """Register a callback on receipt of a published message

        NOTE: This callback will occur in the IO thread; don't waste time
        """
        self._publish_callbacks[request_id] = callback

    def _on_receive(self, data: bytes) -> None:
        """Callback from the transport layer upon receiving a frame

        NOTE: This callback will occur in the IO thread; don't waste time
        """
        with self._cv:
            message_id, self._msg = self._serializer.deserialize(data)
            if message_id == self._request_id:
                self._cv.notify()
            elif message_id in self._publish_callbacks:
                self._publish_callbacks[message_id](self._msg)
            else:
                logging.warning(f'Dropping message with ID {message_id}: {self._msg}')

    def _transact(self, message: Any, request_id: int) -> Any:
        self._transporter.send(self._serializer.serialize(message, request_id))

        with self._cv:
            self._request_id = request_id
            self._cv.wait()
            return self._msg

        return self._serializer.deserialize(self._transporter.receive())

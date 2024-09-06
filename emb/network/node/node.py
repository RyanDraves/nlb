from typing import Any, Self, get_args

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

    @property
    def _serializer(self) -> Serializer:
        # Introspect the generic type; hidden as a property to the object
        # can be initialized first.
        if self.__serializer is None:
            self.__serializer = get_args(self.__orig_class__)[0]  # type: ignore
        return self.__serializer  # type: ignore

    @property
    def _transporter(self) -> Transporter:
        # Introspect the generic type; hidden as a property to the object
        # can be initialized first.
        if self.__transporter is None:
            self.__transporter = get_args(self.__orig_class__)[1]  # type: ignore
        return self.__transporter  # type: ignore

    def start(self) -> None:
        self._transporter.start()

    def stop(self) -> None:
        self._transporter.stop()

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()

    def _transact(self, message: Any, request_id: int) -> Any:
        self._transporter.send(self._serializer.serialize(message, request_id))
        return self._serializer.deserialize(self._transporter.receive())

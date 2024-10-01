import zmq


class Zmq:
    DEFAULT_HOST = 'tcp://localhost'
    DEFAULT_ADDRESS = DEFAULT_HOST + ':1337'

    def __init__(self, address: str):
        self._context = zmq.Context(1)
        self._address = address
        self._socket = None

    def start(self) -> None:
        self._socket = self._context.socket(zmq.SocketType.REQ)
        self._socket.connect(self._address)

    def stop(self) -> None:
        if self._socket and not self._socket.closed:
            self._socket.close()

    def send(self, data: bytes) -> None:
        assert self._socket
        self._socket.send(data)

    def receive(self) -> bytes:
        assert self._socket
        return self._socket.recv()

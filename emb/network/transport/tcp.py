import random
import threading
from typing import Callable

import zmq


class Zmq:
    DEFAULT_HOST = 'tcp://localhost'
    DEFAULT_ADDRESS = DEFAULT_HOST + ':1337'

    def __init__(self, address: str):
        self._ctx = zmq.Context(1)
        self._address = address

        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._stop = threading.Event()

        self._callback: Callable[[bytes], None] = lambda _: None

        self._pipe_name = f'inproc://tx_pipe_{random.randint(0, 2**32)}'
        self._write_pipe = self._ctx.socket(zmq.PAIR)
        self._write_pipe.connect(self._pipe_name)

    def start(self) -> None:
        self._stop.clear()

        if not self._read_thread.is_alive():
            self._read_thread.start()

    def stop(self) -> None:
        self._stop.set()

    def send(self, data: bytes) -> None:
        self._write_pipe.send(data)

    def register_read_callback(self, callback: Callable[[bytes], None]) -> None:
        self._callback = callback

    def _read_loop(self) -> None:
        read_pipe = self._ctx.socket(zmq.PAIR)
        read_pipe.bind(self._pipe_name)

        io_socket = self._ctx.socket(zmq.SocketType.DEALER)
        io_socket.connect(self._address)

        poller = zmq.Poller()
        poller.register(read_pipe, zmq.POLLIN)
        poller.register(io_socket, zmq.POLLIN)

        while not self._stop.is_set():
            socks: dict[zmq.Socket, int] = dict(poller.poll())

            if read_pipe in socks:
                io_socket.send(read_pipe.recv())

            if io_socket in socks:
                self._callback(io_socket.recv())

        io_socket.close()

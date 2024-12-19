import os
import pathlib
import subprocess
import unittest
from typing import Type

import portpicker

from emb.network.transport import tcp
from emb.project import client
from nlb.buffham import bh


class HostTestBase[C: client.ClientLike, N: bh.BhNode](unittest.TestCase):
    # NOTE: Not classvars, see:
    # https://github.com/python/typing/discussions/1424#discussioncomment-7901647
    CLIENT_CLS: Type[C]
    NODE_CLS: Type[N]

    def setUp(self) -> None:
        host_bin = pathlib.Path(os.environ['HOST_BIN'])

        port = portpicker.pick_unused_port()
        address = tcp.Zmq.DEFAULT_HOST + f':{port}'

        self.host = subprocess.Popen(
            [str(host_bin)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={'ZMQ_PORT': str(port)},
        )

        self.addCleanup(self.host.terminate)

        transporter = tcp.Zmq(address)
        self.node = self.NODE_CLS(
            comms_transporter=transporter, log_transporter=transporter
        )
        self.client = self.CLIENT_CLS(self.node)

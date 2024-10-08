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

        self.host = subprocess.Popen(
            [str(host_bin)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.addCleanup(self.host.terminate)

        # NOTE: This `DEFAULT_ADDRESS` use is naughty and prevents concurrent tests
        # from running. A port picker would be better, but right now there's no method
        # to pass the port to the host binary (need to abstract `main` for host compilation).
        port = portpicker.pick_unused_port()
        # TODO: Use `address` instead of `DEFAULT_ADDRESS`
        address = tcp.Zmq.DEFAULT_HOST + f':{port}'

        self.node = self.NODE_CLS(transporter=tcp.Zmq(tcp.Zmq.DEFAULT_ADDRESS))
        self.client = self.CLIENT_CLS(self.node)

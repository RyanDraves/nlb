import os
import pathlib
import subprocess
import unittest
from typing import ClassVar, Type

from emb.network.transport import tcp
from emb.project import client
from nlb.buffham import bh


class HostTestBase[C: client.ClientLike, N: bh.BhNode](unittest.TestCase):
    # NOTE: Not classvars, see:
    # https://github.com/python/typing/discussions/1424#discussioncomment-7901647
    NODE_CLS: Type[N]
    CLIENT_CLS: Type[C]

    def setUp(self) -> None:
        host_bin = pathlib.Path(os.environ['HOST_BIN'])

        self.host = subprocess.Popen(
            [str(host_bin)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.addCleanup(self.host.terminate)

        self.node = self.NODE_CLS(transporter=tcp.Zmq(tcp.Zmq.DEFAULT_ADDRESS))
        self.client = self.CLIENT_CLS(self.node)

import os
import pathlib
import subprocess
import tempfile
import unittest

from emb.network.transport import tcp
from emb.project.base import client


class HostTest(unittest.TestCase):

    def setUp(self) -> None:
        host_bin = pathlib.Path(os.environ['HOST_BIN'])

        self.host = subprocess.Popen(
            [str(host_bin)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.addCleanup(self.host.terminate)

        self.node = client.BaseNode(transporter=tcp.Zmq(tcp.Zmq.DEFAULT_ADDRESS))
        self.client = client.BaseClient(self.node)

    def test_ping(self):
        with self.client:
            self.client.ping()

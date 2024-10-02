from emb.project import host_test_base
from emb.project.robo24 import client
from emb.project.robo24 import robo24_bh


class HostTest(host_test_base.HostTestBase[client.Robo24Client, robo24_bh.Robo24Node]):
    CLIENT_CLS = client.Robo24Client
    NODE_CLS = robo24_bh.Robo24Node

    def test_ping(self):
        with self.client:
            self.client.base.ping()

    def test_get_measurement(self):
        with self.client:
            measure = self.client.get_measurement()
            # It's not mocked or connected to anything, so we expect the driver
            # to return a default value.
            self.assertEqual(measure.distance_mm, 0)
            self.assertGreater(measure.timestamp_ms, 0)

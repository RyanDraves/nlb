from emb.project import client
from emb.project.base import base_bh
from emb.project.base import client as base_client
from emb.project.robo24 import robo24_bh
from nlb.buffham import bh


class Robo24Client(client.Client):
    def __init__(self, node: bh.BhNode) -> None:
        super().__init__(node)
        self.base = base_client.BaseClient(node)

    def get_measurement(self) -> robo24_bh.DistanceMeasurement:
        msg = base_bh.Ping(ping=0)
        resp = robo24_bh.GET_MEASUREMENT.transact(self._node, msg)
        return resp

from emb.project import client
from emb.project.base import base_bh
from emb.project.base import client as base_client
from emb.project.punbox import punbox_bh
from nlb.buffham import bh


class PunboxClient(client.Client):
    def __init__(self, node: bh.BhNode) -> None:
        super().__init__(node)
        self.base = base_client.BaseClient(node)

    def play_sound(self) -> punbox_bh.PunboxState:
        msg = base_bh.Ping(ping=0)
        resp = punbox_bh.PLAY_SOUND.transact(self._node, msg)
        return resp

    def get_state(self) -> punbox_bh.PunboxState:
        msg = base_bh.Ping(ping=0)
        resp = punbox_bh.GET_STATE.transact(self._node, msg)
        return resp

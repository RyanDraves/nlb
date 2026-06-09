from emb.project import host_test_base
from emb.project.punbox import client
from emb.project.punbox import punbox_bh


class HostTest(host_test_base.HostTestBase[client.PunboxClient, punbox_bh.PunboxNode]):
    CLIENT_CLS = client.PunboxClient
    NODE_CLS = punbox_bh.PunboxNode

    def test_ping(self):
        with self.client:
            self.client.base.ping()

    def test_play_sound(self):
        with self.client:
            state = self.client.play_sound()
            self.assertEqual(state.press_count, 1)
            # Host audio is a no-op, so playback "finishes" instantly
            self.assertEqual(state.playing, 0)

            state = self.client.play_sound()
            self.assertEqual(state.press_count, 2)

    def test_get_state(self):
        with self.client:
            state = self.client.get_state()
            self.assertEqual(state.press_count, 0)
            self.assertEqual(state.playing, 0)

            self.client.play_sound()

            state = self.client.get_state()
            self.assertEqual(state.press_count, 1)

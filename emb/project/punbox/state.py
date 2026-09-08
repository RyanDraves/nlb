"""Print the punbox state as JSON, for scripted checks (e.g. bringup)."""

import json

import rich_click as click

from emb.network.transport import usb
from emb.project.punbox import client
from emb.project.punbox import punbox_bh


@click.command()
def main() -> None:
    transporter = usb.PicoSerial()
    c = client.PunboxClient(
        punbox_bh.PunboxNode(comms_transporter=transporter, log_transporter=transporter)
    )

    with c:
        state = c.get_state()

    print(json.dumps({'press_count': state.press_count, 'playing': state.playing}))


if __name__ == '__main__':
    main(prog_name='state')

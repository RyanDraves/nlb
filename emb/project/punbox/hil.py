"""Hardware-in-the-loop smoke test: ping, trigger playback, read state."""

import logging

import rich_click as click

from emb.project import shell
from emb.project.punbox import client
from emb.project.punbox import punbox_bh


@click.command()
@shell.common_shell_options
def main(
    connection: shell.ConnectionType,
    log_connection: shell.ConnectionType | None,
    port: str | None,
    address: str,
    log_level: int,
) -> None:
    comms_transporter, log_transporter = shell.resolve_shell_options(
        connection, log_connection, port, address, log_level
    )

    c = client.PunboxClient(
        punbox_bh.PunboxNode(
            comms_transporter=comms_transporter, log_transporter=log_transporter
        )
    )

    with c:
        c.base.ping()
        logging.info('Ping OK')

        state = c.get_state()
        logging.info(
            'Initial state: press_count=%d playing=%d', state.press_count, state.playing
        )

        state = c.play_sound()
        logging.info(
            'play_sound: press_count=%d playing=%d', state.press_count, state.playing
        )


if __name__ == '__main__':
    main(prog_name='hil')

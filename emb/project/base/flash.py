import logging
import pathlib

import rich_click as click

from emb.project import shell
from emb.project.base import base_bh
from emb.project.base import client


@click.command()
@click.argument(
    'bin_filepath', type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path)
)
@shell.common_shell_options
def main(
    bin_filepath: pathlib.Path,
    connection: shell.ConnectionType,
    log_connection: shell.ConnectionType | None,
    port: str | None,
    address: str,
    log_level: int,
) -> None:
    comms_transporter, log_transporter = shell.resolve_shell_options(
        connection, log_connection, port, address, log_level
    )

    c = client.BaseClient(
        base_bh.BaseNode(
            comms_transporter=comms_transporter, log_transporter=log_transporter
        )
    )

    with c:
        c.write_flash_image(bin_filepath)
        c.reset()

    logging.info('Success!')


if __name__ == '__main__':
    main()

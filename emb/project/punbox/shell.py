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
):
    ctx = shell.ShellContext(client.PunboxClient, punbox_bh.PunboxNode, 'Punbox Shell')

    shell.shell_entry(connection, log_connection, port, address, log_level, ctx)


if __name__ == '__main__':
    main(prog_name='shell')

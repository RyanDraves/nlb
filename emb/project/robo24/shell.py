import rich_click as click

from emb.project import shell
from emb.project.robo24 import client
from emb.project.robo24 import robo24_bh


@click.command()
@shell.common_shell_options
def main(
    connection: shell.ConnectionType,
    log_connection: shell.ConnectionType | None,
    port: str | None,
    address: str,
    log_level: int,
):
    ctx = shell.ShellContext(client.Robo24Client, robo24_bh.Robo24Node, 'Robo24 Shell')

    shell.shell_entry(connection, log_connection, port, address, log_level, ctx)


if __name__ == '__main__':
    main()

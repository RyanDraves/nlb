import rich_click as click

from emb.project import shell
from emb.project.base import base_bh
from emb.project.base import client


@click.command()
@shell.common_shell_options
def main(connection: shell.ConnectionType, port: str | None, address: str, log: str):
    ctx = shell.ShellContext(client.BaseClient, base_bh.BaseNode, 'Base Shell')

    shell.shell_entry(connection, port, address, log, ctx)


if __name__ == '__main__':
    main()

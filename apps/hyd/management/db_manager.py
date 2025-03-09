import enum
import pathlib

import rich_click as click
from alembic import command
from alembic import config

from apps.hyd.management import client
from apps.hyd.management import schema
from nlb.util import click_utils
from nlb.util import path_utils


class Action(enum.Enum):
    CREATE = enum.auto()
    MIGRATE = enum.auto()
    PURGE = enum.auto()


def create_tables(c: client.DbClient) -> None:
    schema.Base.metadata.create_all(c.engine)
    print('Tables created successfully')


def run_migrations(c: client.DbClient) -> None:
    script_dir = pathlib.Path(__file__).parent
    alembic_cfg = config.Config(script_dir.parent / 'alembic.ini')
    alembic_cfg.set_main_option(
        'script_location', str(script_dir.relative_to(path_utils.REPO_ROOT))
    )
    alembic_cfg.set_main_option('sqlalchemy.url', c._db_url)
    command.upgrade(alembic_cfg, 'head')
    print('Migrations run successfully')


def purge_tables(c: client.DbClient) -> None:
    schema.Base.metadata.drop_all(c.engine)
    print('Tables purged successfully')
    create_tables(c)


@click.command()
@click.option('--action', type=click_utils.EnumChoice(Action), required=True)
def main(action: Action) -> None:
    c = client.DbClient()

    if action is Action.CREATE:
        create_tables(c)
    elif action is Action.MIGRATE:
        run_migrations(c)
    elif action is Action.PURGE:
        purge_tables(c)


if __name__ == '__main__':
    main()

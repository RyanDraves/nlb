import os
import pathlib

import dotenv
import sqlalchemy
from sqlalchemy import engine
from sqlalchemy import orm

from apps.hyd.management import schema


class DbClient:
    DB_HOST = 'localhost'
    DB_PORT = 5432
    DB_NAME = 'hyd'

    def __init__(self, loadenv: bool = True):
        if loadenv:
            envfile = pathlib.Path(__file__).parent.parent / '.env'
            dotenv.load_dotenv(envfile, override=True)

        self._engine = sqlalchemy.create_engine(self._db_url)
        self.__session = orm.sessionmaker(bind=self._engine)()

        self._conn: engine.Connection | None = None

    @property
    def _db_url(self) -> str:
        username = os.getenv('POSTGRES_USER', 'hyd')
        password = os.getenv('POSTGRES_PASSWORD', 'example_password')
        return (
            os.environ.get('DATABASE_URL')
            or f'postgresql://{username}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
        )

    @property
    def _session(self) -> orm.Session:
        if self._conn is None:
            try:
                self._conn = self._engine.connect()
            except Exception as e:
                raise Exception(f'Error connecting to the database: {e}')

        return self.__session

    @property
    def engine(self) -> sqlalchemy.Engine:
        return self._engine

    def create_task_progress(
        self, label: str, init_value: int, max_value: int, status: str | None
    ) -> int:
        progress = schema.TaskProgress(
            label=label, value=init_value, max_value=max_value, status=status
        )
        self._session.add(progress)
        self._session.commit()
        return progress.id  # type: ignore

    def update_task_progress(
        self, label_or_id: str | int, value: int | None, status: str | None
    ) -> None:
        if isinstance(label_or_id, int):
            progress = self._session.query(schema.TaskProgress).get(label_or_id)
        else:
            progress = (
                self._session.query(schema.TaskProgress)
                .filter_by(label=label_or_id)
                .first()
            )

        if progress is None:
            raise ValueError(f'No task with label {label_or_id} found')

        if value is not None:
            progress.value = value  # type: ignore
        if status is not None:
            progress.status = status  # type: ignore
        self._session.commit()

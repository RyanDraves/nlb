from typing import Generator, Required, Self, Sequence, TypedDict

import requests
from rich import console
from rich import progress


class TaskProgress(TypedDict, total=False):
    id: int
    label: Required[str]
    value: int
    max_value: int
    status: str


class ProgressBar:
    """Display a progress bar in the console and send updates to a HYD server."""

    def __init__(
        self,
        label: str,
        *,
        max_value: int | None = None,
        endpoint: str = 'http://localhost:3000/api/progress',
        console: console.Console | None = None,
    ):
        self._label = label
        self._max_value = max_value
        self._endpoint = endpoint
        self._value = 0
        self._status: str | None = None

        self._progress = progress.Progress(console=console)
        self._task = self._progress.add_task(label, total=max_value)

    def __enter__(self) -> Self:
        self._progress.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._progress.stop()

    def iter[T](self, iterable: Sequence[T]) -> Generator[T, None, None]:
        self._max_value = len(iterable)
        self._progress.update(self._task, completed=0, total=self._max_value)

        with self:
            for i, item in enumerate(iterable):
                yield item
                self.update_value(i)

    def update_value(
        self,
        value: int,
        index_by_one: bool = True,
    ) -> TaskProgress:
        if index_by_one:
            value += 1
        self._value = value

        payload: TaskProgress = {'label': self._label}
        payload['value'] = self._value
        if self._max_value is not None:
            payload['max_value'] = self._max_value
        if self._status is not None:
            payload['status'] = self._status

        self._progress.update(self._task, completed=self._value)

        response = requests.post(self._endpoint, json=payload)
        response.raise_for_status()
        return response.json()

    def update_status(
        self,
        status: str,
    ) -> TaskProgress:
        payload: TaskProgress = {'label': self._label}
        payload['value'] = self._value
        if self._max_value is not None:
            payload['max_value'] = self._max_value

        self._status = status
        payload['status'] = self._status

        response = requests.post(self._endpoint, json=payload)
        response.raise_for_status()
        return response.json()

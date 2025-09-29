import time


class WallTimer:
    """Simple wall clock timer. It loves to read you the time."""

    def __init__(self):
        self._elapsed_time: float | None = None

    def __enter__(self):
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._elapsed_time = time.time() - self._start_time
        return self

    @property
    def elapsed_time(self) -> float:
        if self._elapsed_time is None:
            raise ValueError('Timer has not been stopped yet')
        return self._elapsed_time

import contextlib
import signal
from types import FrameType
from typing import Generator


class TimeoutError(Exception):
    """Raised when a timeout occurs."""


@contextlib.contextmanager
def timeout(seconds: float) -> Generator[None, None, None]:
    """Context manager that raises TimeoutError if the code block takes too long.

    Args:
        seconds: Maximum time to allow the code block to run.

    Raises:
        TimeoutError: If the code block exceeds the timeout.

    Example:
        with timeout(5.0):
            # Code that should complete within 5 seconds
            some_potentially_long_running_operation()
    """

    def timeout_handler(signum: int, frame: FrameType | None) -> None:
        raise TimeoutError(f'Operation timed out after {seconds} seconds')

    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)

    try:
        yield
    finally:
        # Disable the alarm and restore the old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

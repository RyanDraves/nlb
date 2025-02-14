import functools
import logging
import traceback
from typing import Any, Callable

from IPython.terminal import embed
from IPython.terminal import ipapp


def ipython_on_exception[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Decorator to embed an IPython shell on exception."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f'Exception in {func.__name__}: {e}')
            logging.error(''.join(traceback.format_exception(e)))
            config = ipapp.load_default_config()
            config.InteractiveShellEmbed.colors = 'Linux'
            config.TerminalInteractiveShell.confirm_exit = False

            # Extract the locals of the frame where the exception occurred
            tb = e.__traceback__
            assert tb is not None
            while tb.tb_next:  # Navigate to the innermost traceback
                tb = tb.tb_next
            frame = tb.tb_frame
            local_vars = frame.f_locals

            embed.embed(
                header=f'Exception in {func.__module__}.{func.__name__}',
                config=config,
                stack_depth=2,
                user_ns=local_vars,
            )
            raise

    return wrapper

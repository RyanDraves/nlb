import enum

import rich_click as click

from nlb.sharetrace import st
from nlb.util import click_utils


class Demos(enum.Enum):
    SIMPLE = enum.auto()
    NESTED = enum.auto()
    CONTEXT = enum.auto()


def test_division_by_zero():
    """Function that will cause a ZeroDivisionError."""
    x = 10
    y = 0
    return x / y


def test_simple_error():
    """Function that calls another function that errors."""
    test_division_by_zero()


def inner_nested_function():
    """Function that will cause the original exception."""
    x = 5
    raise ValueError(f'Original error in inner function {x=}')


def middle_nested_function():
    """Function that catches and re-raises with a different exception."""
    try:
        inner_nested_function()
    except ValueError as e:
        raise RuntimeError('Error in middle function') from e


def outer_nested_function():
    """Function that catches and re-raises again."""
    try:
        middle_nested_function()
    except RuntimeError as e:
        raise TypeError('Error in outer function') from e


def test_context_error():
    """Function that will cause an exception during cleanup."""
    try:
        raise ValueError('Original error')
    except ValueError:
        # This will create a context relationship (not cause)
        raise RuntimeError('Error during cleanup')


@click.command()
@click.option(
    '--demo',
    type=click_utils.EnumChoice(Demos),
    default=Demos.SIMPLE,
    required=True,
    help='Demo to run',
)
def main(demo: Demos) -> None:
    """Demo script to create a sample trace file"""
    # Install the exception hook
    st.install_exception_hook()

    print(f'Testing {demo.name.lower()} sharetrace exception capturing...')

    if demo is Demos.SIMPLE:
        test_simple_error()
    elif demo is Demos.NESTED:
        outer_nested_function()
    elif demo is Demos.CONTEXT:
        test_context_error()


if __name__ == '__main__':
    main(prog_name='sharetrace_demo')

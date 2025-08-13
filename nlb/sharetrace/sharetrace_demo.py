import rich_click as click

from nlb.sharetrace import st


def test_division_by_zero():
    """Function that will cause a ZeroDivisionError."""
    x = 10
    y = 0
    return x / y


def test_nested_error():
    """Function that calls another function that errors."""
    test_division_by_zero()


@click.command()
def main():
    """Demo script to create a sample trace file"""
    # Install the exception hook
    st.install_exception_hook()

    print('Testing sharetrace exception capturing...')
    print('This will cause a ZeroDivisionError to be captured.')

    # This will trigger the exception hook
    test_nested_error()


if __name__ == '__main__':
    main(prog_name='sharetrace_demo')

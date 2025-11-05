import difflib
import unittest


def assertTextEqual(
    test: unittest.TestCase, actual: str, expected: str, msg: str | None = None
) -> None:
    """Assert two text strings are equal with a colorful unified diff on failure."""
    if actual == expected:
        return

    actual_lines = actual.splitlines(keepends=True)
    expected_lines = expected.splitlines(keepends=True)

    diff = difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile='expected',
        tofile='actual',
        lineterm='',
    )

    # ANSI color codes
    RED = '\033[91m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

    colored_diff = []
    for line in diff:
        line = line.rstrip()
        if line.startswith('+++') or line.startswith('---'):
            colored_diff.append(f'{CYAN}{line}{RESET}')
        elif line.startswith('+'):
            colored_diff.append(f'{GREEN}{line}{RESET}')
        elif line.startswith('-'):
            colored_diff.append(f'{RED}{line}{RESET}')
        elif line.startswith('@@'):
            colored_diff.append(f'{CYAN}{line}{RESET}')
        else:
            colored_diff.append(line)

    diff_output = '\n'.join(colored_diff)
    error_msg = f'\n\nTexts are not equal:\n{diff_output}\n'
    if msg:
        error_msg = f'{msg}\n{error_msg}'

    test.fail(error_msg)

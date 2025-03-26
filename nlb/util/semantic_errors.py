from typing import Protocol

from thefuzz import fuzz


class IsStringable(Protocol):
    def __str__(self) -> str: ...


def find_best_match[T: IsStringable](
    input_str: str, choices: list[T], min_ratio: int = 70
) -> T | None:
    """
    Find the best match for the input string from a list of choices using fuzzy string matching.

    Args:
        input_str: The input string to match.
        choices: A list of strings to match against.
        min_ratio: The minimum matching ratio to consider a match valid.

    Returns:
        The best matching string from the choices, or an empty string if no match is found.
    """
    best_match = None
    best_ratio = min_ratio

    for choice in choices:
        ratio = fuzz.ratio(input_str, str(choice))
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = choice

    return best_match

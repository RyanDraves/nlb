import itertools

from nlb.models.blockworld import environment


def permutations_of_target(target: int = 5) -> list[list[int]]:
    return list(itertools.permutations(range(target)))  # type: ignore


def find_permutations_sum_to_target(target: int = 5) -> list[list[int]]:
    """Find a permutation of n numbers that sum to target."""
    permutations = []
    # Tuples of 3 numbers that sum to target
    for i in range(target + 1):
        for j in range(target + 1):
            k = target - i - j
            if 0 <= k <= target:
                permutations.append([i, j, k])
    return permutations


def hash_permutation_sum_to_target(numbers: list[int], target: int) -> int:
    """Hash 3 numbers that sum to target"""
    # There are (target + 1)(target + 2)/2 such tuples
    assert len(numbers) == 3
    assert sum(numbers) == target

    i, j, k = numbers
    # Map (i, j, k) to unique index where i + j + k = target
    # We can think of this as choosing i from [0, target] and j from [0, target-i]
    # The hash is the sum of all possible j values for smaller i values, plus j
    hash_value = 0
    for prev_i in range(i):
        # For each previous i, j can range from 0 to target - prev_i
        hash_value += target - prev_i + 1
    hash_value += j
    return hash_value


def hash_permutation(numbers: list[int]) -> int:
    """Hash a permutation of 5 numbers"""
    assert len(numbers) == 5
    # There are 5! = 120 permutations of 5 numbers
    h = 0
    factor = 1
    for i in range(5):
        smaller_count = sum(1 for x in numbers[i + 1 :] if x < numbers[i])
        h += smaller_count * factor
        factor *= 5 - i
    return h


def hash_state(state: environment.State) -> int:
    """A simple hash function for a block world state."""
    sizes = [len(state[0]), len(state[1]), len(state[2])]
    # Flatten the state and compute a hash
    flat_state = state[0] + state[1] + state[2]
    return (
        hash_permutation(flat_state)
        + hash_permutation_sum_to_target(sizes, sum(sizes)) * 120
    )

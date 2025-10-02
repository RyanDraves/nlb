import itertools
import math
from typing import Generator

from nlb.models.blockworld import environment


def _permutations_of_target(target: int = 5) -> Generator[list[int], None, None]:
    return itertools.permutations(range(target))  # type: ignore


def _find_permutations_sum_to_target(
    target: int = 5,
) -> Generator[list[int], None, None]:
    """Find all permutations of 3 numbers that sum to target."""
    # Tuples of 3 numbers that sum to target
    for i in range(target + 1):
        for j in range(target + 1):
            k = target - i - j
            if 0 <= k <= target:
                yield [i, j, k]


def _hash_permutation_sum_to_target(numbers: list[int], target: int) -> int:
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


def _hash_permutation(numbers: list[int]) -> int:
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


class BlockworldSampleMdp:
    def __init__(self, num_blocks: int):
        self._num_blocks = num_blocks
        self._actions = list(environment.Action)

    def states(self) -> Generator[environment.State, None, None]:
        for perm in _permutations_of_target(self._num_blocks):
            for sizes in _find_permutations_sum_to_target(self._num_blocks):
                state: environment.State = [[], [], []]
                index = 0
                for stack_index, size in enumerate(sizes):
                    for _ in range(size):
                        state[stack_index].append(perm[index])
                        index += 1
                yield state

    def state_index(self, state: environment.State) -> int:
        sizes = [len(state[0]), len(state[1]), len(state[2])]
        # Flatten the state and compute a hash
        flat_state = state[0] + state[1] + state[2]
        assert len(flat_state) == self._num_blocks
        assert sum(sizes) == self._num_blocks
        num_block_permutations = math.factorial(self._num_blocks)
        return (
            _hash_permutation(flat_state)
            + _hash_permutation_sum_to_target(sizes, self._num_blocks)
            * num_block_permutations
        )

    def actions(self) -> Generator[environment.Action, None, None]:
        for action in self._actions:
            yield action

    def action_index(self, action: environment.Action) -> int:
        return self._actions.index(action)

    def reward(self, state: environment.State, action: environment.Action) -> float:
        reward = -1.0  # Action cost
        if state[2] == list(range(self._num_blocks)):
            reward += 30.0
        return reward

    def transition(
        self, state: environment.State, action: environment.Action
    ) -> list[tuple[environment.State, float]]:
        next_state = [state[0].copy(), state[1].copy(), state[2].copy()]
        src, dst = environment.ACTION_MAP[action]
        src -= 1
        dst -= 1
        if next_state[src]:
            block = next_state[src].pop()
            next_state[dst].append(block)
        return [(next_state, 1.0)]

    def gamma(self) -> float:
        return 0.95

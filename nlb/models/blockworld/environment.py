import enum

import numpy as np

from nlb.util import console_utils

State = list[list[int]]


class Action(enum.Enum):
    MOVE_1_TO_2 = 'MOVE_1_TO_2'
    MOVE_1_TO_3 = 'MOVE_1_TO_3'
    MOVE_2_TO_1 = 'MOVE_2_TO_1'
    MOVE_2_TO_3 = 'MOVE_2_TO_3'
    MOVE_3_TO_1 = 'MOVE_3_TO_1'
    MOVE_3_TO_2 = 'MOVE_3_TO_2'


ACTION_MAP: dict[Action, tuple[int, int]] = {
    Action.MOVE_1_TO_2: (1, 2),
    Action.MOVE_1_TO_3: (1, 3),
    Action.MOVE_2_TO_1: (2, 1),
    Action.MOVE_2_TO_3: (2, 3),
    Action.MOVE_3_TO_1: (3, 1),
    Action.MOVE_3_TO_2: (3, 2),
}


def action_from_tuple(action: tuple[int, int]) -> Action:
    for act, (src, dst) in ACTION_MAP.items():
        if (src, dst) == action:
            return act
    raise ValueError(f'Invalid action tuple: {action}')


def state_str(state: State) -> str:
    return '\n'.join(f'Stack {i + 1}: {stack}' for i, stack in enumerate(state))


class Environment:
    def __init__(self, num_blocks: int):
        self._console = console_utils.Console()

        blocks = np.random.randint(0, 3, size=num_blocks)

        # 3 stacks of blocks
        self._stacks: State = [[] for _ in range(3)]
        for i, stack in enumerate(blocks):
            self._stacks[stack].append(i)

        self._initial_state = [stack.copy() for stack in self._stacks]
        self._step = 0

    def act(self, action: Action) -> None:
        src, dst = ACTION_MAP[action]
        src -= 1
        dst -= 1

        self._step += 1

        if not self._stacks[src]:
            self._console.warning(f'Invalid action on step {self._step}: {action.name}')
            return

        block = self._stacks[src].pop()
        self._stacks[dst].append(block)

    def get_state(self) -> State:
        return [stack.copy() for stack in self._stacks]

    def terminal(self) -> bool:
        return (
            len(self._stacks[0]) == 0
            and len(self._stacks[1]) == 0
            and all(i == block for i, block in enumerate(self._stacks[2]))
        )

    def reset(self) -> None:
        self._stacks = [stack.copy() for stack in self._initial_state]
        self._step = 0

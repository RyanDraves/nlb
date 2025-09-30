import dataclasses
import enum
from typing import cast

import numpy as np
from numpy import typing as npt

from nlb.util import console_utils


@dataclasses.dataclass
class State:
    # 0=empty, 1=X, -1=O
    grid: npt.NDArray[np.int_]
    anom_pos: tuple[float, float] | None
    anom_has_spawned: bool

    def _cell_str(self, cell: int) -> str:
        if cell == 1:
            return 'X'
        elif cell == -1:
            return 'O'
        else:
            return '.'

    def __repr__(self) -> str:
        grid_str = '\n'.join(
            ' '.join(self._cell_str(cell) for cell in row) for row in self.grid
        )
        anom_str = (
            f'Anomaly at {self.anom_pos}' if self.anom_pos is not None else 'No anomaly'
        )
        return f'Grid:\n{grid_str}\n{anom_str}'


class Action(enum.Enum):
    PLACE_0_0 = (0, 0)
    PLACE_0_1 = (0, 1)
    PLACE_0_2 = (0, 2)
    PLACE_1_0 = (1, 0)
    PLACE_1_1 = (1, 1)
    PLACE_1_2 = (1, 2)
    PLACE_2_0 = (2, 0)
    PLACE_2_1 = (2, 1)
    PLACE_2_2 = (2, 2)
    MOVE_ANOM_LEFT = enum.auto()
    MOVE_ANOM_RIGHT = enum.auto()
    MOVE_ANOM_UP = enum.auto()
    MOVE_ANOM_DOWN = enum.auto()
    NO_OP = enum.auto()


class Environment:
    def __init__(self, anom_chance: float):
        self._anom_chance = anom_chance
        self._console = console_utils.Console()

        self._state = State(
            grid=np.zeros((3, 3), dtype=int),
            anom_pos=None,
            anom_has_spawned=False,
        )

        self._turn = 0

    def act(self, action: Action) -> None:
        if action in {
            Action.PLACE_0_0,
            Action.PLACE_0_1,
            Action.PLACE_0_2,
            Action.PLACE_1_0,
            Action.PLACE_1_1,
            Action.PLACE_1_2,
            Action.PLACE_2_0,
            Action.PLACE_2_1,
            Action.PLACE_2_2,
        }:
            if self._turn % 2 == 0:
                piece = 1
            else:
                piece = -1

            row, col = cast(tuple[int, int], action.value)
            self._turn += 1

            if self._state.grid[row, col] != 0:
                self._console.warning(
                    f'Invalid action: cell {row, col} is already occupied'
                )
            elif self._state.anom_pos is not None:
                self._console.warning('Invalid action: anomaly is present on the board')
            else:
                self._state.grid[row, col] = piece

        elif action in {
            Action.MOVE_ANOM_LEFT,
            Action.MOVE_ANOM_RIGHT,
            Action.MOVE_ANOM_UP,
            Action.MOVE_ANOM_DOWN,
        }:
            if self._state.anom_pos is None:
                self._console.warning('Invalid action: anomaly has not spawned')
            else:
                row, col = self._state.anom_pos
                if action == Action.MOVE_ANOM_LEFT:
                    col -= 0.5
                elif action == Action.MOVE_ANOM_RIGHT:
                    col += 0.5
                elif action == Action.MOVE_ANOM_UP:
                    row -= 0.5
                elif action == Action.MOVE_ANOM_DOWN:
                    row += 0.5

                self._state.anom_pos = (row, col)
                if not (0 <= row <= 3 and 0 <= col <= 3):
                    self._state.anom_pos = None

        # Maybe spawn the anomaly
        if not self._state.anom_has_spawned and np.random.rand() < self._anom_chance:
            # Spawn in a random position in [0.5, 2.5] x [0.5, 2.5] with 0.5 increments
            self._state.anom_pos = (
                np.random.choice([0.5, 1.0, 1.5, 2.0, 2.5]).item(),
                np.random.choice([0.5, 1.0, 1.5, 2.0, 2.5]).item(),
            )
            self._state.anom_has_spawned = True

    def get_state(self) -> State:
        return dataclasses.replace(self._state, grid=self._state.grid.copy())

    def terminal(self) -> bool:
        # Game ends when all cells are filled or there's a 3-in-a-row
        for i in range(3):
            if abs(np.sum(self._state.grid[i, :])) == 3:
                return True
            if abs(np.sum(self._state.grid[:, i])) == 3:
                return True
        if abs(np.sum(np.diag(self._state.grid))) == 3:
            return True
        if abs(np.sum(np.diag(np.fliplr(self._state.grid)))) == 3:
            return True
        return np.all(self._state.grid != 0).item()

    def reset(self) -> None:
        self._state = State(
            grid=np.zeros((3, 3), dtype=int),
            anom_pos=None,
            anom_has_spawned=False,
        )
        self._turn = 0

    def player_two_policy(self) -> Action:
        """Play a semi-random policy for player two (O, -1)"""
        if self._state.anom_pos is not None or self._turn % 2 == 0:
            return Action.NO_OP

        if self._state.grid[1, 1] == 0:
            self._state.grid[1, 1] = -1
        else:
            empty_cells = np.argwhere(self._state.grid == 0)
            if empty_cells.size > 0:
                chosen_cell = empty_cells[np.random.choice(len(empty_cells))]
                return Action((chosen_cell[0], chosen_cell[1]))

        # If no empty cells, do nothing
        return Action.NO_OP

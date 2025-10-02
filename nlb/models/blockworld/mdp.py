from typing import Generator, Protocol

import numpy as np
from numpy import typing as npt

from nlb.models.blockworld import environment


class MDP(Protocol):
    def states(self) -> Generator[environment.State, None, None]: ...

    def state_index(self, state: environment.State) -> int: ...

    def actions(self) -> Generator[environment.Action, None, None]: ...

    def action_index(self, action: environment.Action) -> int: ...

    def reward(self, state: environment.State, action: environment.Action) -> float: ...

    def transition(
        self, state: environment.State, action: environment.Action
    ) -> list[tuple[environment.State, float]]:
        """Transition a state-action pair into (next_state, probability) pairs."""
        ...

    def gamma(self) -> float: ...


def value_iteration(
    mdp: MDP, tol: float = 1e-5, max_iterations: int = 1000
) -> npt.NDArray[np.int32]:
    num_states = sum(1 for _ in mdp.states())
    num_actions = sum(1 for _ in mdp.actions())

    V: npt.NDArray[np.float64] = np.zeros(num_states, dtype=np.float64)
    policy: npt.NDArray[np.int32] = np.zeros(num_states, dtype=np.int32)

    for i in range(max_iterations):
        delta = 0.0
        for state in mdp.states():
            s_idx = mdp.state_index(state)
            v = V[s_idx]
            q_values = np.zeros(num_actions, dtype=np.float64)
            for action in mdp.actions():
                a_idx = mdp.action_index(action)
                r = mdp.reward(state, action)
                q = r
                for next_state, prob in mdp.transition(state, action):
                    ns_idx = mdp.state_index(next_state)
                    q += mdp.gamma() * prob * V[ns_idx]
                q_values[a_idx] = q
            V[s_idx] = np.max(q_values)
            policy[s_idx] = np.argmax(q_values)
            delta = max(delta, abs(v - V[s_idx]))
        if delta < tol:
            iterations = i + 1
            print(f'Value iteration converged in {iterations} iterations.')
            break
    else:
        print(
            'Warning: Value iteration did not converge within the maximum iterations.'
        )

    return policy

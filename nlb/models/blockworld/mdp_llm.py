import pathlib
import tempfile
from importlib import util
from types import ModuleType

import agents
from numpy import typing as npt
from openai.types import shared

from nlb.models.blockworld import environment
from nlb.models.blockworld import mdp
from nlb.models.blockworld import metrics
from nlb.util import console_utils
from nlb.util import timeout

_SYSTEM_PROMPT = '''You are modeling an MDP for a block world environment.

Your goal is to model an MDP that, when solved, will create a policy to
sort the blocks in ascending order on the third stack (Stack 3).
Each action involves moving the top block from one stack to another.
Use the provided tool to write Python code that models this MDP.

An example system state would be:
Stack 1: [2, 0]
Stack 2: [1]
Stack 3: [3, 4]

Where the goal state is:
Stack 1: []
Stack 2: []
Stack 3: [0, 1, 2, 3, 4]

Your code will be a complete module. It should implement the following signature:
```python
import itertools
from typing import Generator

from nlb.models.blockworld import environment

class MDP:
    def __init__(self, num_blocks: int): ...

    def states(self) -> Generator[environment.State, None, None]:
        """Enumerate all possible states of the environment."""
        ...

    def state_index(self, state: environment.State) -> int: ...

    def actions(self) -> Generator[environment.Action, None, None]:
        """Enumerate all possible actions in the environment."""
        ...

    def action_index(self, action: environment.Action) -> int: ...

    def reward(self, state: environment.State, action: environment.Action) -> float: ...

    def transition(
        self, state: environment.State, action: environment.Action
    ) -> list[tuple[environment.State, float]]:
        """Transition a state-action pair into (next_state, probability) pairs."""
        ...

    def gamma(self) -> float: ...
```

The following interfaces are in the `environment` module:
```python
# Three stacks of blocks, each represented as a list of integers.
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
```

The created MDP will be solved with a simple vectorized value iteration algorithm,
so it is important that the `state_index` and `action_index` methods return
consistent and correct indices.
'''


class MdpLlmPlanner:
    def __init__(
        self,
        num_blocks: int,
        model: str,
        reasoning_effort: shared.ReasoningEffort,
        value_iteration_timeout_s: float = 600.0,
    ):
        self._console = console_utils.Console()
        self._num_blocks = num_blocks
        self._value_iteration_timeout_s = value_iteration_timeout_s

        self._agent = agents.Agent(
            name='MdpLlmPlanner',
            model=model,
            model_settings=agents.ModelSettings(
                reasoning=shared.Reasoning(effort=reasoning_effort), verbosity='low'
            ),
            tools=[create_mdp],
            instructions=_SYSTEM_PROMPT,
        )

        self._mdp: mdp.MDP | None = None
        self._policy: npt.NDArray | None = None

        self._mdp_path = pathlib.Path(
            tempfile.NamedTemporaryFile(suffix='.py', delete_on_close=False).name
        )
        self._mdp_code: str | None = None
        self._mdp_module: ModuleType | None = None
        self._tried_generation = False

    def _action_from_action_index(self, action_index: int) -> environment.Action:
        """Convert an action index to an Action enum."""
        return list(environment.Action)[action_index]

    def mdp_llm_policy(
        self, state: environment.State, result: metrics.Result
    ) -> environment.Action:
        """LLM-generated MDP policy for the block world environment."""
        if (self._mdp is None or self._policy is None) and not self._tried_generation:
            self._console.info('Generating MDP model using LLM...')

            agent_result = agents.Runner().run_sync(
                self._agent,
                input='Generate the MDP model code.',
                context=self,
            )
            result.input_tokens += agent_result.context_wrapper.usage.input_tokens
            result.output_tokens += agent_result.context_wrapper.usage.output_tokens

            self._tried_generation = True
            if self._mdp_code is None:
                self._console.error(
                    'LLM failed to generate MDP model code. Taking arbitrary action.'
                )
                return environment.Action.MOVE_1_TO_2  # Arbitrary action

            # Load the generated MDP module
            self._mdp_path.write_text(self._mdp_code)
            self._console.info(f'Wrote mdp to {self._mdp_path}')
            spec = util.spec_from_file_location(
                'nlb.modules.blockworld.mdp_llm_model', self._mdp_path
            )
            if spec is None or spec.loader is None:
                self._console.error(
                    'Failed to load generated MDP model code. Taking arbitrary action.'
                )
                return environment.Action.MOVE_1_TO_2  # Arbitrary action
            self._console.info(f'Loading spec from {self._mdp_path}')
            self._mdp_module = util.module_from_spec(spec)
            try:
                self._console.info('Executing the generated policy module...')
                spec.loader.exec_module(self._mdp_module)
            except Exception as e:
                self._console.error(
                    f'Error executing generated MDP model code: {e}. Taking arbitrary action.'
                )
                self._console.info(f'Generated code:\n{self._mdp_code}')
                return environment.Action.MOVE_1_TO_2  # Arbitrary action
            if not hasattr(self._mdp_module, 'MDP'):
                self._console.error(
                    'Generated module does not have an MDP class. Taking arbitrary action.'
                )
                return environment.Action.MOVE_1_TO_2  # Arbitrary action

            try:
                self._mdp = self._mdp_module.MDP(num_blocks=self._num_blocks)
                assert self._mdp is not None

                self._console.info('Generating MDP policy using value iteration...')
                with timeout.timeout(self._value_iteration_timeout_s):
                    self._policy = mdp.value_iteration(self._mdp)
            except (Exception, timeout.TimeoutError) as e:
                self._console.error(
                    f'Error creating MDP or generating policy: {e}. Taking arbitrary action.'
                )
                return environment.Action.MOVE_1_TO_2  # Arbitrary action
        elif self._mdp is None or self._policy is None:
            return environment.Action.MOVE_1_TO_2  # Arbitrary action

        try:
            state_index = self._mdp.state_index(state)
            return self._action_from_action_index(self._policy[state_index])
        except Exception as e:
            self._console.error(
                f'Error getting action from policy: {e}. Taking arbitrary action.'
            )
            return environment.Action.MOVE_1_TO_2  # Arbitrary action


@agents.function_tool
def create_mdp(clz: agents.RunContextWrapper[MdpLlmPlanner], mdp_code: str) -> None:
    """Create a heuristic policy for sorting blocks.

    Args:
        mdp_code: The code implementing the MDP model.
    """
    clz.context._mdp_code = mdp_code

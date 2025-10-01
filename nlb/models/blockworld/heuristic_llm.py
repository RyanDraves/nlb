import pathlib
import tempfile
from importlib import util
from types import ModuleType

import agents
from openai.types import shared

from nlb.models.blockworld import environment
from nlb.models.blockworld import metrics
from nlb.util import console_utils

_SYSTEM_PROMPT = '''You are coding a heuristic policy for a block world environment.

Your goal is to sort the blocks in ascending order on the third stack (Stack 3).
Each action involves moving the top block from one stack to another.
Use the provided tool to write Python code that sorts the blocks.

An example system state would be:
Stack 1: [2, 0]
Stack 2: [1]
Stack 3: [3, 4]

Where the goal state is:
Stack 1: []
Stack 2: []
Stack 3: [0, 1, 2, 3, 4]

Your code will be a complete module. It should define the following function signature:
```python
from nlb.models.blockworld import environment

def heuristic_policy(state: environment.State) -> environment.Action:
    ...
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

def action_from_tuple(action: tuple[int, int]) -> Action:
    """Convert a (src, dst) tuple to an Action enum."""
    ...
```
'''


class HeuristicLlmPlanner:
    def __init__(self, model: str, reasoning_effort: shared.ReasoningEffort):
        self._console = console_utils.Console()

        self._agent = agents.Agent(
            name='HeuristicLlmPlanner',
            model=model,
            model_settings=agents.ModelSettings(
                reasoning=shared.Reasoning(effort=reasoning_effort), verbosity='low'
            ),
            tools=[create_heuristic_policy],
            instructions=_SYSTEM_PROMPT,
        )

        self._policy_path = pathlib.Path(
            tempfile.NamedTemporaryFile(suffix='.py', delete_on_close=False).name
        )
        self._policy_code: str | None = None
        self._policy_module: ModuleType | None = None
        self._tried_generation = False

    def heuristic_llm(
        self, state: environment.State, result: metrics.Result
    ) -> environment.Action:
        """Heuristic LLM-generated policy for the block world environment."""
        if self._policy_module is None and not self._tried_generation:
            self._console.info('Generating heuristic policy using LLM...')

            agent_result = agents.Runner().run_sync(
                self._agent,
                input='Generate the heuristic policy code.',
                context=self,
            )
            result.input_tokens += agent_result.context_wrapper.usage.input_tokens
            result.output_tokens += agent_result.context_wrapper.usage.output_tokens

            self._tried_generation = True
            if self._policy_code is None:
                self._console.error(
                    'LLM failed to generate a plan. Taking arbitrary action.'
                )
                return environment.Action.MOVE_1_TO_2  # Arbitrary action

            # Load the generated policy code as a module
            self._policy_path.write_text(self._policy_code)
            spec = util.spec_from_file_location(
                'nlb.modules.blockworld.heuristic_llm_policy', self._policy_path
            )
            if spec is None or spec.loader is None:
                self._console.error(
                    'Failed to load the generated policy module. Taking arbitrary action.'
                )
                return environment.Action.MOVE_1_TO_2  # Arbitrary action
            self._policy_module = util.module_from_spec(spec)
            try:
                spec.loader.exec_module(self._policy_module)
            except Exception as e:
                self._console.error(
                    f'Failed to execute the generated policy module: {e}. Taking arbitrary action.'
                )
                self._console.info(f'Generated code:\n{self._policy_code}')
                return environment.Action.MOVE_1_TO_2  # Arbitrary action
            if not hasattr(self._policy_module, 'heuristic_policy'):
                self._console.error(
                    'Generated module does not have a heuristic_policy function. Taking arbitrary action.'
                )
                return environment.Action.MOVE_1_TO_2  # Arbitrary action
        elif self._tried_generation:
            return environment.Action.MOVE_1_TO_2  # Arbitrary action

        return self._policy_module.heuristic_policy(state)  # type: ignore


@agents.function_tool
def create_heuristic_policy(
    clz: agents.RunContextWrapper[HeuristicLlmPlanner], policy_code: str
) -> None:
    """Create a heuristic policy for sorting blocks.

    Args:
        policy_code: The code implementing the heuristic policy.
    """
    clz.context._policy_code = policy_code

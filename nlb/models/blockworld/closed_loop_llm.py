import agents
from openai.types import shared

from nlb.models.blockworld import environment
from nlb.models.blockworld import metrics
from nlb.util import console_utils

_SYSTEM_PROMPT = """You are a robotic arm in a block world environment.

Your goal is to sort the blocks in ascending order on the third stack (Stack 3).
Each action involves moving the top block from one stack to another.
Use the provided tool to select the next action to achieve this goal.

An example system state would be:
Stack 1: [2, 0]
Stack 2: [1]
Stack 3: [3, 4]

Where the goal state is:
Stack 1: []
Stack 2: []
Stack 3: [0, 1, 2, 3, 4]
"""


class ClosedLoopPlanner:
    def __init__(self, model: str, reasoning_effort: shared.ReasoningEffort):
        self._console = console_utils.Console()

        self._agent = agents.Agent(
            name='ClosedLoopBlockworldPlanner',
            model=model,
            model_settings=agents.ModelSettings(
                reasoning=shared.Reasoning(effort=reasoning_effort), verbosity='low'
            ),
            tools=[select_action],
            instructions=_SYSTEM_PROMPT,
        )

        self._next_action: environment.Action | None = None

    def closed_loop_llm(
        self, state: environment.State, result: metrics.Result
    ) -> environment.Action:
        """Closed-loop LLM policy for the block world environment."""
        self._console.info('Generating action using LLM...')

        agent_result = agents.Runner().run_sync(
            self._agent,
            input=f'Generate the next action for the following state:\n{environment.state_str(state)}',
            context=self,
        )
        result.input_tokens += agent_result.context_wrapper.usage.input_tokens
        result.output_tokens += agent_result.context_wrapper.usage.output_tokens

        if self._next_action is None:
            self._console.error(
                'LLM failed to generate a plan. Taking arbitrary action.'
            )
            return environment.Action.MOVE_1_TO_2  # Arbitrary action

        return self._next_action


@agents.function_tool
def select_action(
    clz: agents.RunContextWrapper[ClosedLoopPlanner], action: environment.Action
) -> None:
    """Select the next action to take to sort the blocks.

    Args:
        action: The action to be taken.
    """
    clz.context._next_action = action

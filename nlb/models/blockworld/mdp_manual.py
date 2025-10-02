from nlb.models.blockworld import blockworld_sample_mdp
from nlb.models.blockworld import environment
from nlb.models.blockworld import mdp
from nlb.models.blockworld import metrics
from nlb.util import console_utils


class MdpPlanner:
    def __init__(self, num_blocks: int):
        self._console = console_utils.Console()

        self._mdp = blockworld_sample_mdp.BlockworldSampleMdp(num_blocks=num_blocks)
        self._policy = None

    def _action_from_action_index(self, action_index: int) -> environment.Action:
        """Convert an action index to an Action enum."""
        return list(environment.Action)[action_index]

    def mdp_policy(
        self, state: environment.State, result: metrics.Result
    ) -> environment.Action:
        """LLM-generated MDP policy for the block world environment."""
        if self._policy is None:
            self._console.info('Generating MDP policy using value iteration...')
            self._policy = mdp.value_iteration(self._mdp)
        state_index = self._mdp.state_index(state)
        return self._action_from_action_index(self._policy[state_index])

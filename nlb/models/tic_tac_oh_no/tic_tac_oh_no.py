import pathlib

import numpy as np
import rich_click as click

from nlb.models.tic_tac_oh_no import environment
from nlb.models.tic_tac_oh_no import plot
from nlb.util import console_utils


@click.command()
def main() -> None:
    np.random.seed(42)
    env = environment.Environment(anom_chance=0.2)
    console = console_utils.Console()

    states = [env.get_state()]
    action_plan = [
        environment.Action.PLACE_1_1,
        environment.Action.MOVE_ANOM_RIGHT,
        environment.Action.MOVE_ANOM_RIGHT,
        environment.Action.PLACE_0_0,
        environment.Action.PLACE_2_2,
    ]
    actions = []
    max_steps = 20
    step = 0
    while not env.terminal() and step < max_steps:
        # Act on the policy
        console.print(env.get_state())
        action = (
            action_plan[step] if step < len(action_plan) else environment.Action.NO_OP
        )
        console.print(f'Action: {action}')
        env.act(action)
        states.append(env.get_state())
        actions.append(action)

        if not env.terminal():
            # Player 2 action
            console.print(env.get_state())
            p2_action = env.player_two_policy()
            env.act(p2_action)
            states.append(env.get_state())
            actions.append(p2_action)

        step += 1

    console.rule('Final State')
    console.print(env.get_state())
    console.print(f'Terminal: {env.terminal()}')

    plot.plot_environment(
        states, actions, pathlib.Path(__file__).parent / 'plots' / 'tic_tac_oh_no.gif'
    )


if __name__ == '__main__':
    main(prog_name='tic_tac_oh_no')

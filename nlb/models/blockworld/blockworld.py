import os
import pathlib
from typing import Callable

import numpy as np
import rich_click as click
from openai.types import shared

from nlb.models.blockworld import closed_loop_llm
from nlb.models.blockworld import environment
from nlb.models.blockworld import heuristic
from nlb.models.blockworld import metrics
from nlb.models.blockworld import open_loop_llm
from nlb.models.blockworld import plot
from nlb.util import click_utils
from nlb.util import console_utils
from nlb.util import dataframe
from nlb.util import path_utils
from nlb.util import secrets
from nlb.util import timer


def _save_results(
    results: list[metrics.Result], output: pathlib.Path, console: console_utils.Console
) -> None:
    df = dataframe.dataframe_from_type(metrics.Result, results)
    df.to_csv(output, index=False)
    console.info(f'Results saved to {output.relative_to(path_utils.REPO_ROOT)}.')


@click.command()
@click.option(
    '--num-blocks',
    '-n',
    type=int,
    default=5,
    help='Number of blocks in the environment',
)
@click.option(
    '--monte-carlo',
    '-m',
    type=int,
    help='Number of monte carlo runs to average over (default: 1)',
)
@click.option(
    '--policy',
    '-p',
    type=click_utils.EnumChoice(metrics.Policy),
    multiple=True,
    help='Policy(ies) to use',
)
@click.option(
    '--make-gif',
    is_flag=True,
    help='Whether to create a GIF of the environment execution (1 seed per sim)',
)
def main(
    num_blocks: int,
    monte_carlo: int | None,
    policy: list[metrics.Policy],
    make_gif: bool,
) -> None:
    cur_dir = pathlib.Path(__file__).parent
    console = console_utils.Console()

    results: list[metrics.Result] = []

    # Setup the OpenAI environment
    os.environ['OPENAI_API_KEY'] = secrets.get_secret('openai.key')
    model = 'gpt-5-mini'
    reasoning_efforts: list[shared.ReasoningEffort] = [
        # 'minimal',
        'low',
        # 'medium',
        # 'high',
    ]

    for reasoning_effort in reasoning_efforts:
        open_loop_planner = open_loop_llm.OpenLoopPlanner(model, reasoning_effort)
        closed_loop_planner = closed_loop_llm.ClosedLoopPlanner(model, reasoning_effort)

        policies: dict[
            metrics.Policy,
            Callable[[environment.State, metrics.Result], environment.Action],
        ] = {
            metrics.Policy.HEURISTIC: heuristic.heuristic_policy,
            metrics.Policy.OPEN_LOOP_LLM: open_loop_planner.open_loop_llm,
            metrics.Policy.CLOSED_LOOP_LLM: closed_loop_planner.closed_loop_llm,
        }

        assert reasoning_effort is not None
        rng_seeds = [42] if monte_carlo is None else list(range(monte_carlo))
        for rng_seed in rng_seeds:
            console.rule(f'Reasoning Effort: {reasoning_effort}, Seed: {rng_seed}')
            np.random.seed(rng_seed)
            env = environment.Environment(num_blocks=num_blocks)

            for policy_type, policy_func in policies.items():
                if len(policy) and policy_type not in policy:
                    continue
                console.rule(f'Policy: {policy_type.name}')
                output = (
                    cur_dir
                    / 'plots'
                    / f'blockworld_{num_blocks}_{policy_type.name.lower()}.gif'
                )
                result = metrics.Result(
                    policy=policy_type.name,
                    rng_seed=rng_seed,
                    num_blocks=num_blocks,
                    model=model,
                    reasoning_effort=reasoning_effort,
                )

                env.reset()

                with timer.WallTimer() as wall_timer:
                    # Run the policy
                    states = [env.get_state()]
                    actions = []
                    max_steps = 20
                    while not env.terminal() and len(actions) < max_steps:
                        action = policy_func(env.get_state(), result)
                        env.act(action)
                        states.append(env.get_state())
                        actions.append(action)
                result.wall_time_s = wall_timer.elapsed_time

                console.info(f'Terminal state reached in {len(actions)} steps')

                result.steps = len(actions)
                result.success = env.terminal()
                results.append(result)

                if (
                    monte_carlo is None or rng_seed == min(42, monte_carlo)
                ) and make_gif:
                    plot.plot_environment(num_blocks, states, actions, output=output)

    policy_str = (
        '_'.join(p.name.lower() for p in policy)
        if len(policy)
        else '_'.join(p.name.lower() for p in metrics.Policy)
    )
    results_output = (
        cur_dir
        / f'results_{policy_str}_{num_blocks}_blocks_{monte_carlo if monte_carlo else 1}_runs.csv'
    )
    _save_results(results, results_output, console)


if __name__ == '__main__':
    main(prog_name='blockworld')

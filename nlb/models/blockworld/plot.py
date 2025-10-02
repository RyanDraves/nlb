import io
import pathlib
from typing import Any

import imageio
import numpy as np
import pandas as pd
import rich_click as click
from matplotlib import axes
from matplotlib import figure
from matplotlib import offsetbox
from matplotlib import patches
from matplotlib import pyplot as plt
from numpy import typing as npt
from PIL import Image

from nlb.models.blockworld import environment
from nlb.models.blockworld import metrics
from nlb.util import console_utils
from nlb.util import path_utils

CONSOLE = console_utils.Console()

claw_path = pathlib.Path(__file__).parent / 'claw.png'


def _export_image(fig: figure.Figure, writer: Any) -> None:
    """Export matplotlib figure to numpy array for GIF creation."""
    ios = io.BytesIO()
    fig.savefig(ios, format='raw', dpi=150)
    ios.seek(0)
    w, h = fig.canvas.get_width_height()
    img = np.reshape(
        np.frombuffer(ios.getvalue(), dtype=np.uint8), (int(h), int(w), 4)
    )[:, :, 0:3]  # Remove alpha channel
    writer.append_data(img)


def _load_image(path: pathlib.Path) -> npt.NDArray[np.uint8]:
    try:
        image = Image.open(path)
        return np.array(image)
    except Exception as e:
        CONSOLE.warning(f'Failed to load image {path}: {e}')
        # Return a simple colored square as fallback
        return np.full((10, 10, 3), 128, dtype=np.uint8)


def plot_state(
    num_blocks: int, state: environment.State, lifted: int | None = None
) -> tuple[figure.Figure, axes.Axes]:
    fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
    colors = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'cyan', 'magenta']

    ax.set_ylim(0, num_blocks + 1)
    ax.set_xlim(0, 3)

    # For each stack, plot the blocks as rectangles
    for i, stack in enumerate(state):
        for j, block in enumerate(stack):
            block_x = i
            block_y = j
            if lifted == i + 1 and j == len(stack) - 1:
                block_y = num_blocks - 0.5  # Move lifted block to top
            rect = patches.Rectangle(
                (block_x + 0.325, block_y),
                0.35,
                1,
                linewidth=1,
                edgecolor='black',
                facecolor=colors[block % len(colors)],
                alpha=0.85,
            )
            ax.add_patch(rect)
            ax.text(
                block_x + 0.5,
                block_y + 0.5,
                str(block),
                ha='center',
                va='center',
                fontsize=24,
            )

    return fig, ax


def _get_claw_size(
    fig: figure.Figure,
    ax: axes.Axes,
    claw_image: npt.NDArray[np.uint8],
    zoom_factor: float,
) -> tuple[float, float]:
    # Calculate claw size in data coordinates
    # Get the figure size in inches and DPI
    fig_width_inches, fig_height_inches = fig.get_size_inches()
    dpi = fig.get_dpi()

    # Get axis bounds in figure coordinates (0-1)
    ax_bbox = ax.get_position()
    ax_width_pixels = ax_bbox.width * fig_width_inches * dpi
    ax_height_pixels = ax_bbox.height * fig_height_inches * dpi

    # Get data coordinate ranges
    x_range = ax.get_xlim()[1] - ax.get_xlim()[0]  # Should be 3
    y_range = ax.get_ylim()[1] - ax.get_ylim()[0]  # Should be num_blocks + 1

    # Calculate pixels per data unit
    pixels_per_x_unit = ax_width_pixels / x_range
    pixels_per_y_unit = ax_height_pixels / y_range

    # Get claw image dimensions and apply zoom
    claw_height_pixels, claw_width_pixels = claw_image.shape[:2]
    claw_width_zoomed = claw_width_pixels * zoom_factor
    claw_height_zoomed = claw_height_pixels * zoom_factor

    # Convert to data coordinates
    claw_width_data = claw_width_zoomed / pixels_per_x_unit
    claw_height_data = claw_height_zoomed / pixels_per_y_unit

    # AnnotationBbox positions by center, so these are half-widths/heights
    return 2 * claw_width_data, 2 * claw_height_data


def _add_claw(
    ax: axes.Axes,
    claw_image: npt.NDArray[np.uint8],
    claw_x: float,
    claw_y: float,
    zoom_factor: float,
) -> None:
    im = offsetbox.OffsetImage(claw_image, zoom=zoom_factor)
    ab = offsetbox.AnnotationBbox(im, (claw_x, claw_y), frameon=False)
    ax.add_artist(ab)


def plot_state_action(
    num_blocks: int,
    prev_state: environment.State,
    state: environment.State,
    action: environment.Action,
    step: int,
    claw_image: npt.NDArray[np.uint8],
    claw_width: float,
    claw_height: float,
    y_max: float,
    zoom_factor: float,
    writer: Any,
) -> None:
    """Plot a single state and action, and export to GIF writer."""
    src, dst = environment.ACTION_MAP[action]

    # Animate the claw moving to collect and move the block
    claw_positions = [
        ((src - 1 + 0.5, y_max - claw_height / 2), True, None),
        ((src - 1 + 0.5, len(state[src - 1]) + 1), True, None),
        ((src - 1 + 0.5, y_max - claw_height / 2), True, src),
        ((dst - 1 + 0.5, y_max - claw_height / 2), False, dst),
        ((dst - 1 + 0.5, len(state[dst - 1])), False, None),
        ((dst - 1 + 0.5, y_max - claw_height / 2), False, None),
    ]

    for (claw_x, claw_y), is_prev, lifted in claw_positions:
        fig, ax = plot_state(
            num_blocks, prev_state if is_prev else state, lifted=lifted
        )

        ax.set_title(f'Step {step}: Move block from Stack {src} to Stack {dst}')

        # Add claw image
        _add_claw(ax, claw_image, claw_x, claw_y, zoom_factor)

        _export_image(fig, writer)
        plt.close(fig)


def plot_environment(
    num_blocks: int,
    states: list[environment.State],
    actions: list[environment.Action],
    output: pathlib.Path,
) -> None:
    """Plot the blockworld environment states and actions as a GIF."""
    CONSOLE.info(f'Creating GIF at {output.relative_to(path_utils.REPO_ROOT)}...')
    fps = 1.5
    frame_duration_ms = int(1000 / fps)
    writer = imageio.get_writer(output, mode='I', duration=frame_duration_ms)

    claw_image = _load_image(claw_path)
    zoom_factor = 0.5

    # Plot the initial state
    fig, ax = plot_state(num_blocks, states[0])
    ax.set_title('Initial State')

    # Grab some data for the claw
    claw_width, claw_height = _get_claw_size(
        fig, ax, claw_image, zoom_factor=zoom_factor
    )
    y_max = ax.get_ylim()[1]

    # Add the claw to the first stack
    _add_claw(ax, claw_image, 0.5, y_max - claw_height / 2, zoom_factor)

    _export_image(fig, writer)
    plt.close(fig)

    prev_state = states[0]
    for i, (state, action) in enumerate(zip(states[1:], actions)):
        plot_state_action(
            num_blocks,
            prev_state,
            state,
            action,
            i + 1,
            claw_image,
            claw_width,
            claw_height,
            y_max,
            zoom_factor,
            writer,
        )
        prev_state = state

    writer.close()
    CONSOLE.success(f'Wrote GIF to {output.relative_to(path_utils.REPO_ROOT)}')


def plot_policy_success(
    df: pd.DataFrame, policy: metrics.Policy, output: pathlib.Path
) -> None:
    policy_df = df[df['policy'] == policy.name]

    # Get the reasoning effort levels
    reasoning_efforts = policy_df['reasoning_effort'].unique()

    # Aggregate success rates by reasoning effort
    success_rates = (
        policy_df.groupby('reasoning_effort')['success']
        .mean()
        .reindex(reasoning_efforts)
    )

    # Plotting
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(reasoning_efforts, success_rates, color='skyblue')
    ax.set_xlabel('Reasoning Effort')
    ax.set_ylabel('Success Rate')
    ax.set_title(f'Success Rate by Reasoning Effort for {policy.name}')
    for i, v in enumerate(success_rates):
        ax.text(i, v + 0.02, f'{v:.2f}', ha='center', fontsize=12)

    plt.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    CONSOLE.success(f'Wrote plot to {output.relative_to(path_utils.REPO_ROOT)}')


def plot_policy_success_comparison(
    method_to_df: dict[metrics.Policy, pd.DataFrame],
    reasoning_effort: str,
    output: pathlib.Path,
) -> None:
    # Prepare data for comparison
    policies = list(method_to_df.keys())
    success_rates = []
    for policy in policies:
        df = method_to_df[policy]
        policy_df = df[df['reasoning_effort'] == reasoning_effort]
        success_rate = policy_df['success'].mean()
        success_rates.append(success_rate)

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar([p.name for p in policies], success_rates, color='lightblue')
    ax.set_xlabel('Policy')
    ax.set_ylabel('Success Rate')
    ax.set_title(
        f'Policy Success Rate Comparison at {reasoning_effort.capitalize()} Reasoning Effort'
    )
    for i, v in enumerate(success_rates):
        ax.text(i, v + 0.02, f'{v:.2f}', ha='center', fontsize=12)

    plt.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    CONSOLE.success(f'Wrote plot to {output.relative_to(path_utils.REPO_ROOT)}')


def plot_steps(df: pd.DataFrame, policy: metrics.Policy, output: pathlib.Path) -> None:
    """Box plot of steps to solution by reasoning effort."""
    policy_df = df[df['policy'] == policy.name]

    # Get the reasoning effort levels
    reasoning_efforts = policy_df['reasoning_effort'].unique()

    # Plotting
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.boxplot(
        [
            policy_df[policy_df['reasoning_effort'] == reff]['steps']
            for reff in reasoning_efforts
        ],
    )
    ax.set_xlabel('Reasoning Effort')
    ax.set_ylabel('Steps to Solution')
    ax.set_title(f'Steps to Solution by Reasoning Effort for {policy.name}')
    ax.set_xticklabels(reasoning_efforts)

    plt.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    CONSOLE.success(f'Wrote plot to {output.relative_to(path_utils.REPO_ROOT)}')


def plot_steps_comparison(
    method_to_df: dict[metrics.Policy, pd.DataFrame],
    reasoning_effort: str,
    output: pathlib.Path,
) -> None:
    policies = list(method_to_df.keys())
    steps_data = []
    for policy in policies:
        df = method_to_df[policy]
        policy_df = df[df['reasoning_effort'] == reasoning_effort]
        steps_data.append(policy_df['steps'])

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(steps_data)
    ax.set_xlabel('Policy')
    ax.set_ylabel('Steps to Solution')
    ax.set_title(
        f'Policy Steps to Solution Comparison at {reasoning_effort.capitalize()} Reasoning Effort'
    )
    ax.set_xticklabels([p.name for p in policies])

    plt.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    CONSOLE.success(f'Wrote plot to {output.relative_to(path_utils.REPO_ROOT)}')


def plot_wall_time(
    df: pd.DataFrame, policy: metrics.Policy, output: pathlib.Path, batch_size: int
) -> None:
    policy_df = df[df['policy'] == policy.name]

    # Get the reasoning effort levels
    reasoning_efforts = policy_df['reasoning_effort'].unique()

    # Aggregate wall time by reasoning effort
    wall_times = (
        policy_df.groupby('reasoning_effort')['wall_time_s']
        .mean()
        .reindex(reasoning_efforts)
    )
    if policy in {metrics.Policy.MDP_LLM, metrics.Policy.HEURISTIC_LLM}:
        # Multiple by batch size to compute "offline" time
        wall_times *= batch_size

    # Plotting
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(reasoning_efforts, wall_times, color='lightgreen')
    ax.set_xlabel('Reasoning Effort')
    ax.set_ylabel('Average Wall Time (s)')
    ax.set_title(f'Average Wall Time by Reasoning Effort for {policy.name}')
    for i, v in enumerate(wall_times):
        ax.text(i, v + 0.02, f'{v:.2f}s', ha='center', fontsize=12)

    plt.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    CONSOLE.success(f'Wrote plot to {output.relative_to(path_utils.REPO_ROOT)}')


def plot_wall_time_comparison(
    method_to_df: dict[metrics.Policy, pd.DataFrame],
    reasoning_effort: str,
    output: pathlib.Path,
) -> None:
    policies = list(method_to_df.keys())
    wall_time_data = []
    for policy in policies:
        df = method_to_df[policy]
        policy_df = df[df['reasoning_effort'] == reasoning_effort]
        wall_time_data.append(policy_df['wall_time_s'])

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(wall_time_data)
    ax.set_xlabel('Policy')
    ax.set_ylabel('Wall Time (s)')
    ax.set_title(
        f'Policy Wall Time Comparison at {reasoning_effort.capitalize()} Reasoning Effort'
    )
    ax.set_xticklabels([p.name for p in policies])

    plt.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    CONSOLE.success(f'Wrote plot to {output.relative_to(path_utils.REPO_ROOT)}')


def plot_token_usage(
    df: pd.DataFrame, policy: metrics.Policy, output: pathlib.Path, batch_size: int
) -> None:
    policy_df = df[df['policy'] == policy.name]

    # Get the reasoning effort levels
    reasoning_efforts = policy_df['reasoning_effort'].unique()

    # Aggregate token usage by reasoning effort
    input_tokens = (
        policy_df.groupby('reasoning_effort')['input_tokens']
        .mean()
        .reindex(reasoning_efforts)
    )
    output_tokens = (
        policy_df.groupby('reasoning_effort')['output_tokens']
        .mean()
        .reindex(reasoning_efforts)
    )
    if policy in {metrics.Policy.MDP_LLM, metrics.Policy.HEURISTIC_LLM}:
        # Multiple by batch size to compute "offline" tokens
        input_tokens *= batch_size
        output_tokens *= batch_size

    x = np.arange(len(reasoning_efforts))  # the label locations
    width = 0.35  # the width of the bars

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width / 2, input_tokens, width, label='Input Tokens', color='lightcoral')
    ax.bar(
        x + width / 2, output_tokens, width, label='Output Tokens', color='lightsalmon'
    )

    ax.set_xlabel('Reasoning Effort')
    ax.set_ylabel('Average Token Usage')
    ax.set_title(f'Average Token Usage by Reasoning Effort for {policy.name}')
    ax.set_xticks(x)
    ax.set_xticklabels(reasoning_efforts)
    ax.legend()

    for i, (in_tok, out_tok) in enumerate(zip(input_tokens, output_tokens)):
        ax.text(i - width / 2, in_tok + 5, f'{int(in_tok)}', ha='center', fontsize=10)
        ax.text(i + width / 2, out_tok + 5, f'{int(out_tok)}', ha='center', fontsize=10)

    plt.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    CONSOLE.success(f'Wrote plot to {output.relative_to(path_utils.REPO_ROOT)}')


def plot_token_usage_comparison(
    method_to_df: dict[metrics.Policy, pd.DataFrame],
    reasoning_effort: str,
    output: pathlib.Path,
    batch_size: int,
) -> None:
    policies = list(method_to_df.keys())
    input_token_data = []
    output_token_data = []
    for policy in policies:
        df = method_to_df[policy]
        policy_df = df[df['reasoning_effort'] == reasoning_effort]
        input_token_data.append(policy_df['input_tokens'])
        output_token_data.append(policy_df['output_tokens'])
        if policy in {metrics.Policy.MDP_LLM, metrics.Policy.HEURISTIC_LLM}:
            # Multiple by batch size to compute "offline" tokens
            input_token_data[-1] *= batch_size
            output_token_data[-1] *= batch_size

    x = np.arange(len(policies))  # the label locations
    width = 0.35  # the width of the bars

    # Plotting
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(
        x - width / 2,
        [it.mean() for it in input_token_data],
        width,
        label='Input Tokens',
        color='lightcoral',
    )
    ax.bar(
        x + width / 2,
        [ot.mean() for ot in output_token_data],
        width,
        label='Output Tokens',
        color='lightsalmon',
    )

    ax.set_xlabel('Policy')
    ax.set_ylabel('Average Token Usage')
    ax.set_title(
        f'Policy Token Usage Comparison at {reasoning_effort.capitalize()} Reasoning Effort'
    )
    ax.set_xticks(x)
    ax.set_xticklabels([p.name for p in policies])
    ax.legend()

    for i, (in_tok, out_tok) in enumerate(zip(input_token_data, output_token_data)):
        ax.text(
            i - width / 2,
            in_tok.mean() + 5,
            f'{int(in_tok.mean())}',
            ha='center',
            fontsize=10,
        )
        ax.text(
            i + width / 2,
            out_tok.mean() + 5,
            f'{int(out_tok.mean())}',
            ha='center',
            fontsize=10,
        )

    plt.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    CONSOLE.success(f'Wrote plot to {output.relative_to(path_utils.REPO_ROOT)}')


@click.command()
@click.option(
    '--cur-dir',
    type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path),
    default=pathlib.Path(__file__).parent,
    help='Current directory (for loading plots and results)',
)
def main(cur_dir: pathlib.Path) -> None:
    """Load sim results and plot them"""
    batch_size = 50
    method_to_csv = {
        metrics.Policy.HEURISTIC: cur_dir / 'results_heuristic_5_blocks_50_runs.csv',
        metrics.Policy.MDP: cur_dir / 'results_mdp_5_blocks_50_runs.csv',
        metrics.Policy.OPEN_LOOP_LLM: cur_dir
        / 'results_open_loop_llm_5_blocks_50_runs.csv',
        metrics.Policy.CLOSED_LOOP_LLM: cur_dir
        / 'results_closed_loop_llm_5_blocks_50_runs_full.csv',
        metrics.Policy.HEURISTIC_LLM: cur_dir
        / 'results_heuristic_llm_5_blocks_50_runs.csv',
        metrics.Policy.MDP_LLM: cur_dir / 'results_mdp_llm_5_blocks_50_runs.csv',
    }
    method_to_df = {method: pd.read_csv(csv) for method, csv in method_to_csv.items()}

    for method, df in method_to_df.items():
        if method is metrics.Policy.HEURISTIC:
            continue

        plot_policy_success(
            df,
            method,
            cur_dir / 'plots' / f'{method.name.lower()}_success.png',
        )

        plot_steps(
            df,
            method,
            cur_dir / 'plots' / f'{method.name.lower()}_steps.png',
        )

        plot_wall_time(
            df,
            method,
            cur_dir / 'plots' / f'{method.name.lower()}_wall_time.png',
            batch_size,
        )

        plot_token_usage(
            df,
            method,
            cur_dir / 'plots' / f'{method.name.lower()}_token_usage.png',
            batch_size,
        )

    if len(method_to_df) < 2:
        return
    compare_reasoning_effort = 'high'
    plot_policy_success_comparison(
        method_to_df,
        reasoning_effort=compare_reasoning_effort,
        output=cur_dir / 'plots' / 'policy_success_comparison.png',
    )

    plot_steps_comparison(
        method_to_df,
        reasoning_effort=compare_reasoning_effort,
        output=cur_dir / 'plots' / 'steps_comparison.png',
    )

    plot_wall_time_comparison(
        method_to_df,
        reasoning_effort=compare_reasoning_effort,
        output=cur_dir / 'plots' / 'wall_time_comparison.png',
    )

    plot_token_usage_comparison(
        method_to_df,
        reasoning_effort=compare_reasoning_effort,
        output=cur_dir / 'plots' / 'token_usage_comparison.png',
        batch_size=batch_size,
    )


if __name__ == '__main__':
    main()

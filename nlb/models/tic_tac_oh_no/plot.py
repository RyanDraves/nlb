import io
import pathlib
from typing import Any

import imageio
import numpy as np
from matplotlib import figure
from matplotlib import patches
from matplotlib import pyplot as plt

from nlb.models.tic_tac_oh_no import environment
from nlb.util import console_utils
from nlb.util import path_utils

CONSOLE = console_utils.Console()


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


def plot_state(state: environment.State, title: str, writer: Any) -> None:
    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)

    ax.set_ylim(0, 3)
    ax.set_xlim(0, 3)

    # Draw grid lines
    for x in range(1, 3):
        ax.axhline(x, color='black', linewidth=1)
        ax.axvline(x, color='black', linewidth=1)
    ax.set_xticks([])
    ax.set_yticks([])
    # Remove the border
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # Draw X and O on the grid
    for i in range(3):
        for j in range(3):
            cell = state.grid[i, j]
            if cell == 1:
                ax.text(
                    j + 0.5,
                    2.5 - i,
                    'X',
                    fontsize=60,
                    ha='center',
                    va='center',
                    color='blue',
                )
            elif cell == -1:
                ax.text(
                    j + 0.5,
                    2.5 - i,
                    'O',
                    fontsize=60,
                    ha='center',
                    va='center',
                    color='red',
                )

    # Draw anomaly as a 1x1 green square with transparency
    if state.anom_pos is not None:
        anom_row, anom_col = state.anom_pos
        anom_square = patches.Rectangle(
            (anom_col - 0.5, anom_row - 0.5),
            1,
            1,
            linewidth=1,
            edgecolor='green',
            facecolor='green',
            alpha=0.8,
        )
        ax.add_patch(anom_square)

    ax.set_title(title)

    _export_image(fig, writer)
    plt.close(fig)


def plot_environment(
    states: list[environment.State],
    actions: list[environment.Action],
    output: pathlib.Path,
) -> None:
    """Plot the blockworld environment states and actions as a GIF."""
    CONSOLE.info(f'Creating GIF at {output.relative_to(path_utils.REPO_ROOT)}...')
    fps = 1
    frame_duration_ms = int(1000 / fps)
    writer = imageio.get_writer(output, mode='I', duration=frame_duration_ms)

    # Plot the initial state
    plot_state(states[0], title='Initial State', writer=writer)

    for i, (state, action) in enumerate(zip(states[1:], actions)):
        plot_state(
            state,
            title=f'Step {i + 1}: Action = {action.name}',
            writer=writer,
        )

    writer.close()
    CONSOLE.success(f'Wrote GIF to {output.relative_to(path_utils.REPO_ROOT)}')

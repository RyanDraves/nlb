import io
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
from daltonize import daltonize
from matplotlib import figure
from PIL import Image

# Colorblindness simulation types
ColorblindType = Literal['protan', 'deutan', 'tritan']


def simulate_colorblindness(
    fig: figure.Figure,
    colorblind_type: ColorblindType,
    dpi: int = 100,
) -> figure.Figure:
    """Simulate how a figure would appear with different types of colorblindness.

    Requires the 'daltonize' package to be installed.

    Args:
        fig: The matplotlib Figure to simulate colorblindness on.
        colorblind_type: Type of colorblindness to simulate:
            - 'protan': Protanopia (red-blind)
            - 'deutan': Deuteranopia (green-blind)
            - 'tritan': Tritanopia (blue-blind)
        dpi: Resolution to use for rendering the figure.

    Returns:
        A new Figure showing how the original would appear with the specified
        colorblindness type.

    Raises:
        ImportError: If daltonize package is not installed.

    Examples:
        >>> fig, ax = plt.subplots()
        >>> ax.plot(x, y, color='red')
        >>> protan_fig = simulate_colorblindness(fig, 'protan')
        >>> protan_fig.savefig('protan_view.png')
    """
    # Map our names to daltonize's format
    deficit_map = {'protan': 'p', 'deutan': 'd', 'tritan': 't'}
    deficit_code = deficit_map[colorblind_type]

    # Render the figure to an image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf)
    img_array = np.array(img, dtype=np.float32) / 255.0  # Normalize to [0, 1]

    # Handle alpha channel if present
    if img_array.shape[2] == 4:
        rgb = img_array[:, :, :3]
        alpha = img_array[:, :, 3:]
        simulated_rgb = daltonize.simulate(rgb, deficit_code)
        simulated_array = np.concatenate([simulated_rgb, alpha], axis=2)
    else:
        simulated_array = daltonize.simulate(img_array, deficit_code)

    # Convert back to [0, 255] range
    simulated_array = np.clip(simulated_array * 255, 0, 255).astype(np.uint8)

    # Create a new figure with the simulated image
    new_fig, new_ax = plt.subplots(figsize=fig.get_size_inches())
    new_ax.imshow(simulated_array)
    new_ax.axis('off')
    new_fig.suptitle(
        'How the plot appears with Protanopia (Red-Blind)',
        fontsize=12,
        fontweight='bold',
    )
    new_fig.tight_layout(pad=0)

    buf.close()

    return new_fig


def show_colorblind_comparison(
    fig: figure.Figure,
    types: list[ColorblindType] | None = None,
    dpi: int = 100,
) -> figure.Figure:
    """Show original figure alongside colorblindness simulations.

    Args:
        fig: The matplotlib Figure to compare.
        types: List of colorblindness types to simulate. If None, shows all three types.
        dpi: Resolution to use for rendering the figure.

    Returns:
        A new Figure with the original and all simulated versions side by side.

    Raises:
        ImportError: If daltonize package is not installed.

    Examples:
        >>> fig, ax = plt.subplots()
        >>> ax.plot(x, y, color='red', label='Data')
        >>> ax.legend()
        >>> comparison = show_colorblind_comparison(fig)
        >>> comparison.savefig('colorblind_comparison.png')
    """
    if types is None:
        types = ['protan', 'deutan', 'tritan']

    # Map our names to daltonize's format
    deficit_map = {'protan': 'p', 'deutan': 'd', 'tritan': 't'}

    # Render original figure
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    original_img = Image.open(buf)
    original_array = np.array(original_img)

    # Create comparison figure
    n_cols = len(types) + 1
    comparison_fig, axes = plt.subplots(
        1, n_cols, figsize=(6 * n_cols, 6), constrained_layout=True
    )

    if n_cols == 1:
        axes = [axes]

    # Show original
    axes[0].imshow(original_array)
    axes[0].set_title('Original (Normal Vision)', fontsize=14, fontweight='bold')
    axes[0].axis('off')

    # Show simulations
    type_names = {
        'protan': 'Protanopia\n(Red-Blind)',
        'deutan': 'Deuteranopia\n(Green-Blind)',
        'tritan': 'Tritanopia\n(Blue-Blind)',
    }

    for i, colorblind_type in enumerate(types, start=1):
        deficit_code = deficit_map[colorblind_type]
        # Normalize to [0, 1] for daltonize
        img_normalized = original_array.astype(np.float32) / 255.0

        # Handle alpha channel if present
        if img_normalized.shape[2] == 4:
            rgb = img_normalized[:, :, :3]
            alpha = img_normalized[:, :, 3:]
            simulated_rgb = daltonize.simulate(rgb, deficit_code)
            simulated_normalized = np.concatenate([simulated_rgb, alpha], axis=2)
        else:
            simulated_normalized = daltonize.simulate(img_normalized, deficit_code)

        # Convert back to [0, 255] range
        simulated_array = np.clip(simulated_normalized * 255, 0, 255).astype(np.uint8)

        axes[i].imshow(simulated_array)
        axes[i].set_title(type_names[colorblind_type], fontsize=14, fontweight='bold')
        axes[i].axis('off')

    comparison_fig.suptitle(
        'Colorblindness Simulation Comparison', fontsize=16, fontweight='bold', y=0.98
    )
    comparison_fig.tight_layout()

    buf.close()

    return comparison_fig

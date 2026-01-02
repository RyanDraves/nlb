"""Example usage of Paul Tol's Bright colorblind-friendly color scheme."""

import matplotlib.pyplot as plt
import numpy as np

from nlb.plotting import daltonize
from nlb.plotting import palette


def example_line_plots():
    """Example: Multiple line plots with Tol Bright color cycle."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Set the color cycle
    palette.set_tol_bright_cycle(ax)

    x = np.linspace(0, 10, 100)
    for i in range(7):
        y = np.sin(x + i * np.pi / 4) + i
        ax.plot(x, y, label=f'Line {i + 1}', linewidth=2)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Line Plots with Paul Tol Bright Colors')
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig


def example_scatter():
    """Example: Scatter plot with discrete categories."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Generate sample data with 5 categories
    np.random.seed(42)
    n_points = 50
    categories = np.random.randint(0, 5, n_points)
    x = np.random.randn(n_points)
    y = np.random.randn(n_points)

    # Use discrete colormap
    cmap = palette.tol_bright_cmap(n=5, discrete=True)
    scatter = ax.scatter(
        x, y, c=categories, cmap=cmap, s=100, edgecolors='black', linewidth=0.5
    )

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Scatter Plot with Discrete Categories')
    plt.colorbar(scatter, ax=ax, label='Category')

    return fig


def example_heatmap():
    """Example: Heatmap with continuous colormap."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Generate sample data
    np.random.seed(42)
    data = np.random.randn(20, 20)

    # Smooth colormap
    cmap_smooth = palette.tol_bright_cmap(discrete=False)
    im1 = ax1.imshow(data, cmap=cmap_smooth, aspect='auto')
    ax1.set_title('Smooth Tol Bright Colormap')
    plt.colorbar(im1, ax=ax1)

    # Discrete colormap
    cmap_discrete = palette.tol_bright_cmap(discrete=True)
    im2 = ax2.imshow(data, cmap=cmap_discrete, aspect='auto')
    ax2.set_title('Discrete Tol Bright Colormap')
    plt.colorbar(im2, ax=ax2)

    fig.suptitle(
        'Heatmaps with Paul Tol Bright Colormap', fontsize=14, fontweight='bold'
    )

    return fig


def example_bar_chart():
    """Example: Bar chart with specific colors."""
    fig, ax = plt.subplots(figsize=(10, 6))

    categories = ['Category A', 'Category B', 'Category C', 'Category D']
    values = [23, 45, 56, 34]

    # Get specific colors
    colors = palette.tol_bright_colors(n=4)

    ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1)

    ax.set_ylabel('Values')
    ax.set_title('Bar Chart with Paul Tol Bright Colors')
    ax.grid(True, axis='y', alpha=0.3)

    return fig


def example_direct_colors():
    """Example: Using direct color constants."""
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.linspace(0, 10, 100)

    # Use specific named colors
    ax.plot(x, np.sin(x), color=palette.TOL_BLUE, label='Sine (Blue)', linewidth=2)
    ax.plot(
        x, np.cos(x), color=palette.TOL_SALMON, label='Cosine (Salmon)', linewidth=2
    )
    ax.plot(
        x,
        np.sin(x) + np.cos(x),
        color=palette.TOL_GREEN,
        label='Sum (Green)',
        linewidth=2,
    )

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Using Direct Color Constants')
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig


def example_continuous_heatmap():
    """Example: Heatmap with continuous data on a smooth color spectrum."""
    fig, ax = plt.subplots(figsize=(10, 8))

    # Generate continuous data (e.g., a 2D function)
    x = np.linspace(-3, 3, 200)
    y = np.linspace(-3, 3, 200)
    X, Y = np.meshgrid(x, y)

    # Create interesting continuous data (2D Gaussian with some variation)
    Z = np.exp(-(X**2 + Y**2) / 2) * np.cos(X) * np.sin(Y)

    # Use smooth continuous colormap
    cmap = palette.tol_bright_cmap()
    im = ax.imshow(
        Z,
        extent=(-3, 3, -3, 3),
        origin='lower',
        cmap=cmap,
        aspect='auto',
        interpolation='bilinear',
    )

    ax.set_xlabel('X', fontsize=12)
    ax.set_ylabel('Y', fontsize=12)
    ax.set_title(
        'Continuous Spectrum Heatmap\n(Colorblind-Friendly)',
        fontsize=14,
        fontweight='bold',
    )

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Value', fontsize=12)

    # Add contour lines for clarity
    contours = ax.contour(X, Y, Z, colors='black', alpha=0.3, linewidths=0.5, levels=10)
    ax.clabel(contours, inline=True, fontsize=8)

    return fig


def main():
    """Run all examples."""
    print('Generating examples of Paul Tol Bright color scheme...')

    # Register the colormap globally
    palette.register_tol_bright_cmap()
    print('Registered tol_bright colormap')

    # Create examples
    line_fig = example_line_plots()
    print('Created line plot example')

    example_scatter()
    print('Created scatter plot example')

    example_heatmap()
    print('Created heatmap example')

    bar_fig = example_bar_chart()
    print('Created bar chart example')

    example_direct_colors()
    print('Created direct colors example')

    continuous_fig = example_continuous_heatmap()
    print('Created continuous heatmap example')

    # Create colorblindness comparison examples for select plots
    print('\nGenerating colorblindness simulations...')

    # Show how the line plot looks to people with different types of colorblindness
    daltonize.show_colorblind_comparison(line_fig)
    print('Created line plot colorblindness comparison')

    # Show how the continuous heatmap looks
    daltonize.show_colorblind_comparison(continuous_fig)
    print('Created heatmap colorblindness comparison')

    # Show how the bar chart looks
    daltonize.show_colorblind_comparison(bar_fig)
    print('Created bar chart colorblindness comparison')

    plt.show()
    print('\nAll examples generated!')


if __name__ == '__main__':
    main()

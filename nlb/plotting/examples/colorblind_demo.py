"""Demonstration of colorblindness simulation utilities.

This example shows how to use the colorblindness simulation functions
to verify that plots are accessible to people with different types of colorblindness.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import figure

from nlb.plotting import daltonize
from nlb.plotting import palette


def create_sample_plot() -> figure.Figure:
    """Create a sample plot to demonstrate colorblindness simulation."""
    fig, ax = plt.subplots(figsize=(8, 5))

    # Set the Tol Bright color cycle
    palette.set_tol_bright_cycle(ax)

    # Generate some sample data
    x = np.linspace(0, 10, 100)

    # Plot multiple lines with different colors
    ax.plot(x, np.sin(x), linewidth=3, label='Sine')
    ax.plot(x, np.cos(x), linewidth=3, label='Cosine')
    ax.plot(x, np.sin(x) * np.cos(x), linewidth=3, label='Product')
    ax.plot(x, np.sin(x + np.pi / 4), linewidth=3, label='Phase shifted')

    ax.set_xlabel('X', fontsize=12)
    ax.set_ylabel('Y', fontsize=12)
    ax.set_title(
        'Multiple Line Plot with Tol Bright Colors', fontsize=14, fontweight='bold'
    )
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)

    return fig


def demo_single_simulation() -> None:
    """Demonstrate simulating a single type of colorblindness."""
    print('Creating sample plot...')
    fig = create_sample_plot()

    print('Simulating protanopia (red-blind) vision...')
    daltonize.simulate_colorblindness(fig, 'protan')


def demo_full_comparison() -> None:
    """Demonstrate comparing all colorblindness types side by side."""
    print('Creating sample plot...')
    fig = create_sample_plot()

    print('Creating comparison with all colorblindness types...')
    daltonize.show_colorblind_comparison(fig)


def main():
    """Run colorblindness simulation demonstrations."""
    print('=' * 60)
    print('Colorblindness Simulation Demo')
    print('=' * 60)
    print()

    # Example 1: Single simulation
    print('Example 1: Single colorblindness type simulation')
    print('-' * 60)
    demo_single_simulation()
    print('✓ Created protanopia simulation')
    print()

    # Example 2: Full comparison
    print('Example 2: Full comparison with all types')
    print('-' * 60)
    demo_full_comparison()
    print('✓ Created full comparison showing all three types')
    print()

    print('=' * 60)
    print('All examples generated!')
    print('Close the plot windows to exit.')
    print('=' * 60)

    plt.show()


if __name__ == '__main__':
    main()

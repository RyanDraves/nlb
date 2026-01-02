"""Colorblind-friendly plotting palette utilities.

This module provides utilities for using Paul Tol's Bright color scheme,
which is designed to be colorblind-friendly and distinguishable in both
color and grayscale reproduction.

Reference: https://sronpersonalpages.nl/~pault/
"""

import cycler
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import axes
from matplotlib import colors

# Paul Tol's Bright color scheme (RGB values 0-255)
_TOL_BRIGHT_RGB = [
    (0x44, 0x77, 0xAA),  # blue
    (0x66, 0xCC, 0xEE),  # cyan
    (0x22, 0x88, 0x33),  # green
    (0xCC, 0xBB, 0x44),  # yellow
    (0xEE, 0x66, 0x77),  # salmon
    (0xAA, 0x33, 0x77),  # purple
    (0xBB, 0xBB, 0xBB),  # grey
]

# Normalize to 0-1 range for matplotlib
_TOL_BRIGHT_NORMALIZED = [(r / 255, g / 255, b / 255) for r, g, b in _TOL_BRIGHT_RGB]

# Convenience constants for direct color access
TOL_BLUE = _TOL_BRIGHT_NORMALIZED[0]
TOL_CYAN = _TOL_BRIGHT_NORMALIZED[1]
TOL_GREEN = _TOL_BRIGHT_NORMALIZED[2]
TOL_YELLOW = _TOL_BRIGHT_NORMALIZED[3]
TOL_SALMON = _TOL_BRIGHT_NORMALIZED[4]
TOL_PURPLE = _TOL_BRIGHT_NORMALIZED[5]
TOL_GREY = _TOL_BRIGHT_NORMALIZED[6]


def tol_bright_colors(
    *, n: int | None = None, alpha: float = 1.0
) -> list[tuple[float, ...]]:
    """Get Paul Tol's Bright color scheme colors.

    Args:
        n: Number of colors to return. If None, returns all 7 colors.
           If n > 7, colors will cycle.
        alpha: Alpha (transparency) value, 0-1.

    Returns:
        List of RGBA tuples with values in [0, 1].

    Examples:
        >>> colors = tol_bright_colors(3)  # Get first 3 colors
        >>> colors = tol_bright_colors(alpha=0.5)  # All colors with 50% transparency
    """
    _colors = _TOL_BRIGHT_NORMALIZED.copy()

    if n is not None:
        if n <= len(_colors):
            _colors = _colors[:n]
        else:
            # Cycle colors if more requested than available
            _colors = [_colors[i % len(_colors)] for i in range(n)]

    # Add alpha channel
    return [(*color, alpha) for color in _colors]


def tol_bright_cmap(
    *, n: int | None = None, discrete: bool = False, sans_grey: bool = True
) -> colors.ListedColormap:
    """Create a colormap using Paul Tol's Bright color scheme.

    Args:
        n: Number of colors from the scheme in the colormap.
        discrete: If True, returns a discrete colormap with distinct colors.
            If False, returns a continuous colormap interpolated between the
            Bright colors.
        sans_grey: If True, excludes the grey color from the colormap.

    Returns:
        A ListedColormap that can be used with matplotlib plotting functions.

    Examples:
        >>> cmap = tol_bright_cmap()  # Smooth colormap
        >>> plt.imshow(data, cmap=cmap)
        >>>
        >>> cmap_discrete = tol_bright_cmap(n=7)  # Discrete colormap
        >>> plt.scatter(x, y, c=categories, cmap=cmap_discrete)
    """
    num_colors = len(_TOL_BRIGHT_NORMALIZED) - (1 * sans_grey)

    n = n or num_colors
    if n > num_colors:
        raise ValueError(
            f'Cannot create colormap with {n} colors; maximum is {num_colors}.'
        )

    if discrete:
        # For small n, just use the actual colors
        _colors = tol_bright_colors(n=n)
    else:
        # For larger n, interpolate between colors
        base_colors = tol_bright_colors(n=n)
        # Create interpolation points
        x = np.linspace(0, 1, len(base_colors))
        xnew = np.linspace(0, 1, 256)

        # Interpolate each RGB channel
        r = np.interp(xnew, x, [c[0] for c in base_colors])
        g = np.interp(xnew, x, [c[1] for c in base_colors])
        b = np.interp(xnew, x, [c[2] for c in base_colors])

        _colors = list(zip(r, g, b, [1.0] * 256))

    return colors.ListedColormap(_colors, name='tol_bright')


def register_tol_bright_cmap() -> None:
    """Register Paul Tol's Bright colormap with matplotlib.

    After calling this function, the colormap can be accessed by name:
        plt.plot(x, y, cmap='tol_bright')
    """
    cmap = tol_bright_cmap()
    mpl.colormaps.register(cmap=cmap)


def set_tol_bright_cycle(ax: axes.Axes | None = None) -> None:
    """Set the color cycle to Paul Tol's Bright colors for an axes or globally.

    This affects line plots, scatter plots, and other plots that cycle through colors.

    Args:
        ax: Matplotlib axes to apply colors to. If None, applies globally
            to the current rcParams.

    Examples:
        >>> fig, ax = plt.subplots()
        >>> set_tol_bright_cycle(ax)
        >>> for i in range(7):
        ...     ax.plot(x, y + i, label=f'Line {i}')
        >>>
        >>> set_tol_bright_cycle()  # Apply globally
        >>> plt.plot(x, y)
    """
    _colors = tol_bright_colors()

    if ax is not None:
        ax.set_prop_cycle(color=_colors)
    else:
        plt.rcParams['axes.prop_cycle'] = cycler.cycler(color=_colors)

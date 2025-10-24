"""
Core Utility: interpolation
---------------------------
Common interpolation logic shared across all tools.
"""

from typing import Tuple

import numpy as np
import pandas as pd


def interpolate_to_common_grid(
    prof1: pd.DataFrame, prof2: pd.DataFrame, dx: float = 10.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Interpolates two profiles to a common uniform X-grid.

    Parameters
    ----------
    prof1, prof2 : pd.DataFrame
        Each with columns ['X', 'Z'].
    dx : float
        Spacing for the common grid, default = 10 ft.

    Returns
    -------
    x_common : np.ndarray
        Uniform X-grid spanning the overlap of both profiles.
    z1_interp : np.ndarray
        Interpolated Z values for Profile 1.
    z2_interp : np.ndarray
        Interpolated Z values for Profile 2.
    """
    xmin = max(prof1["X"].min(), prof2["X"].min())
    xmax = min(prof1["X"].max(), prof2["X"].max())

    if xmin >= xmax:
        raise ValueError("Profiles do not overlap in X-range.")

    x_common = np.arange(xmin, xmax + dx, dx)
    z1_interp = np.interp(x_common, prof1["X"], prof1["Z"])
    z2_interp = np.interp(x_common, prof2["X"], prof2["Z"])

    return x_common, z1_interp, z2_interp

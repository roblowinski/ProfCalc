"""
Module: interpolate
Location: profcalc.modules.profiles
--------------------------------------------
Replicates BMAP's "Interpolate" tool.

Resamples a single beach profile at uniform X-spacing (Δx)
using linear interpolation.
"""

import numpy as np
import pandas as pd


def compute_interpolate(profile: pd.DataFrame, dx: float = 5.0) -> pd.DataFrame:
    """
    Interpolate a single profile to a uniform Δx spacing.

    Parameters
    ----------
    profile : pd.DataFrame
        Input profile with columns ['X', 'Z'].
    dx : float, optional
        Desired horizontal spacing in same units as X (default 5.0).

    Returns
    -------
    pd.DataFrame
        Resampled profile with evenly spaced X values and interpolated Z values.
    """
    if not {"X", "Z"}.issubset(profile.columns):
        raise ValueError("Input DataFrame must contain columns ['X', 'Z'].")

    profile = profile.sort_values("X").dropna(subset=["X", "Z"])

    x_min, x_max = profile["X"].min(), profile["X"].max()
    new_x = np.arange(x_min, x_max + dx, dx)
    new_z = np.interp(new_x, profile["X"], profile["Z"])

    resampled = pd.DataFrame({"X": new_x, "Z": new_z})
    resampled.attrs["dx"] = dx
    return resampled


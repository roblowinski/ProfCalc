# =============================================================================
# BMAP Profile Interpolation Tool
# =============================================================================
#
# FILE: src/profcalc/tools/bmap/bmap_interpolate.py
#
# PURPOSE:
# This module replicates BMAP's "Interpolate" tool functionality, providing
# uniform resampling of beach profile data. It takes profiles with irregular
# or non-uniform spacing and creates evenly-spaced data points using linear
# interpolation, which is essential for many analytical operations.
#
# WHAT IT'S FOR:
# - Resampling profiles to uniform cross-shore spacing
# - Preparing profile data for comparative analysis
# - Ensuring consistent data density for numerical operations
# - Supporting interpolation-based analysis techniques
# - Creating regular grids for profile visualization and processing
#
# WORKFLOW POSITION:
# This tool is used early in profile analysis workflows to standardize data
# spacing. It's particularly important when profiles from different surveys
# have varying point densities or when analysis methods require uniform
# spacing for accurate results.
#
# LIMITATIONS:
# - Uses simple linear interpolation between existing points
# - Cannot extrapolate beyond the original profile extent
# - May smooth over important morphological features
# - Assumes monotonic X-coordinate ordering
#
# ASSUMPTIONS:
# - Profile data is sorted by cross-shore distance
# - Linear interpolation is appropriate for the data characteristics
# - Desired spacing is suitable for the intended analysis
# - Profile covers the full range needed for analysis
#
# =============================================================================

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

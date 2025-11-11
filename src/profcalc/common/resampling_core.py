# =============================================================================
# Profile Resampling and Interpolation Core Utilities
# =============================================================================
#
# FILE: src/profcalc/common/resampling_core.py
#
# PURPOSE:
# This module provides core interpolation and resampling functionality for
# beach profile analysis. It handles the critical task of resampling profile
# data to common grids, enabling accurate comparisons between surveys taken
# at different spatial resolutions or with different point densities.
#
# WHAT IT'S FOR:
# - Interpolating profile data to uniform spatial grids
# - Creating common X-coordinate grids for profile comparison
# - Handling overlapping profile ranges automatically
# - Linear interpolation of elevation data between survey points
# - Supporting configurable grid spacing for different analysis needs
#
# WORKFLOW POSITION:
# This module is fundamental to comparative analysis workflows where profiles
# from different surveys need to be compared. It's used whenever profile
# data must be resampled to enable volumetric calculations, change detection,
# or statistical comparisons between surveys.
#
# LIMITATIONS:
# - Uses simple linear interpolation (no advanced interpolation methods)
# - Requires profile overlap in X-range for resampling
# - Assumes profiles have 'X' and 'Z' columns with appropriate units
# - Grid spacing is uniform (not adaptive to data density)
# - No handling of data gaps or outliers during interpolation
#
# ASSUMPTIONS:
# - Profile data is sorted by X-coordinate
# - Elevation data is continuous and suitable for linear interpolation
# - Overlapping regions represent the same physical locations
# - Grid spacing is appropriate for the analysis resolution needed
# - Coordinate systems are consistent between profiles
#
# =============================================================================

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

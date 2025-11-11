# =============================================================================
# BMAP Profile Averaging Tool
# =============================================================================
#
# FILE: src/profcalc/tools/bmap/bmap_average.py
#
# PURPOSE:
# This module replicates BMAP's "Average" tool functionality, computing
# statistical profiles from multiple beach profile surveys. It generates
# average profiles along with envelope profiles (min/max) and variability
# measures (standard deviation) to characterize profile morphology.
#
# WHAT IT'S FOR:
# - Computing average beach profiles from multiple surveys
# - Generating minimum and maximum envelope profiles
# - Calculating standard deviation profiles to show variability
# - Supporting statistical analysis of beach profile datasets
# - Providing envelope boundaries for profile comparison
#
# WORKFLOW POSITION:
# This tool is used in multi-profile analysis workflows to characterize
# typical beach morphology and variability across multiple surveys. It's
# particularly useful for understanding seasonal or inter-annual changes
# in beach profiles.
#
# LIMITATIONS:
# - Currently limited to two-profile averaging
# - Requires profiles to have overlapping cross-shore ranges
# - Interpolation assumes linear relationships between points
# - Statistical measures may not be meaningful for small sample sizes
#
# ASSUMPTIONS:
# - Input profiles represent the same physical cross-section
# - Profile data is in consistent coordinate systems
# - Interpolation spacing is appropriate for the data resolution
# - Users understand statistical interpretation of envelope profiles
#
# =============================================================================

"""
Module: average_profiles
------------------------
Replicates BMAP's "Average" tool behavior.

Generates:
  • Average profile
  • Minimum envelope profile
  • Maximum envelope profile
  • Standard deviation profile

This tool belongs to the 'profcalc.modules' package
and uses shared interpolation logic from profcalc.core.resampling_core.

Author: Rob & GPT-5
Date: October 2025
"""

from typing import Dict

import numpy as np
import pandas as pd

from profcalc.common.resampling_core import interpolate_to_common_grid


def compute_average_profiles(
    prof1: pd.DataFrame, prof2: pd.DataFrame, dx: float = 10.0
) -> Dict[str, pd.DataFrame]:
    """
    Compute BMAP-style average, min, max, and std. deviation profiles.

    Parameters
    ----------
    prof1, prof2 : pd.DataFrame
        Two input profiles, each with columns ['X', 'Z'].
    dx : float, optional
        Global X spacing for interpolation (default = 10 ft).

    Returns
    -------
    profiles : dict of pd.DataFrame
        {
            "average": DataFrame(X, Z),
            "min_envelope": DataFrame(X, Z),
            "max_envelope": DataFrame(X, Z),
            "std_dev": DataFrame(X, Z)
        }
    """
    x_common, z1, z2 = interpolate_to_common_grid(prof1, prof2, dx)

    z_avg = 0.5 * (z1 + z2)
    z_min = np.minimum(z1, z2)
    z_max = np.maximum(z1, z2)
    z_std = np.sqrt(((z1 - z_avg) ** 2 + (z2 - z_avg) ** 2) / 2.0)

    return {
        "average": pd.DataFrame({"X": x_common, "Z": z_avg}),
        "min_envelope": pd.DataFrame({"X": x_common, "Z": z_min}),
        "max_envelope": pd.DataFrame({"X": x_common, "Z": z_max}),
        "std_dev": pd.DataFrame({"X": x_common, "Z": z_std}),
    }

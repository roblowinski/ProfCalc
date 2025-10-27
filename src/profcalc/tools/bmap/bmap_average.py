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


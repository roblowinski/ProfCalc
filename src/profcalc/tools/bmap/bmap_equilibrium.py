# =============================================================================
# BMAP Equilibrium Profile Generation Tool
# =============================================================================
#
# FILE: src/profcalc/tools/bmap/bmap_equilibrium.py
#
# PURPOSE:
# This module generates theoretical equilibrium beach profiles based on Dean's
# (1977) equilibrium profile theory. It computes the expected beach morphology
# under stable wave conditions, providing a baseline for comparing observed
# profiles and assessing beach state relative to theoretical equilibrium.
#
# WHAT IT'S FOR:
# - Generating theoretical equilibrium profiles using Dean's equation
# - Computing Dean's A parameter from median grain size
# - Creating baseline profiles for morphological analysis
# - Supporting beach state assessment and profile comparisons
# - Providing theoretical profiles for design and planning purposes
#
# WORKFLOW POSITION:
# This tool is used in profile analysis workflows to establish theoretical
# baselines for beach morphology. It's particularly useful for assessing
# whether observed profiles represent equilibrium conditions or are in a
# state of adjustment due to storms or sediment supply changes.
#
# LIMITATIONS:
# - Based on simplified equilibrium theory (Dean, 1977)
# - Assumes uniform sediment characteristics and wave conditions
# - Does not account for complex beach morphodynamic processes
# - Theoretical profiles may not match real-world conditions exactly
#
# ASSUMPTIONS:
# - Beach is in equilibrium with prevailing wave conditions
# - Sediment is well-sorted with known median grain size
# - Profile shape follows power-law relationship
# - Coordinate system and units are consistent with analysis needs
#
# =============================================================================

"""
Module: equilibrium
Location: profcalc.modules.profiles
--------------------------------------------
Generates a theoretical Dean (1977) equilibrium beach profile.

Computes profile elevation/depth as:

    h = A * x^(2/3)

User specifies:
- Horizontal range (Xon, Xoff) and spacing (dX)
- Either the Dean A parameter (ft^(1/3)) or a median grain size (mm)

Example:
    profile_df = compute_equilibrium(xon=0, xoff=300, dx=2, grain_size=0.25)
"""

from typing import Optional

import numpy as np
import pandas as pd


def compute_A_from_grain_size(d50_mm: float) -> float:
    """
    Compute Dean's A parameter (ft^(1/3)) from median grain size (mm).

    Equation (Dean, 1977):
        A = 0.21 * D50^0.48  (A in m^(1/3))
    Converted to feet using (3.28084)^(1/3).
    """
    d50_m = d50_mm / 1000.0
    A_m = 0.21 * (d50_m**0.48)
    return A_m * (3.28084 ** (1.0 / 3.0))


def compute_equilibrium(
    xon: float,
    xoff: float,
    dx: float,
    A: Optional[float] = None,
    grain_size: Optional[float] = None,
) -> pd.DataFrame:
    """
    Compute Dean equilibrium beach profile (units in feet).

    Parameters
    ----------
    xon : float
        Starting coordinate (ft).
    xoff : float
        Ending coordinate (ft).
    dx : float
        Horizontal spacing between profile points (ft).
    A : float, optional
        Dean profile parameter (ft^(1/3)).
    grain_size : float, optional
        Median grain size (mm). Used if A is not given.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['X', 'Z'] representing the equilibrium
        beach profile. Positive Z downward (depth, ft).

    Notes
    -----
    Uses the empirical Dean relation:
        h = A * x^(2/3)
    If A is not provided, it is derived from the median grain size.
    """
    if A is None and grain_size is None:
        raise ValueError("Either A or grain_size must be provided.")

    if A is None:
        assert grain_size is not None  # This should be guaranteed by the check above
        A = compute_A_from_grain_size(grain_size)

    x = np.arange(xon, xoff + dx, dx)
    z = A * np.power(x, 2.0 / 3.0)

    profile_df = pd.DataFrame({"X": x, "Z": z})
    profile_df.attrs["method"] = "Dean Equilibrium"
    profile_df.attrs["parameters"] = {
        "A_ft13": A,
        "grain_size_mm": grain_size,
        "xon_ft": xon,
        "xoff_ft": xoff,
        "dx_ft": dx,
    }

    return profile_df

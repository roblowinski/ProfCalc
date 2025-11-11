# =============================================================================
# BMAP Modified Equilibrium Profile Generation Tool
# =============================================================================
#
# FILE: src/profcalc/tools/bmap/bmap_mod_equilibrium.py
#
# PURPOSE:
# This module generates modified equilibrium beach profiles using an enhanced
# version of Dean's equilibrium theory that includes decay coefficients and
# depth ratios. It provides more flexible theoretical profile generation for
# complex beach morphologies that may not follow simple power-law relationships.
#
# WHAT IT'S FOR:
# - Generating theoretical profiles with exponential decay terms
# - Modeling complex beach morphologies with depth ratios
# - Computing Dean A-parameter from grain size for modified profiles
# - Supporting advanced equilibrium profile analysis
# - Providing theoretical baselines for complex beach systems
#
# WORKFLOW POSITION:
# This tool extends the basic equilibrium profile generation for cases where
# simple Dean profiles are insufficient. It's used when beach profiles show
# complex morphologies that require additional parameters to model accurately.
#
# LIMITATIONS:
# - More complex parameterization increases uncertainty
# - Requires knowledge of appropriate decay coefficients and depth ratios
# - Theoretical basis may be less well-established than simple Dean profiles
# - Parameter selection requires expertise in coastal morphodynamics
#
# ASSUMPTIONS:
# - Modified equilibrium equation is appropriate for the beach system
# - Decay coefficients and depth ratios are physically meaningful
# - Sediment characteristics follow Dean's relationships
# - Complex profile shapes require the additional parameters
#
# =============================================================================

"""
Module: modified_equilibrium
Location: profcalc.modules.profiles
--------------------------------------------
Generates a modified equilibrium beach profile using the provided equation.

Computes profile elevation/depth as:

    h(x) = A * [ x + (1/λ) * (D_ratio - 1) * (1 - exp(-λx)) ]^(2/3)

User specifies:
- Horizontal range (Xon, Xoff) and spacing (dX)
- Either the Dean A parameter (ft^(1/3)) or a median grain size (mm)
- dRatio and decay coefficient (λ)

Example:
    profile_df = compute_modified_equilibrium(xon=0, xoff=300, dx=2, grain_size=0.25, dRatio=0.8, decay_coeff=1.5)
"""

from typing import Optional

import numpy as np
import pandas as pd


def compute_A_from_grain_size(d50_mm: float) -> float:
    """
    Compute Dean's A parameter (ft^(1/3)) from sediment grain size (mm).

    Equation (Dean, 1977):
        A = 0.21 * D50^0.48
    Converted to feet using (3.28084)^(1/3).
    """
    d50_m = d50_mm / 1000.0
    A_m = 0.21 * (d50_m**0.48)
    return A_m * (3.28084 ** (1.0 / 3.0))


def compute_modified_equilibrium(
    xon: float,
    xoff: float,
    dx: float,
    A: Optional[float] = None,
    grain_size: Optional[float] = None,
    dRatio: float = 1.0,
    decay_coeff: float = 1.0,
) -> pd.DataFrame:
    """
    Compute the modified equilibrium beach profile using the provided equation.

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
    dRatio : float
        Custom scaling factor for the profile's depth.
    decay_coeff : float
        Decay coefficient (λ). Controls the profile's decay over distance.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['X', 'Z'] representing the modified equilibrium profile.
    """
    if A is None and grain_size is None:
        raise ValueError("Either A or grain_size must be provided.")

    if A is None:
        assert grain_size is not None  # This should be guaranteed by the check above
        A = compute_A_from_grain_size(grain_size)

    x = np.arange(xon, xoff + dx, dx)
    term = x + (1 / decay_coeff) * (dRatio - 1) * (1 - np.exp(-decay_coeff * x))
    z = A * np.power(term, 2 / 3)

    profile_df = pd.DataFrame({"X": x, "Z": z})
    profile_df.attrs["method"] = "Modified Equilibrium"
    profile_df.attrs["parameters"] = {
        "A_ft13": A,
        "grain_size_mm": grain_size,
        "xon_ft": xon,
        "xoff_ft": xoff,
        "dx_ft": dx,
        "dRatio": dRatio,
        "decay_coeff_ft": decay_coeff,
    }

    return profile_df

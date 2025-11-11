# =============================================================================
# BMAP Sediment Transport Rate Calculation Tool
# =============================================================================
#
# FILE: src/profcalc/tools/bmap/bmap_sed_transport.py
#
# PURPOSE:
# This module computes cross-shore sediment transport rates between beach
# profile surveys using the Larson and Kraus (1989) methodology as implemented
# in BMAP. It calculates the cumulative volumetric changes to derive transport
# rates, providing quantitative estimates of sediment movement patterns.
#
# WHAT IT'S FOR:
# - Computing cross-shore sediment transport rates between profile surveys
# - Calculating cumulative volume changes along the profile
# - Deriving transport rates in cubic yards per foot per hour
# - Supporting temporal analysis of sediment transport patterns
# - Providing quantitative data for coastal sediment budget studies
#
# WORKFLOW POSITION:
# This tool is used in sediment transport analysis workflows to quantify
# the movement of sediment across the beach profile over time. It's essential
# for understanding erosion/accretion patterns and sediment budget calculations.
#
# LIMITATIONS:
# - Assumes one-dimensional cross-shore transport only
# - Requires accurate time intervals between surveys
# - Transport rates depend on profile interpolation accuracy
# - Does not account for longshore transport components
#
# ASSUMPTIONS:
# - Profile pairs represent the same physical cross-section
# - Time intervals are accurately known and appropriate for rate calculations
# - Elevation changes represent net sediment transport
# - Coordinate systems and datums are consistent between surveys
#
# =============================================================================

"""
Module: transport_rate
Location: profcalc.modules.profiles
--------------------------------------------
Computes the cross-shore sediment transport rate between two profiles
following Larson and Kraus (1989) as implemented in BMAP.

Equation:
    q(x) = -(1/Δt) * ∫_{xon}^{x} [η₂(ξ) - η₁(ξ)] dξ

Units:
    Input  X, Z in feet; Δt in hours
    Output q(x) in cubic yards per foot per hour (cu yd/ft/hr)

Example:
    profile_rate_df, report = compute_transport_rate(
        profile1=baseline_df,
        profile2=poststorm_df,
        dx=10.0,
        dtime_hr=48786.8
    )
"""

import numpy as np
import pandas as pd


def compute_transport_rate(
    profile1: pd.DataFrame, profile2: pd.DataFrame, dx: float, dtime_hr: float
) -> tuple[pd.DataFrame, str]:
    """
    Compute the cross-shore transport rate profile.

    Parameters
    ----------
    profile1 : pd.DataFrame
        Earlier profile with columns ['X', 'Z'].
    profile2 : pd.DataFrame
        Later profile with columns ['X', 'Z'].
    dx : float
        Horizontal increment (ft) for integration.
    dtime_hr : float
        Time difference between surveys (hours).

    Returns
    -------
    profile_rate_df : pd.DataFrame
        DataFrame with ['X', 'TransportRate_cuyd_per_ft_per_hr'].
    report : str
        Text summary matching BMAP's Transport Rate Report style.
    """
    # --- Validation ---
    if not {"X", "Z"}.issubset(profile1.columns) or not {"X", "Z"}.issubset(
        profile2.columns
    ):
        raise ValueError("Both profiles must contain columns ['X', 'Z'].")

    if dtime_hr <= 0:
        raise ValueError("Time difference (dtime_hr) must be positive.")

    # --- Common grid (uniform) ---
    x_min = max(profile1["X"].min(), profile2["X"].min())
    x_max = min(profile1["X"].max(), profile2["X"].max())
    x_grid = np.arange(x_min, x_max + dx, dx)

    # Interpolate both profiles onto same grid
    z1 = np.interp(x_grid, profile1["X"], profile1["Z"])
    z2 = np.interp(x_grid, profile2["X"], profile2["Z"])

    # --- Compute elevation change ---
    dz = z2 - z1  # positive = accretion (upward)

    # --- Cumulative integral (trapezoidal rule) ---
    # Integral of elevation change from landward boundary to each x
    cumulative_integral = np.cumsum(np.concatenate(([0], (dz[1:] + dz[:-1]) / 2 * dx)))

    # --- Transport rate per unit width (ft²/hr) ---
    q_ft2_hr = -cumulative_integral / dtime_hr  # minus sign from continuity

    # Convert to cubic yards per foot per hour
    q_cuyd_ft_hr = q_ft2_hr / 27.0

    # --- Build output DataFrame ---
    profile_rate_df = pd.DataFrame(
        {"X": x_grid, "TransportRate_cuyd_per_ft_per_hr": q_cuyd_ft_hr}
    )

    # --- Summary stats for report ---
    max_idx = np.argmax(q_cuyd_ft_hr)
    min_idx = np.argmin(q_cuyd_ft_hr)
    q_max, q_min = q_cuyd_ft_hr[max_idx], q_cuyd_ft_hr[min_idx]
    x_maxloc, x_minloc = x_grid[max_idx], x_grid[min_idx]
    q_seaward = q_cuyd_ft_hr[-1]
    x_seaward = x_grid[-1]

    # --- Build report string ---
    report = (
        f"Transport Rate Report\n"
        f"dX:\t{dx:.2f} ft\n"
        f"Time Difference:\t{dtime_hr:.2f} hr\n"
        f"Maximum Transport Rate:\t{q_max:.3f} cu. yd/ft/hr\n"
        f"   Location:\t{x_maxloc:.2f} ft\n"
        f"Minimum Transport Rate:\t{q_min:.3f} cu. yd/ft/hr\n"
        f"   Location:\t{x_minloc:.2f} ft\n"
        f"Rate at most seaward point:\t{q_seaward:.3f} cu. yd/ft/hr\n"
        f"   Location:\t{x_seaward:.2f} ft\n"
    )

    profile_rate_df.attrs["method"] = "Transport Rate (Larson & Kraus 1989)"
    profile_rate_df.attrs["parameters"] = {
        "dx_ft": dx,
        "dtime_hr": dtime_hr,
        "integration_range_ft": [float(x_min), float(x_max)],
    }

    return profile_rate_df, report

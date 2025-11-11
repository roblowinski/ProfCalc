# =============================================================================
# BMAP Profile Translation Tool
# =============================================================================
#
# FILE: src/profcalc/tools/bmap/bmap_translate.py
#
# PURPOSE:
# This module replicates BMAP's "Translate" tool functionality, providing
# uniform horizontal and vertical shifting of beach profile coordinates.
# It enables profile alignment, datum adjustments, and coordinate system
# transformations by applying consistent offsets to all profile points.
#
# WHAT IT'S FOR:
# - Applying horizontal shifts to align profiles at specific locations
# - Making vertical datum adjustments (e.g., tide corrections)
# - Transforming coordinate systems with uniform offsets
# - Supporting profile registration and alignment workflows
# - Enabling comparative analysis with adjusted coordinates
#
# WORKFLOW POSITION:
# This tool is used in profile preprocessing and alignment workflows when
# profiles need coordinate adjustments. It's particularly important when
# working with data from different surveys, coordinate systems, or tidal
# conditions that require uniform corrections.
#
# LIMITATIONS:
# - Applies only uniform (constant) shifts across the entire profile
# - Cannot handle non-uniform transformations or warping
# - Assumes all points require the same coordinate adjustments
# - Does not validate the physical meaningfulness of transformations
#
# ASSUMPTIONS:
# - Translation offsets are appropriate for all profile points
# - Coordinate adjustments maintain profile shape integrity
# - Users understand the implications of coordinate transformations
# - Translation preserves relative profile morphology
#
# =============================================================================

"""
Module: translate
Location: profcalc.modules.profiles
--------------------------------------------
Replicates BMAP's "Translate" tool.

Applies a uniform horizontal (ΔX) and/or vertical (ΔZ) shift
to a beach profile.

Example:
    translated = compute_translate(profile_df, dx=25.0, dz=-0.5)
"""

import pandas as pd


def compute_translate(
    profile: pd.DataFrame,
    dx: float = 0.0,
    dz: float = 0.0,
) -> pd.DataFrame:
    """
    Translate (shift) a profile horizontally and/or vertically.

    Parameters
    ----------
    profile : pd.DataFrame
        Input profile with columns ['X', 'Z'].
    dx : float, optional
        Horizontal translation in feet (+ seaward, - landward).
    dz : float, optional
        Vertical translation in feet (+ upward, - downward).

    Returns
    -------
    pd.DataFrame
        Translated profile with same number of points and new columns X, Z.
    """
    if not {"X", "Z"}.issubset(profile.columns):
        raise ValueError("Input DataFrame must contain columns ['X', 'Z'].")

    profile_shifted = profile.copy()
    profile_shifted["X"] = profile_shifted["X"] + dx
    profile_shifted["Z"] = profile_shifted["Z"] + dz

    profile_shifted.attrs["translation"] = {"dx": dx, "dz": dz}
    return profile_shifted

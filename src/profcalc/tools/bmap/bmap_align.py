# =============================================================================
# BMAP Profile Alignment Tool
# =============================================================================
#
# FILE: src/profcalc/tools/bmap/bmap_align.py
#
# PURPOSE:
# This module provides profile alignment functionality for BMAP analysis,
# allowing horizontal alignment of beach profiles at specified reference
# elevations. It's essential for comparing profiles that may have been
# surveyed at different horizontal positions or need to be aligned for
# accurate morphological comparison.
#
# WHAT IT'S FOR:
# - Horizontally aligning target profiles to reference profiles at specified elevations
# - Finding intersection points where profiles cross reference elevations
# - Supporting manual override of computed alignment positions
# - Enabling accurate profile comparisons by removing horizontal offsets
#
# WORKFLOW POSITION:
# This tool is used in profile comparison workflows when profiles need to
# be aligned before analysis. It's particularly important for comparing
# surveys taken at different times or by different methods that may have
# horizontal positioning variations.
#
# LIMITATIONS:
# - Requires profiles to cross the reference elevation
# - Assumes linear interpolation between profile points is adequate
# - Manual X_ref override may not be physically meaningful
# - Alignment assumes profiles represent the same physical location
#
# ASSUMPTIONS:
# - Reference elevation is meaningful for alignment (e.g., MHW, MSL)
# - Profile data is sorted by cross-shore distance
# - Alignment corrections are small relative to profile length
# - Users understand the implications of horizontal profile shifts
#
# =============================================================================

"""
Module: align_profiles
Location: profcalc.modules.profiles
--------------------------------------------
Horizontally aligns one beach profile (target) to another (reference)
at a specified elevation (Z_ref). Optionally, the user may override
the computed reference intersection with a manually supplied X_ref.

If the reference elevation (Z_ref) is not crossed by either profile,
no alignment is performed.

Example:
    aligned_df = compute_align_profiles(
        profile_ref=ref_df,
        profile_target=target_df,
        z_ref=0.0,
        x_ref=None
    )
"""

import pandas as pd


def _find_x_at_elevation(profile: pd.DataFrame, z_ref: float) -> float | None:
    """
    Find the X coordinate where the profile crosses a given elevation (Z_ref)
    using linear interpolation between adjacent points.

    Parameters
    ----------
    profile : pd.DataFrame
        Profile with columns ['X', 'Z'].
    z_ref : float
        Elevation (ft NAVD) to find intersection.

    Returns
    -------
    float | None
        X coordinate of crossing if found, else None.
    """
    x = profile["X"].values
    z = profile["Z"].values

    for i in range(len(x) - 1):
        if (z[i] - z_ref) * (z[i + 1] - z_ref) <= 0 and z[i] != z[i + 1]:
            # Linear interpolation
            frac = (z_ref - z[i]) / (z[i + 1] - z[i])
            return x[i] + frac * (x[i + 1] - x[i])

    return None


def compute_align_profiles(
    profile_ref: pd.DataFrame,
    profile_target: pd.DataFrame,
    z_ref: float,
    x_ref: float | None = None,
) -> pd.DataFrame:
    """
    Align the target profile horizontally to the reference profile
    at a specified elevation (Z_ref).

    Parameters
    ----------
    profile_ref : pd.DataFrame
        Reference profile (fixed) with columns ['X', 'Z'].
    profile_target : pd.DataFrame
        Target profile to shift, with columns ['X', 'Z'].
    z_ref : float
        Elevation (ft NAVD) to align at.
    x_ref : float, optional
        Manual override for the reference X location. If provided,
        this value replaces the computed X_ref from the reference profile.

    Returns
    -------
    pd.DataFrame
        New DataFrame of the aligned target profile, with columns ['X', 'Z'].
        Metadata includes alignment parameters.
    """
    # --- Validation ---
    if not {"X", "Z"}.issubset(profile_ref.columns):
        raise ValueError("Reference profile must contain columns ['X', 'Z'].")
    if not {"X", "Z"}.issubset(profile_target.columns):
        raise ValueError("Target profile must contain columns ['X', 'Z'].")

    # --- Find intersection points with z_ref ---
    x_ref_found = _find_x_at_elevation(profile_ref, z_ref)
    x_target_found = _find_x_at_elevation(profile_target, z_ref)

    if x_target_found is None:
        raise ValueError(
            "Target profile does not cross the specified elevation (Z_ref)."
        )
    if x_ref is None and x_ref_found is None:
        raise ValueError(
            "Reference profile does not cross the specified elevation (Z_ref)."
        )

    # --- Determine effective reference X location ---
    x_reference = x_ref if x_ref is not None else x_ref_found
    assert x_reference is not None  # Guaranteed by validation above

    # --- Compute shift ---
    dx_shift = x_target_found - x_reference

    # --- Apply horizontal shift to target profile ---
    aligned_df = profile_target.copy()
    aligned_df["X"] = aligned_df["X"] - dx_shift

    # --- Store metadata for traceability ---
    aligned_df.attrs["method"] = "Align Profiles"
    aligned_df.attrs["parameters"] = {
        "alignment_elevation_ft": float(z_ref),
        "x_reference_ft": float(x_reference),
        "x_shift_applied_ft": float(dx_shift),
        "x_ref_override": x_ref is not None,
    }

    return aligned_df

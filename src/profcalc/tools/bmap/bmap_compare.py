"""
Module: compare_profiles
Location: profcalc.modules.profiles
--------------------------------------------
Compares two beach profiles within a specified range.

Computes:
- Elevation difference (ΔZ)
- Volume change per unit width (cu. yd/ft)
- Horizontal shift of a user-specified contour (ft)

Uses global dX from config_utils.py, consistent with BMAP behavior.

Example:
    diff_df, report = compute_compare_profiles(
        profile1=poststorm_df,
        profile2=prestorm_df,
        xon=0.0,
        xoff=264.79,
        contour=0.0
    )
"""

import numpy as np
import pandas as pd

from profcalc.common.config_utils import get_dx


def _interp_x_at_contour(
    profile: pd.DataFrame, contour: float
) -> float | None:
    """
    Find the X coordinate where the profile crosses the specified elevation (contour)
    using linear interpolation between adjacent points.
    Returns None if the contour is not intersected.
    """
    x = profile["X"].values
    z = profile["Z"].values

    for i in range(len(x) - 1):
        if (z[i] - contour) * (z[i + 1] - contour) <= 0 and z[i] != z[i + 1]:
            frac = (contour - z[i]) / (z[i + 1] - z[i])
            return x[i] + frac * (x[i + 1] - x[i])

    return None


def compute_compare_profiles(
    profile1: pd.DataFrame,
    profile2: pd.DataFrame,
    xon: float,
    xoff: float,
    contour: float,
) -> tuple[pd.DataFrame, str]:
    """
    Compare two profiles between Xon and Xoff using global dX spacing.

    Parameters
    ----------
    profile1 : pd.DataFrame
        First profile (e.g., PostStorm) with columns ['X', 'Z'].
    profile2 : pd.DataFrame
        Second profile (e.g., PreStorm) with columns ['X', 'Z'].
    xon : float
        Landward limit (ft).
    xoff : float
        Seaward limit (ft).
    contour : float
        Elevation (ft NAVD) at which contour change is measured.

    Returns
    -------
    diff_df : pd.DataFrame
        DataFrame with columns ['X', 'Z1', 'Z2', 'DeltaZ'].
    report : str
        Text summary matching BMAP's "Profile Comparison Report".
    """
    # --- Validation ---
    if not {"X", "Z"}.issubset(profile1.columns):
        raise ValueError("Profile 1 must contain columns ['X', 'Z'].")
    if not {"X", "Z"}.issubset(profile2.columns):
        raise ValueError("Profile 2 must contain columns ['X', 'Z'].")

    if xoff <= xon:
        raise ValueError("xoff must be greater than xon.")

    # --- Get global dX ---
    dx = get_dx()

    # --- Common uniform grid ---
    x_grid = np.arange(xon, xoff + dx, dx)

    # Interpolate both profiles to same grid
    z1 = np.interp(x_grid, profile1["X"], profile1["Z"])
    z2 = np.interp(x_grid, profile2["X"], profile2["Z"])

    # --- Elevation difference ---
    dz = z1 - z2

    # --- Volume change (ft³/ft → yd³/ft) ---
    vol_ft3_per_ft = np.trapz(dz, x_grid)
    vol_cuyd_per_ft = float(vol_ft3_per_ft) / 27.0

    # --- Contour change (horizontal shift) ---
    x_contour_1 = _interp_x_at_contour(profile1, contour)
    x_contour_2 = _interp_x_at_contour(profile2, contour)
    contour_change = 0.0
    if x_contour_1 is not None and x_contour_2 is not None:
        contour_change = x_contour_1 - x_contour_2

    # --- Build comparison table ---
    diff_df = pd.DataFrame({"X": x_grid, "Z1": z1, "Z2": z2, "DeltaZ": dz})

    diff_df.attrs["method"] = "Compare Profiles"
    diff_df.attrs["parameters"] = {
        "xon_ft": float(xon),
        "xoff_ft": float(xoff),
        "contour_ft": float(contour),
        "volume_cuyd_per_ft": float(vol_cuyd_per_ft),
        "contour_change_ft": float(contour_change),
        "dx_ft": float(dx),
    }

    # --- Determine profile names from metadata (if available) ---
    name1 = profile1.attrs.get("name", "Profile 1")
    name2 = profile2.attrs.get("name", "Profile 2")

    # --- Build BMAP-style report ---
    report = (
        "Profile Comparison Report\n"
        f"Profile 1:\t{name1}\n"
        f"Profile 2:\t{name2}\n"
        f"XOn:\t{xon:.2f} ft\n"
        f"XOff:\t{xoff:.2f} ft\n"
        f"Contour:\t{contour:.2f} ft\n"
        f"Volume Change:\t{vol_cuyd_per_ft:.3f} cu. yd/ft\n"
        f"Contour Change:\t{contour_change:.2f} ft\n"
    )

    return diff_df, report


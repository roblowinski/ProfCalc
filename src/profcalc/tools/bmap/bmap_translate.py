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

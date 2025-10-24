"""
Module: slope_profile
Location: profile_analysis.modules.profiles
--------------------------------------------
Generates a linear interpolated synthetic beach profile between Xon and Xoff.

Computes profile elevation as:

    h(x) = h_on + ((h_off - h_on) / (X_off - X_on)) * (x - X_on)

User specifies:
- Horizontal range (Xon, Xoff) and spacing (dX)
- Elevation at Xon and Xoff

Example:
    profile_df = compute_slope_profile(xon=0, xoff=300, dx=2, elev_on=5, elev_off=2)
"""

import numpy as np
import pandas as pd


def compute_slope_profile(
    xon: float, xoff: float, dx: float, elev_on: float, elev_off: float
) -> pd.DataFrame:
    """
    Compute a linear interpolated beach profile.

    Parameters
    ----------
    xon : float
        Starting coordinate (ft).
    xoff : float
        Ending coordinate (ft).
    dx : float
        Horizontal spacing between profile points (ft).
    elev_on : float
        Elevation at Xon (ft).
    elev_off : float
        Elevation at Xoff (ft).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['X', 'Z'] representing the interpolated profile.
    """
    # Create an array of x values from Xon to Xoff with spacing dx
    x = np.arange(xon, xoff + dx, dx)

    # Compute the elevation at each point using linear interpolation
    slope = (elev_off - elev_on) / (xoff - xon)
    z = elev_on + slope * (x - xon)

    # Create DataFrame to return
    profile_df = pd.DataFrame({"X": x, "Z": z})
    profile_df.attrs["method"] = "Linear Interpolation"
    profile_df.attrs["parameters"] = {
        "elev_on_ft": elev_on,
        "elev_off_ft": elev_off,
        "xon_ft": xon,
        "xoff_ft": xoff,
        "dx_ft": dx,
    }

    return profile_df

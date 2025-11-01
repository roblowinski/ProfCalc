"""
Module: combine_profiles
Location: profcalc.modules.profiles
--------------------------------------------
Combines two beach profiles into one by either distance or elevation.

User can specify whether to combine the profiles based on a specific distance or a specific elevation.

Example:
    combined_profile_df = compute_combine_profiles(profile_df1, profile_df2, combine_by='distance', value=100)
    combined_profile_df = compute_combine_profiles(profile_df1, profile_df2, combine_by='elevation', value=5)
"""

import numpy as np
import pandas as pd


def combine_by_distance(
    profile1: pd.DataFrame, profile2: pd.DataFrame, distance: float
) -> pd.DataFrame:
    """
    Combine two profiles based on a specified distance.
    Profiles are aligned at the specified distance.

    Parameters
    ----------
    profile1, profile2 : pd.DataFrame
        Profile DataFrames with columns ['X', 'Z'].
    distance : float
        Distance (in feet) where the profiles will be aligned.

    Returns
    -------
    pd.DataFrame
        Combined profile DataFrame.
    """
    # Find the closest points to the specified distance in both profiles
    p1_nearest = profile1.iloc[(profile1["X"] - distance).abs().argsort()[:1]]
    p2_nearest = profile2.iloc[(profile2["X"] - distance).abs().argsort()[:1]]

    # Combine the profiles
    combined_df = pd.concat([p1_nearest, p2_nearest], ignore_index=True)
    combined_df = combined_df.sort_values(by="X").reset_index(drop=True)

    return combined_df


def combine_by_elevation(
    profile1: pd.DataFrame,
    profile2: pd.DataFrame,
    elevation: float,
    retain_distance: bool,
) -> pd.DataFrame:
    """
    Combine two profiles based on a specified elevation.
    Profiles are aligned at the specified elevation.

    Parameters
    ----------
    profile1, profile2 : pd.DataFrame
        Profile DataFrames with columns ['X', 'Z'].
    elevation : float
        Elevation (in feet) where the profiles will be aligned.
    retain_distance : bool
        Whether to retain original distance values (True) or adjust them (False).

    Returns
    -------
    pd.DataFrame
        Combined profile DataFrame.
    """
    # Find the closest points to the specified elevation in both profiles
    p1_nearest = profile1.iloc[(profile1["Z"] - elevation).abs().argsort()[:1]]
    p2_nearest = profile2.iloc[(profile2["Z"] - elevation).abs().argsort()[:1]]

    # If retaining distance values, use the original X values; otherwise, align distances
    if retain_distance:
        combined_df = pd.concat([p1_nearest, p2_nearest], ignore_index=True)
    else:
        # Adjust the X values of both profiles based on the specified distance
        new_x = np.mean([p1_nearest["X"].values[0], p2_nearest["X"].values[0]])
        p1_nearest["X"] = new_x
        p2_nearest["X"] = new_x
        combined_df = pd.concat([p1_nearest, p2_nearest], ignore_index=True)

    combined_df = combined_df.sort_values(by="X").reset_index(drop=True)

    return combined_df


def compute_combine_profiles(
    profile1: pd.DataFrame,
    profile2: pd.DataFrame,
    combine_by: str,
    value: float,
    retain_distance: bool = False,
) -> pd.DataFrame:
    """
    Combine two beach profiles into one.

    Parameters
    ----------
    profile1, profile2 : pd.DataFrame
        Profile DataFrames with columns ['X', 'Z'].
    combine_by : str
        Either 'distance' or 'elevation' to specify how the profiles should be combined.
    value : float
        The distance or elevation value to combine the profiles by.
    retain_distance : bool, optional
        Whether to retain original distance values when combining by elevation (default is False).

    Returns
    -------
    pd.DataFrame
        Combined profile DataFrame.
    """
    if combine_by == "distance":
        return combine_by_distance(profile1, profile2, value)
    elif combine_by == "elevation":
        return combine_by_elevation(profile1, profile2, value, retain_distance)
    else:
        raise ValueError(
            "Invalid 'combine_by' value. Use 'distance' or 'elevation'."
        )

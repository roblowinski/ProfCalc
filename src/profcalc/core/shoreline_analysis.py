import math
from typing import Dict, Optional

import pandas as pd


def extract_seaward_most_position(profile: pd.DataFrame, target_elevation: float) -> Optional[Dict[str, float]]:
    """
    Extract the seaward-most cross-shore distance and real-world coordinates where the profile crosses a target elevation.

    Args:
        profile: DataFrame with columns 'X' (distance) and 'Z' (elevation).
        target_elevation: Elevation to find (e.g., 4.0).

    Returns:
        A dictionary containing the elevation, cross-shore distance, easting, northing, and elevation.
    """
    x = profile['X'].values
    z = profile['Z'].values

    seaward_most = None

    for i in range(len(x) - 1):
        if (z[i] - target_elevation) * (z[i + 1] - target_elevation) <= 0:
            # Linear interpolation to find the crossing point
            frac = (target_elevation - z[i]) / (z[i + 1] - z[i])
            cross_shore_x = x[i] + frac * (x[i + 1] - x[i])
            seaward_most = {
                "Elevation": target_elevation,
                "CrossShoreX": cross_shore_x,
                "Z": target_elevation  # Elevation remains the same
            }

    return seaward_most

def calculate_real_world_coordinates(point: Dict[str, float], origin_easting: float, origin_northing: float, azimuth: float) -> Dict[str, float]:
    """
    Convert a cross-shore distance to real-world coordinates (Easting, Northing).

    Args:
        point: A point with 'CrossShoreX' and 'Z'.
        origin_easting: Easting of the profile origin.
        origin_northing: Northing of the profile origin.
        azimuth: Azimuth of the profile in degrees.

    Returns:
        The point with added 'Easting' and 'Northing'.
    """
    azimuth_rad = math.radians(azimuth)
    cross_shore_x = point['CrossShoreX']
    point['Easting'] = origin_easting + cross_shore_x * math.cos(azimuth_rad)
    point['Northing'] = origin_northing + cross_shore_x * math.sin(azimuth_rad)
    return point

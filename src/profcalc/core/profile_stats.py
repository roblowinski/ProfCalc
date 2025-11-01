"""
Profile statistics and geometric calculations module.

Provides functions for calculating profile characteristics including:
- Common X ranges across surveys
- Berm width detection
- Beach face slope calculation
- Elevation statistics
"""

from typing import Dict, List, Optional, Tuple

# Type alias for a list of (x, z) coordinate pairs
Points = List[Tuple[float, float]]


def _sorted_points(points: Points) -> Points:
    """Return a new list of points sorted by X coordinate.

    Keeps the original list unmodified.
    """
    return sorted(points, key=lambda p: p[0])


def _avg_spacing_from_sorted(sorted_points: Points) -> float:
    """Compute average spacing between consecutive sorted points.

    Returns 0.0 when spacing cannot be computed.
    """
    if len(sorted_points) < 2:
        return 0.0
    spacings: List[float] = []
    for i in range(1, len(sorted_points)):
        spacing = sorted_points[i][0] - sorted_points[i - 1][0]
        if spacing > 0:
            spacings.append(spacing)
    return sum(spacings) / len(spacings) if spacings else 0.0


def _profile_length_from_sorted(sorted_points: Points) -> float:
    """Compute the 2D profile length along sorted points.

    Uses euclidean distances between consecutive points.
    """
    if len(sorted_points) < 2:
        return 0.0
    length = 0.0
    for i in range(1, len(sorted_points)):
        dx = sorted_points[i][0] - sorted_points[i - 1][0]
        dy = sorted_points[i][1] - sorted_points[i - 1][1]
        length += (dx**2 + dy**2) ** 0.5
    return length


def _elevation_stats(points: Points) -> Tuple[float, float, float, float]:
    """Return (min, max, avg, range) for elevation values in points.

    If points is empty all values default to 0.0.
    """
    if not points:
        return 0.0, 0.0, 0.0, 0.0
    elevations = [p[1] for p in points]
    min_elev = min(elevations)
    max_elev = max(elevations)
    avg_elev = sum(elevations) / len(elevations)
    elev_range = max_elev - min_elev
    return min_elev, max_elev, avg_elev, elev_range


def _compute_slopes(points: Points) -> List[float]:
    """Compute absolute slopes between consecutive points.

    Returns list of slopes (abs(dz/dx)). Zero is used when dx == 0.
    """
    slopes: List[float] = []
    for i in range(1, len(points)):
        dx = points[i][0] - points[i - 1][0]
        dz = points[i][1] - points[i - 1][1]
        slopes.append(abs(dz / dx) if dx > 0 else 0.0)
    return slopes


def _find_low_slope_segments(
    pts: Points, slopes: List[float], threshold: float = 0.05
) -> List[Points]:
    """Return continuous low-slope segments from pts using slopes list.

    A low-slope segment is a list of consecutive points where the
    corresponding slope values are all below `threshold`.
    """
    low_slope_segments: List[Points] = []
    current: Points = []
    for i, s in enumerate(slopes):
        if s < threshold:
            current.append(pts[i])
        else:
            if len(current) >= 2:
                low_slope_segments.append(current)
            current = []
    if len(current) >= 2:
        low_slope_segments.append(current)
    return low_slope_segments


def calculate_common_ranges(
    profiles: Dict[str, List[List[Tuple[float, float]]]],
    mhw_elev: Optional[float] = None,
) -> Dict[
    str,
    Tuple[
        float,
        float,
        int,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        str,
    ],
]:
    """
    For each profile name, calculate comprehensive profile characteristics
    across all profiles with that name.

    Args:
        profiles: Dictionary from parse_bmap_file mapping profile names to lists of point lists
        mhw_elev: Optional Mean High Water elevation for geometric properties

    Returns:
        Dictionary mapping profile names to comprehensive statistics tuple:
        (Xmin_Common, Xmax_Common, num_surveys, avg_spacing, total_length, completeness,
         min_elev, max_elev, avg_elev, elev_range, profile_length, avg_slope,
         berm_width, beach_face_slope, beach_type)
    """
    from .beach_classification import classify_beach_type

    common_ranges = {}

    for profile_name, profile_list in profiles.items():
        if not profile_list:
            continue

        # Collect min/max x for each profile instance
        min_xs = []
        max_xs = []
        all_points = []

        for points in profile_list:
            if not points:
                continue
            xs = [point[0] for point in points]
            min_xs.append(min(xs))
            max_xs.append(max(xs))
            all_points.extend(points)

        if min_xs and max_xs and all_points:
            # Common range is the overlap
            xmin_common = max(min_xs)
            xmax_common = min(max_xs)

            # Only include if there's actual overlap
            if xmin_common <= xmax_common:
                num_surveys = len(profile_list)

                # Average point spacing
                if len(all_points) > 1:
                    sorted_points = _sorted_points(all_points)
                    avg_spacing = _avg_spacing_from_sorted(sorted_points)
                else:
                    avg_spacing = 0.0

                # Total profile length (sum of all survey lengths)
                total_length = sum(
                    max_x - min_x for min_x, max_x in zip(min_xs, max_xs)
                )

                # Data completeness
                surveyed_range = (
                    max(max_xs) - min(min_xs) if max_xs and min_xs else 0.0
                )
                common_range_length = xmax_common - xmin_common
                completeness = (
                    (common_range_length / surveyed_range) * 100
                    if surveyed_range > 0
                    else 0.0
                )

                # Elevation statistics
                (
                    min_elev,
                    max_elev,
                    avg_elev,
                    elev_range,
                ) = _elevation_stats(all_points)

                # Profile length (actual distance)
                if len(all_points) > 1:
                    sorted_points = _sorted_points(all_points)
                    profile_length = _profile_length_from_sorted(sorted_points)
                else:
                    profile_length = 0.0

                # Average slope
                avg_slope = (
                    (max_elev - min_elev) / (xmax_common - xmin_common)
                    if (xmax_common - xmin_common) > 0
                    else 0.0
                )

                # Geometric properties (only if MHW provided)
                berm_width = 0.0
                beach_face_slope = 0.0
                beach_type = "UNKNOWN"

                if mhw_elev is not None:
                    berm_width = calculate_berm_width(all_points, mhw_elev)
                    beach_face_slope = calculate_beach_face_slope(
                        all_points, mhw_elev
                    )
                    beach_type = classify_beach_type(beach_face_slope)

                common_ranges[profile_name] = (
                    xmin_common,
                    xmax_common,
                    num_surveys,
                    avg_spacing,
                    total_length,
                    completeness,
                    min_elev,
                    max_elev,
                    avg_elev,
                    elev_range,
                    profile_length,
                    avg_slope,
                    berm_width,
                    beach_face_slope,
                    beach_type,
                )

    return common_ranges


def calculate_berm_width(points: Points, mhw_elev: float) -> float:
    """
    Calculate berm width using slope-based criteria above MHW.

    Args:
        points: List of (x, z) coordinates sorted by x
        mhw_elev: Mean High Water elevation (ft NAVD88)

    Returns:
        Berm width in feet, or 0.0 if no berm detected
    """
    # =======================================================================
    # METHODOLOGY:
    # -----------
    # Berms are identified as relatively flat platform areas above Mean High Water (MHW)
    # that represent the backshore depositional zone. This implementation uses a
    # slope-based detection algorithm adapted from coastal engineering standards.
    #
    # MATHEMATICAL APPROACH:
    # ---------------------
    # 1. Filter points above MHW elevation: P_above = {p | p.z >= MHW}
    # 2. Calculate slope between consecutive points: s_i = (z_{i+1} - z_i) / (x_{i+1} - x_i)
    # 3. Identify low-slope segments: segments where |s_i| < 0.05 (5% slope threshold)
    # 4. Find longest continuous low-slope segment
    # 5. Calculate width: width = x_end - x_start of longest segment
    #
    # SLOPE THRESHOLD JUSTIFICATION:
    # -----------------------------
    # - 5% slope threshold based on USACE Coastal Engineering Manual (CEM)
    # - Berms typically have slopes < 5% (nearly horizontal platforms)
    # - Distinguishes berms from steeper beach face and dune transitions
    #
    # REFERENCES:
    # ----------
    # - USACE (2015). Coastal Engineering Manual. Part III-2, Chapter 3.
    # - Larson, M., & Kraus, N. C. (1989). SBEACH: Numerical model for simulating
    #   storm-induced beach change. Report 1: Empirical foundation and model
    #   development. Technical Report CERC-89-9, US Army Engineer Waterways
    #   Experiment Station.
    # - Stockdon, H. F., et al. (2007). National assessment of shoreline change:
    #   Historical shoreline change along the Pacific Northwest coast. Open-File
    #   Report 2007-1133, USGS.
    #
    # LIMITATIONS:
    # ------------
    # - Assumes berm is the longest flat area above MHW
    # - May not detect narrow berms or multiple berm segments
    # - Sensitive to point density and MHW accuracy
    # =======================================================================

    if not points:
        return 0.0

    # Find points above MHW
    berm_candidates = [p for p in points if p[1] >= mhw_elev]

    if len(berm_candidates) < 3:
        return 0.0

    # Sort berm candidates and compute slopes
    berm_candidates = _sorted_points(berm_candidates)
    slopes = _compute_slopes(berm_candidates)

    # Find continuous segments with low slope (<5%)
    low_slope_segments = _find_low_slope_segments(berm_candidates, slopes)

    # Return width of longest low-slope segment
    if low_slope_segments:
        longest_segment = max(low_slope_segments, key=len)
        return longest_segment[-1][0] - longest_segment[0][0]

    return 0.0


def calculate_beach_face_slope(points: Points, mhw_elev: float) -> float:
    """
    Calculate beach face slope from MHW to the first point below MHW.

    Args:
        points: List of (x, z) coordinates sorted by x
        mhw_elev: Mean High Water elevation (ft NAVD88)

    Returns:
        Beach face slope (rise/run), or 0.0 if cannot calculate
    """
    # =======================================================================
    # METHODOLOGY:
    # -----------
    # The beach face slope represents the primary dissipative zone between the
    # shoreline and berm toe. This method calculates the slope of the active
    # beach face using a simplified linear regression approach.
    #
    # MATHEMATICAL APPROACH:
    # ---------------------
    # 1. Find MHW intercept point: p_mhw = first point where z >= MHW
    # 2. Find seaward points below MHW: P_seaward = {p | p.x > p_mhw.x ∧ p.z < MHW}
    # 3. Select representative seaward point: p_beach = point with z closest to MHW
    # 4. Calculate slope: slope = (p_beach.z - p_mhw.z) / (p_beach.x - p_mhw.x)
    #
    # SLOPE INTERPRETATION:
    # --------------------
    # - Negative slopes (typical): Beach face declines seaward
    # - Slope magnitude: |slope| > 0.1 (10%) = reflective beach
    #                  |slope| < 0.02 (2%) = dissipative beach
    #                  0.02 < |slope| < 0.1 = intermediate beach
    #
    # REFERENCES:
    # ----------
    # - Wright, L. D., & Short, A. D. (1984). Morphodynamic variability of
    #   surf zones and beaches: A synthesis. Marine Geology, 56(1-4), 93-118.
    # - Stockdon, H. F., et al. (2006). Empirical parameterization of setup,
    #   swash, and runup. Coastal Engineering, 53(7), 573-588.
    # - USACE (2015). Coastal Engineering Manual. Part III-2, Beach Profiles.
    # =======================================================================

    if not points:
        return 0.0

    # Sort points by x
    sorted_points = _sorted_points(points)

    # Find MHW intercept (first point at or above MHW)
    mhw_point = None
    for point in sorted_points:
        if point[1] >= mhw_elev:
            mhw_point = point
            break

    if not mhw_point:
        return 0.0

    # Find the first point below MHW seaward of MHW point
    seaward_points = [
        p for p in sorted_points if p[0] > mhw_point[0] and p[1] < mhw_elev
    ]

    if not seaward_points:
        return 0.0

    # Use the point closest to MHW elevation below it
    beach_point = min(seaward_points, key=lambda p: abs(p[1] - mhw_elev))

    # Calculate slope
    dx = beach_point[0] - mhw_point[0]
    dz = beach_point[1] - mhw_point[1]

    if dx > 0:
        return dz / dx  # Negative slope expected for beach face

    return 0.0

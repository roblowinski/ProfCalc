# =============================================================================
# Coordinate Transformation and Baseline Management Utilities
# =============================================================================
#
# FILE: src/profcalc/common/coordinate_transforms.py
#
# PURPOSE:
# This module provides comprehensive coordinate transformation functionality
# for beach profile analysis, handling conversions between different coordinate
# systems commonly used in coastal engineering. It manages the complex
# transformations between geographic coordinates, profile-relative coordinates,
# and baseline-based systems.
#
# WHAT IT'S FOR:
# - Transforms 3D survey points (X, Y, Z) to 2D profile coordinates
# - Converts geographic/projected coordinates to profile-relative distances
# - Manages profile baseline definitions and calculations
# - Handles azimuth-based transformations for shoreline orientation
# - Supports batch processing of multiple profiles and points
# - Provides accurate geometric calculations for coastal analysis
#
# WORKFLOW POSITION:
# This module is fundamental to beach profile analysis, as it handles the
# coordinate transformations that convert raw survey data into meaningful
# profile representations. It's used whenever profile data needs to be
# analyzed in cross-shore vs. elevation space rather than geographic coordinates.
#
# LIMITATIONS:
# - Requires accurate baseline definitions (origin points and azimuths)
# - Assumes planar geometry (may not be suitable for very large areas)
# - Coordinate transformations depend on consistent coordinate systems
# - Complex geometries may require multiple baseline segments
#
# ASSUMPTIONS:
# - Coordinate systems are consistent and properly referenced
# - Baseline azimuths are accurately measured and specified
# - Profile geometries can be represented by straight baselines
# - Elevation data is relative to appropriate vertical datums
# - Users understand coordinate system transformations
#
# =============================================================================

"""
Coordinate Transformation Utilities

This module provides functions for transforming between different coordinate systems
commonly used in beach profile analysis:

- 3D to 2D conversion: Convert survey points (X, Y, Z) to profile coordinates (cross-shore distance, elevation)
- Profile-relative coordinates: Transform geographic coordinates to distances along a profile baseline
- Baseline calculations: Define profile baselines from origin points and azimuths

Key transformations:
- Geographic/Projected coordinates → Profile-relative coordinates
- 3D survey points → 2D profile lines
"""

from typing import List, Tuple

import numpy as np
import pandas as pd

from .bmap_io import Profile
from .error_handler import (
    BeachProfileError,
    ErrorCategory,
    LogComponent,
    get_logger,
)


def calculate_point_profile_offset(
    origin_x: float,
    origin_y: float,
    azimuth: float,
    point_x: float,
    point_y: float,
) -> float:
    """Calculate the cross-shore distance of a point from a profile baseline.

    Computes the perpendicular distance from a point to a profile baseline defined
    by an origin point and azimuth angle. Positive distances indicate points
    seaward of the baseline, negative distances indicate landward points.

    Args:
        origin_x: X-coordinate of the profile origin point (baseline start).
        origin_y: Y-coordinate of the profile origin point (baseline start).
        azimuth: Azimuth angle of the baseline in degrees (0° = north, 90° = east,
            clockwise positive).
        point_x: X-coordinate of the point to measure from the baseline.
        point_y: Y-coordinate of the point to measure from the baseline.

    Returns:
        Cross-shore distance from the baseline in the same units as input
        coordinates. Positive values indicate seaward direction, negative
        values indicate landward direction.
    """
    # Convert azimuth to radians (0 = north, clockwise positive)
    azimuth_rad = np.radians(azimuth)
    cos_a = np.cos(azimuth_rad)
    sin_a = np.sin(azimuth_rad)

    # Vector from origin to point
    dx = point_x - origin_x
    dy = point_y - origin_y

    # Rotate coordinates so that profile direction aligns with X-axis
    # Rotation matrix: [cos(-a), -sin(-a)] = [cos(a), sin(a)]
    #                  [sin(-a),  cos(-a)] = [-sin(a), cos(a)]

    # Transform coordinates using rotation by -azimuth
    # This rotates so that the baseline aligns with the X-axis
    y_rotated = -dx * sin_a + dy * cos_a

    # Cross-shore distance is the Y coordinate in the rotated system
    # This represents the perpendicular distance from the baseline
    return y_rotated


def convert_3d_to_2d_profile(
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    z_coords: np.ndarray,
    origin_x: float,
    origin_y: float,
    azimuth: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Convert 3D survey points to 2D profile coordinates.

    Takes 3D coordinates (X, Y, Z) and transforms them to 2D profile coordinates
    (cross-shore distance, elevation) relative to a profile baseline.

    Args:
        x_coords: Array of X coordinates (easting/longitude)
        y_coords: Array of Y coordinates (northing/latitude)
        z_coords: Array of Z coordinates (elevation)
        origin_x: X-coordinate of profile origin
        origin_y: Y-coordinate of profile origin
        azimuth: Profile azimuth in degrees (0 = north, 90 = east)

    Returns:
        Tuple of (cross_shore_distances, elevations)
    """
    if len(x_coords) != len(y_coords) or len(x_coords) != len(z_coords):
        raise BeachProfileError(
            f"Coordinate arrays must have same length: X={len(x_coords)}, Y={len(y_coords)}, Z={len(z_coords)}",
            category=ErrorCategory.SPATIAL,
        )

    # Calculate cross-shore distances for all points
    cross_shore_distances = np.array(
        [
            calculate_point_profile_offset(origin_x, origin_y, azimuth, x, y)
            for x, y in zip(x_coords, y_coords)
        ]
    )

    return cross_shore_distances, z_coords


def transform_profile_to_2d(
    profile: Profile, origin_x: float, origin_y: float, azimuth: float
) -> Profile:
    """Transform a 3D profile to 2D profile coordinates.

    Takes a Profile object with 3D coordinates in metadata and transforms
    it to 2D profile coordinates suitable for BMAP-style analysis.

    Args:
        profile: Profile object with 3D coordinates in metadata
        origin_x: X-coordinate of profile origin
        origin_y: Y-coordinate of profile origin
        azimuth: Profile azimuth in degrees

    Returns:
        New Profile object with 2D coordinates

    Raises:
        CoordinateTransformError: If profile doesn't have required 3D coordinates
    """
    # Check if profile has Y coordinates in metadata
    if not hasattr(profile, "metadata") or profile.metadata is None:
        raise BeachProfileError(
            "Profile must have metadata with Y coordinates",
            category=ErrorCategory.SPATIAL,
        )

    y_coords = profile.metadata.get("y_coordinates")
    if y_coords is None:
        raise BeachProfileError(
            "Profile metadata must contain 'y_coordinates'",
            category=ErrorCategory.SPATIAL,
        )

    if len(y_coords) != len(profile.x):
        raise BeachProfileError(
            f"Y coordinate array length ({len(y_coords)}) doesn't match X coordinates ({len(profile.x)})",
            category=ErrorCategory.SPATIAL,
        )

    # Convert to 2D coordinates
    cross_shore_distances, elevations = convert_3d_to_2d_profile(
        profile.x, y_coords, profile.z, origin_x, origin_y, azimuth
    )

    # Create new profile with 2D coordinates
    new_metadata = profile.metadata.copy()
    new_metadata["original_3d_coords"] = {
        "x": profile.x.copy(),
        "y": y_coords.copy(),
        "z": profile.z.copy(),
    }
    new_metadata["profile_origin"] = {"x": origin_x, "y": origin_y}
    new_metadata["profile_azimuth"] = azimuth
    new_metadata["transformation"] = "3D_to_2D"

    # Update description to indicate transformation
    new_description = profile.description or ""
    if new_description:
        new_description += "; "
    new_description += f"Transformed to 2D (origin: {origin_x:.1f}, {origin_y:.1f}, azimuth: {azimuth:.1f}°)"

    new_profile = Profile(
        name=profile.name,
        date=profile.date,
        description=new_description,
        x=cross_shore_distances,
        z=elevations,
        metadata=new_metadata,
    )

    return new_profile


def batch_transform_profiles_to_2d(
    profiles: List[Profile], origin_x: float, origin_y: float, azimuth: float
) -> List[Profile]:
    """Transform multiple 3D profiles to 2D coordinates with error handling.

    Applies 3D-to-2D coordinate transformation to a list of Profile objects.
    Profiles that fail transformation are logged as warnings and skipped,
    allowing the batch process to continue with successful transformations.

    Args:
        profiles: List of Profile objects containing 3D coordinate data in
            metadata. Each profile must have 'y_coordinates' in metadata.
        origin_x: X-coordinate of the profile origin point for all profiles.
        origin_y: Y-coordinate of the profile origin point for all profiles.
        azimuth: Azimuth angle in degrees for the baseline direction
            (0° = north, 90° = east).

    Returns:
        List of successfully transformed Profile objects with 2D coordinates.
        Failed transformations are omitted from the result with warning logs.
    """
    transformed_profiles = []

    for profile in profiles:
        try:
            transformed = transform_profile_to_2d(profile, origin_x, origin_y, azimuth)
            transformed_profiles.append(transformed)
        except BeachProfileError as e:
            logger = get_logger(LogComponent.SPATIAL)
            logger.warning(f"Failed to transform profile {profile.name}: {e}")
            continue

    return transformed_profiles


def estimate_profile_baseline(
    x_coords: np.ndarray, y_coords: np.ndarray
) -> Tuple[float, float, float]:
    """Estimate profile baseline from a set of points.

    Uses principal component analysis to estimate the profile direction
    and finds the origin as the landward-most point.

    Args:
        x_coords: Array of X coordinates
        y_coords: Array of Y coordinates

    Returns:
        Tuple of (origin_x, origin_y, azimuth)
    """
    # Center the points
    x_mean: float = float(np.mean(x_coords))
    y_mean: float = float(np.mean(y_coords))
    x_centered = x_coords - x_mean
    y_centered = y_coords - y_mean

    # Compute covariance matrix
    cov_matrix = np.cov(x_centered, y_centered)

    # Find principal component (direction of maximum variance)
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    max_eigenvalue_idx = np.argmax(eigenvalues)
    principal_component = eigenvectors[:, max_eigenvalue_idx]

    # Calculate azimuth from principal component
    # Principal component gives direction vector
    dx, dy = principal_component
    azimuth = np.degrees(np.arctan2(dx, dy))  # atan2(dx, dy) gives angle from north

    # Ensure azimuth is between 0 and 360
    if azimuth < 0:
        azimuth += 360

    # Find origin as the point with minimum cross-shore distance
    # (assuming the profile extends seaward from the origin)
    cross_shore_distances = np.array(
        [
            calculate_point_profile_offset(x_mean, y_mean, azimuth, x, y)
            for x, y in zip(x_coords, y_coords)
        ]
    )

    min_distance_idx = np.argmin(cross_shore_distances)
    origin_x = x_coords[min_distance_idx]
    origin_y = y_coords[min_distance_idx]

    return origin_x, origin_y, azimuth


def load_profile_baselines(
    baseline_file_path: str,
) -> dict[str, dict[str, float]]:
    """Load profile baseline configurations from CSV file.

    Args:
        baseline_file_path: Path to CSV file containing profile baselines

    Returns:
        Dictionary mapping profile names to baseline parameters
        Format: {profile_name: {'x0': float, 'y0': float, 'azimuth': float}}
    """
    df = pd.read_csv(baseline_file_path)

    # Validate required columns
    required_cols = ["profile_name", "x0", "y0", "azimuth"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Baseline file missing required columns: {missing_cols}")

    baselines = {}
    for _, row in df.iterrows():
        baselines[row["profile_name"]] = {
            "x0": float(row["x0"]),
            "y0": float(row["y0"]),
            "azimuth": float(row["azimuth"]),
        }

    return baselines


def transform_profiles_with_baselines(
    profiles: List[Profile], baseline_file_path: str
) -> List[Profile]:
    """Transform multiple 3D profiles to 2D using individual baseline configurations.

    Loads profile-specific baseline parameters from a CSV file and applies
    customized 3D-to-2D transformations for each profile. Profiles without
    matching baselines in the file are skipped with warnings.

    Args:
        profiles: List of Profile objects containing 3D coordinate data.
            Each profile must have 'y_coordinates' in metadata.
        baseline_file_path: Path to CSV file containing baseline configurations.
            Must include columns: 'profile_name', 'x0', 'y0', 'azimuth'.

    Returns:
        List of successfully transformed Profile objects with 2D coordinates.
        Profiles without matching baselines are omitted with warning logs.

    Raises:
        ValueError: If the baseline file is missing required columns or
            cannot be read.
    """
    baselines = load_profile_baselines(baseline_file_path)
    transformed_profiles = []

    for profile in profiles:
        baseline = baselines.get(profile.name)
        if baseline is None:
            logger = get_logger(LogComponent.SPATIAL)
            logger.warning(
                f"No baseline found for profile {profile.name}, skipping transformation"
            )
            continue

        try:
            transformed = transform_profile_to_2d(
                profile, baseline["x0"], baseline["y0"], baseline["azimuth"]
            )
            transformed_profiles.append(transformed)
        except (
            ValueError,
            TypeError,
            KeyError,
            IndexError,
            RuntimeError,
        ) as e:
            logger = get_logger(LogComponent.SPATIAL)
            logger.error(f"Failed to transform profile {profile.name}: {e}")

    return transformed_profiles


def convert_2d_to_3d_profile(
    cross_shore_distances: np.ndarray,
    elevations: np.ndarray,
    origin_x: float,
    origin_y: float,
    azimuth: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert 2D profile coordinates back to 3D survey points.

    Takes 2D profile coordinates (cross-shore distance, elevation) and transforms
    them back to 3D coordinates (X, Y, Z) using the profile baseline.

    The cross-shore distance represents the perpendicular distance from the baseline,
    so we need to project this distance perpendicular to the baseline direction.

    Args:
        cross_shore_distances: Array of cross-shore distances from baseline
        elevations: Array of Z coordinates (elevations)
        origin_x: X-coordinate of profile origin
        origin_y: Y-coordinate of profile origin
        azimuth: Profile azimuth in degrees (0 = north, 90 = east)

    Returns:
        Tuple of (x_coords, y_coords, z_coords) - the 3D coordinates
    """
    if len(cross_shore_distances) != len(elevations):
        raise BeachProfileError(
            f"Coordinate arrays must have same length: cross_shore={len(cross_shore_distances)}, elevations={len(elevations)}",
            category=ErrorCategory.SPATIAL,
        )

    # Convert azimuth to radians (0 = north, clockwise positive)
    azimuth_rad = np.radians(azimuth)

    # The cross-shore distance represents the perpendicular distance from the baseline
    # To convert back to 3D coordinates, place the point at that perpendicular distance
    # The direction perpendicular to the baseline is azimuth + 90°

    cos_perp = np.cos(azimuth_rad + np.pi / 2)  # cos(a + 90°) = -sin(a)
    sin_perp = np.sin(azimuth_rad + np.pi / 2)  # sin(a + 90°) = cos(a)

    # Project cross-shore distance in the perpendicular direction
    x_coords = origin_x + cross_shore_distances * cos_perp
    y_coords = origin_y + cross_shore_distances * sin_perp

    return x_coords, y_coords, elevations


def transform_profile_to_3d(
    profile: Profile, origin_x: float, origin_y: float, azimuth: float
) -> Profile:
    """Transform a 2D profile back to 3D coordinates.

    Converts a Profile object with 2D coordinates (cross-shore distance, elevation)
    back to 3D coordinates (X, Y, Z) using the specified profile baseline.
    This is useful for exporting 2D analysis results back to 3D formats.

    Args:
        profile: Profile object with 2D coordinates (cross-shore distances in
            x attribute, elevations in z attribute).
        origin_x: X-coordinate of the profile origin point.
        origin_y: Y-coordinate of the profile origin point.
        azimuth: Azimuth angle in degrees for the baseline direction
            (0° = north, 90° = east).

    Returns:
        New Profile object with 3D coordinates (X, Y, Z) and updated metadata
        indicating the transformation.

    Raises:
        BeachProfileError: If the coordinate transformation fails due to
            invalid input data.
    """
    # Convert 2D coordinates back to 3D
    x_coords, y_coords, z_coords = convert_2d_to_3d_profile(
        profile.x, profile.z, origin_x, origin_y, azimuth
    )

    # Create new profile with 3D coordinates
    new_metadata = profile.metadata.copy() if profile.metadata else {}
    new_metadata["y_coordinates"] = y_coords
    new_metadata["transformation"] = "2D_to_3D"

    # Update description to indicate transformation
    new_description = profile.description or ""
    if new_description:
        new_description += "; "
    new_description += f"Converted to 3D (origin: {origin_x:.1f}, {origin_y:.1f}, azimuth: {azimuth:.1f}°)"

    new_profile = Profile(
        name=profile.name,
        date=profile.date,
        description=new_description,
        x=x_coords,
        z=z_coords,
        metadata=new_metadata,
    )

    return new_profile


def batch_transform_profiles_to_3d(
    profiles: List[Profile], origin_x: float, origin_y: float, azimuth: float
) -> List[Profile]:
    """Transform multiple 2D profiles back to 3D coordinates with error handling.

    Applies 2D-to-3D coordinate transformation to a list of Profile objects.
    Profiles that fail transformation are logged as warnings and skipped,
    allowing the batch process to continue with successful transformations.

    Args:
        profiles: List of Profile objects containing 2D coordinate data
            (cross-shore distances in x, elevations in z).
        origin_x: X-coordinate of the profile origin point for all profiles.
        origin_y: Y-coordinate of the profile origin point for all profiles.
        azimuth: Azimuth angle in degrees for the baseline direction
            (0° = north, 90° = east).

    Returns:
        List of successfully transformed Profile objects with 3D coordinates.
        Failed transformations are omitted from the result with warning logs.
    """
    transformed_profiles = []

    for profile in profiles:
        try:
            transformed = transform_profile_to_3d(profile, origin_x, origin_y, azimuth)
            transformed_profiles.append(transformed)
        except BeachProfileError as e:
            logger = get_logger(LogComponent.SPATIAL)
            logger.warning(f"Failed to transform profile {profile.name}: {e}")
            continue

    return transformed_profiles

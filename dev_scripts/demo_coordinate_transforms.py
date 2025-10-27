#!/usr/bin/env python3
"""
Example usage of 3D to 2D coordinate transformation utilities.

This script demonstrates how to convert 3D survey data (X, Y, Z coordinates)
to 2D profile coordinates (cross-shore distance, elevation) that are compatible
with BMAP analysis tools.
"""

import os

# Add src to path for imports
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from profcalc.common import (  # type: ignore[import]
    convert_3d_to_2d_profile,
    estimate_profile_baseline,
    transform_profile_to_2d,
)
from profcalc.common.bmap_io import Profile  # type: ignore[import]


def demo_3d_to_2d_conversion():
    """Demonstrate basic 3D to 2D coordinate conversion."""

    print("=== 3D to 2D Coordinate Conversion Demo ===\n")

    # Sample 3D survey points forming a simple beach profile
    # X, Y, Z coordinates (simulated survey data)
    x_coords = np.array([100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0])
    y_coords = np.array([200.0, 200.5, 201.0, 201.5, 202.0, 202.5, 203.0])  # Slight alongshore variation
    z_coords = np.array([2.5, 2.3, 2.1, 1.8, 1.2, 0.5, -0.2])  # Beach profile elevations

    # Define profile baseline (origin and direction)
    origin_x, origin_y = 100.0, 200.0  # Start of profile
    azimuth = 45.0  # 45 degrees from north (northeast direction)

    print("Original 3D coordinates:")
    print("Point  X      Y      Z")
    for i, (x, y, z) in enumerate(zip(x_coords, y_coords, z_coords)):
        print("4d")

    print(f"\nProfile baseline: origin=({origin_x}, {origin_y}), azimuth={azimuth}°")

    # Convert to 2D profile coordinates
    cross_shore_distances, elevations = convert_3d_to_2d_profile(
        x_coords, y_coords, z_coords, origin_x, origin_y, azimuth
    )

    print("\nConverted 2D profile coordinates:")
    print("Point  Cross-shore  Elevation")
    for i, (dist, elev) in enumerate(zip(cross_shore_distances, elevations)):
        print("4d")

    return cross_shore_distances, elevations


def demo_profile_transformation():
    """Demonstrate transforming a Profile object from 3D to 2D."""

    print("\n=== Profile Object 3D to 2D Transformation ===\n")

    # Create a sample profile with 3D coordinates in metadata
    x_coords = np.array([500.0, 505.0, 510.0, 515.0, 520.0])
    y_coords = np.array([300.0, 300.2, 300.4, 300.6, 300.8])
    z_coords = np.array([3.0, 2.8, 2.5, 2.0, 1.5])

    # Create Profile object with Y coordinates in metadata
    profile_3d = Profile(
        name="Sample_Profile_001",
        date="2024-01-15",
        description="Sample beach profile with 3D coordinates",
        x=x_coords,
        z=z_coords,
        metadata={
            'y_coordinates': y_coords,
            'survey_method': 'RTK_GPS',
            'units': 'meters'
        }
    )

    print("Original 3D Profile:")
    print(f"Name: {profile_3d.name}")
    print(f"Date: {profile_3d.date}")
    print("Coordinates (X, Y, Z):")
    y_coords = profile_3d.metadata.get('y_coordinates', []) if profile_3d.metadata else []
    for i, (x, y, z) in enumerate(zip(profile_3d.x, y_coords, profile_3d.z)):
        print("4d")

    # Define profile baseline
    origin_x, origin_y = 500.0, 300.0
    azimuth = 30.0  # 30 degrees from north

    # Transform to 2D
    profile_2d = transform_profile_to_2d(profile_3d, origin_x, origin_y, azimuth)

    print("\nTransformed 2D Profile:")
    print(f"Name: {profile_2d.name}")
    print(f"Description: {profile_2d.description}")
    print("Coordinates (Cross-shore distance, Elevation):")
    for i, (dist, elev) in enumerate(zip(profile_2d.x, profile_2d.z)):
        print("6.1f")

    metadata_keys = list(profile_2d.metadata.keys()) if profile_2d.metadata else []
    print(f"\nMetadata preserved: {metadata_keys}")

    return profile_2d


def demo_baseline_estimation():
    """Demonstrate automatic baseline estimation from survey points."""

    print("\n=== Automatic Baseline Estimation ===\n")

    # Generate sample survey points along a profile
    np.random.seed(42)  # For reproducible results

    # Create points along a profile line with some noise
    n_points = 20
    distances = np.linspace(0, 100, n_points)  # Cross-shore distances

    # Profile baseline: origin at (1000, 2000), azimuth 60°
    true_origin_x, true_origin_y = 1000.0, 2000.0
    true_azimuth = 60.0

    # Convert distances back to geographic coordinates
    azimuth_rad = np.radians(true_azimuth)
    x_coords = true_origin_x + distances * np.sin(azimuth_rad)
    y_coords = true_origin_y + distances * np.cos(azimuth_rad)

    # Add some noise to simulate real survey data
    x_coords += np.random.normal(0, 0.5, n_points)
    y_coords += np.random.normal(0, 0.5, n_points)

    print("Sample survey points (first 5):")
    print("Point  X        Y        Z")
    for i in range(5):
        print("4d")

    # Estimate baseline from the points
    est_origin_x, est_origin_y, est_azimuth = estimate_profile_baseline(x_coords, y_coords)

    print("\nEstimated baseline:")
    print(f"  Origin X: {est_origin_x:.1f}")
    print(f"  Origin Y: {est_origin_y:.1f}")
    print(f"  Azimuth: {est_azimuth:.1f}°")

    print("\nTrue baseline:")
    print(f"  Origin X: {true_origin_x:.1f}")
    print(f"  Origin Y: {true_origin_y:.1f}")
    print(f"  Azimuth: {true_azimuth:.1f}°")

    # Calculate errors
    origin_error = np.sqrt((est_origin_x - true_origin_x)**2 + (est_origin_y - true_origin_y)**2)
    azimuth_error = abs(est_azimuth - true_azimuth)

    print("\nEstimation errors:")
    print(f"  Origin error: {origin_error:.2f} meters")
    print(f"  Azimuth error: {azimuth_error:.1f}°")


if __name__ == "__main__":
    demo_3d_to_2d_conversion()
    demo_profile_transformation()
    demo_baseline_estimation()

    print("\n=== Demo Complete ===")
    print("The coordinate transformation utilities are ready for use with CSV and 9-column data!")

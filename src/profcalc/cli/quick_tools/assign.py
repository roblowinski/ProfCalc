"""
Assign XYZ Points - Assign scattered XYZ points to profile lines.

Uses perpendicular distance calculations to assign survey points to their
nearest profile baseline. Requires baseline data (origin coordinates and azimuths).
"""

import argparse
from typing import NamedTuple

import numpy as np
import pandas as pd


class ProfileBaseline(NamedTuple):
    """Profile baseline definition."""

    name: str
    origin_x: float
    origin_y: float
    azimuth: float  # degrees from north


class XYZPoint(NamedTuple):
    """XYZ survey point."""

    x: float
    y: float
    z: float


def execute_from_cli(args: list[str]) -> None:
    """
    Execute XYZ point assignment from command line.

    Args:
        args: Command-line arguments (excluding the -a flag)
    """
    parser = argparse.ArgumentParser(
        prog="profcalc -a",
        description="Assign XYZ points to profile lines using perpendicular distance",
    )
    parser.add_argument("xyz_file", help="XYZ data file (space or comma separated)")
    parser.add_argument(
        "--baseline", required=True, help="Baseline CSV file (name,x,y,azimuth)"
    )
    parser.add_argument("-o", "--output", required=True, help="Output BMAP file path")
    parser.add_argument(
        "-t",
        "--tolerance",
        type=float,
        default=10.0,
        help="Maximum perpendicular distance in feet (default: 10.0)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed assignment info"
    )

    parsed_args = parser.parse_args(args)

    print(f"🔍 Reading XYZ points from: {parsed_args.xyz_file}")
    print(f"📐 Reading baselines from: {parsed_args.baseline}")
    print(f"📏 Tolerance: {parsed_args.tolerance} ft")

    # Read data
    xyz_points = read_xyz_points(parsed_args.xyz_file)
    baselines = read_baseline_csv(parsed_args.baseline)

    print(f"   Found {len(xyz_points)} XYZ points")
    print(f"   Found {len(baselines)} profile baseline(s)")

    # Assign points to profiles
    assignments = assign_points_to_profiles(
        xyz_points, baselines, tolerance=parsed_args.tolerance
    )

    # Generate report
    print("\n" + "=" * 60)
    print("ASSIGNMENT SUMMARY")
    print("=" * 60)

    total_assigned = 0
    for profile_name, points in assignments.items():
        print(f"  {profile_name}: {len(points)} points")
        total_assigned += len(points)

    unassigned = len(xyz_points) - total_assigned
    if unassigned > 0:
        print(f"  Unassigned: {unassigned} points (exceeded tolerance)")

    print(f"\nTotal: {total_assigned}/{len(xyz_points)} points assigned")

    # Convert to BMAP profiles and write
    print(f"\n💾 Writing BMAP file: {parsed_args.output}")
    profiles = convert_to_bmap_profiles(assignments, baselines)
    write_bmap_output(profiles, parsed_args.output, source_file=parsed_args.xyz_file)

    print("✅ Assignment complete!")


def read_xyz_points(file_path: str) -> list[XYZPoint]:
    """
    Read XYZ points from file.

    Supports space or comma separated format:
    X Y Z
    or
    X,Y,Z

    Args:
        file_path: Path to XYZ file

    Returns:
        List of XYZPoint objects
    """
    points = []

    with open(file_path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(">"):
                continue

            # Replace commas with spaces and split
            parts = line.replace(",", " ").split()

            try:
                if len(parts) >= 3:
                    x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                    points.append(XYZPoint(x, y, z))
            except ValueError:
                print(f"Warning: Skipping invalid line {line_num}: {line}")
                continue

    return points


def read_baseline_csv(file_path: str) -> list[ProfileBaseline]:
    """
    Read profile baseline data from CSV.

    Expected format:
    profile_name,origin_x,origin_y,azimuth

    Args:
        file_path: Path to baseline CSV file

    Returns:
        List of ProfileBaseline objects
    """
    baselines = []

    df = pd.read_csv(file_path, thousands=",")

    # Normalize column names (handle case variations and Origin_X vs origin_x)
    df.columns = df.columns.str.lower().str.replace("origin_", "origin")

    # Check for required columns (flexible naming)
    name_col = None
    x_col = None
    y_col = None
    az_col = None

    for col in df.columns:
        if "name" in col:
            name_col = col
        elif col in ["originx", "origin_x", "x"]:
            x_col = col
        elif col in ["originy", "origin_y", "y"]:
            y_col = col
        elif "azimuth" in col or col == "az":
            az_col = col

    if not all([name_col, x_col, y_col, az_col]):
        raise ValueError(
            f"Baseline CSV must have columns for: profile_name, origin_x, origin_y, azimuth\n"
            f"Found: {', '.join(df.columns)}"
        )

    # Type assertions for mypy
    assert name_col is not None
    assert x_col is not None
    assert y_col is not None
    assert az_col is not None

    for _, row in df.iterrows():
        baselines.append(
            ProfileBaseline(
                name=str(row[name_col]),
                origin_x=float(row[x_col]),
                origin_y=float(row[y_col]),
                azimuth=float(row[az_col]),
            )
        )

    return baselines


def assign_points_to_profiles(
    points: list[XYZPoint],
    baselines: list[ProfileBaseline],
    tolerance: float = 10.0,
) -> dict[str, list[tuple[float, float]]]:
    """
    Assign XYZ points to profiles using perpendicular distance.

    For each point, calculates the perpendicular distance to each profile
    baseline and assigns to the nearest profile if within tolerance.

    Args:
        points: List of XYZ points to assign
        baselines: List of profile baselines
        tolerance: Maximum perpendicular distance in feet

    Returns:
        Dictionary mapping profile names to lists of (along_profile_distance, elevation) tuples
    """
    assignments: dict[str, list[tuple[float, float]]] = {
        baseline.name: [] for baseline in baselines
    }

    for point in points:
        best_profile = None
        best_distance = float("inf")
        best_along_dist = 0.0

        # Find nearest profile
        for baseline in baselines:
            perp_dist, along_dist = calculate_distances(point, baseline)

            if abs(perp_dist) < abs(best_distance):
                best_distance = perp_dist
                best_profile = baseline.name
                best_along_dist = along_dist

        # Assign if within tolerance
        if best_profile and abs(best_distance) <= tolerance:
            assignments[best_profile].append((best_along_dist, point.z))

    return assignments


def calculate_distances(
    point: XYZPoint, baseline: ProfileBaseline
) -> tuple[float, float]:
    """
    Calculate perpendicular and along-profile distances.

    Uses coordinate transformation to rotate the point into the profile's
    local coordinate system where the profile runs along the X-axis.

    Args:
        point: XYZ point
        baseline: Profile baseline

    Returns:
        Tuple of (perpendicular_distance, along_profile_distance)
    """
    # Convert azimuth to radians (measured clockwise from North)
    # In standard math, angles are counterclockwise from East
    # Azimuth: 0° = North, 90° = East, 180° = South, 270° = West
    # We need to convert to standard mathematical angle
    math_angle = np.radians(90 - baseline.azimuth)

    # Translate point to baseline origin
    dx = point.x - baseline.origin_x
    dy = point.y - baseline.origin_y

    # Rotate to profile coordinate system
    cos_theta = np.cos(math_angle)
    sin_theta = np.sin(math_angle)

    # Along-profile distance (X' in rotated system)
    along_dist = dx * cos_theta + dy * sin_theta

    # Perpendicular distance (Y' in rotated system)
    perp_dist = -dx * sin_theta + dy * cos_theta

    return perp_dist, along_dist


def convert_to_bmap_profiles(
    assignments: dict[str, list[tuple[float, float]]], baselines: list[ProfileBaseline]
) -> list:
    """
    Convert assigned points to BMAP Profile objects.

    Args:
        assignments: Dictionary of profile assignments
        baselines: List of profile baselines (for ordering)

    Returns:
        List of Profile objects
    """
    from profcalc.common.bmap_io import Profile

    profiles = []

    # Process in baseline order
    for baseline in baselines:
        points = assignments.get(baseline.name, [])

        if not points:
            continue

        # Sort by along-profile distance
        points.sort(key=lambda p: p[0])

        # Extract coordinates
        x_coords = np.array([p[0] for p in points])
        z_coords = np.array([p[1] for p in points])

        profiles.append(
            Profile(
                name=baseline.name,
                date=None,
                description="Assigned from XYZ",
                x=x_coords,
                z=z_coords,
            )
        )

    return profiles


def write_bmap_output(profiles: list, output_file: str, source_file: str | None = None) -> None:
    """
    Write profiles to BMAP format file.

    Args:
        profiles: List of Profile objects
        output_file: Output file path
        source_file: Optional source XYZ filename for date extraction
    """
    from profcalc.common.bmap_io import write_bmap_profiles

    write_bmap_profiles(profiles, output_file, source_filename=source_file)


def execute_from_menu() -> None:
    """Execute XYZ point assignment from interactive menu."""
    print("\n" + "=" * 60)
    print("ASSIGN XYZ POINTS TO PROFILES")
    print("=" * 60)

    # Get user inputs
    xyz_file = input("Enter XYZ data file path: ").strip()
    baseline_file = input("Enter baseline CSV file path: ").strip()
    output_file = input("Enter output BMAP file path: ").strip()

    tolerance_input = input("Maximum perpendicular distance (ft) [10.0]: ").strip()
    tolerance = float(tolerance_input) if tolerance_input else 10.0

    try:
        print("\n🔄 Processing point assignments...")

        # Read data
        xyz_points = read_xyz_points(xyz_file)
        baselines = read_baseline_csv(baseline_file)

        print(f"   Found {len(xyz_points)} XYZ points")
        print(f"   Found {len(baselines)} profile baseline(s)")

        # Assign points
        assignments = assign_points_to_profiles(xyz_points, baselines, tolerance)

        # Show summary
        print("\n" + "=" * 60)
        print("ASSIGNMENT SUMMARY")
        print("=" * 60)

        total_assigned = 0
        for profile_name, points in assignments.items():
            print(f"  {profile_name}: {len(points)} points")
            total_assigned += len(points)

        unassigned = len(xyz_points) - total_assigned
        if unassigned > 0:
            print(f"  Unassigned: {unassigned} points (exceeded tolerance)")

        print(f"\nTotal: {total_assigned}/{len(xyz_points)} points assigned")

        # Write output
        profiles = convert_to_bmap_profiles(assignments, baselines)
        write_bmap_output(profiles, output_file, source_file=xyz_file)

        print(f"\n✅ BMAP file written to: {output_file}")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

    input("\nPress Enter to continue...")


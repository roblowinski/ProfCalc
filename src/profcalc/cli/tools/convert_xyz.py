# =============================================================================
# XYZ Format Conversion and Processing Tool
# =============================================================================
#
# FILE: src/profcalc/cli/tools/convert_xyz.py
#
# PURPOSE:
# This module provides comprehensive utilities for reading, writing, and
# processing XYZ format files containing beach profile survey data. It handles
# coordinate transformations, profile creation from point clouds, and conversion
# between XYZ and other formats like BMAP.
#
# WHAT IT'S FOR:
# - Reads XYZ format files with automatic delimiter detection
# - Converts XYZ point clouds to structured beach profile objects
# - Handles flexible column ordering (X,Y,Z in any position)
# - Supports coordinate transformations and baseline adjustments
# - Writes profile data back to XYZ format when needed
# - Provides validation and error handling for XYZ data
# - Supports both 2D and 3D coordinate systems
#
# WORKFLOW POSITION:
# This tool is used when working with raw survey data in XYZ format, which is
# common from laser scanning, GPS surveys, and other point cloud data sources.
# It serves as a bridge between unstructured point data and structured profile
# analysis, enabling the use of diverse survey data sources in beach morphology
# studies.
#
# LIMITATIONS:
# - Requires clear column identification for X, Y, Z coordinates
# - May struggle with noisy or irregular point distributions
# - Coordinate transformations require proper baseline definitions
# - Large XYZ files may require significant memory for processing
# - Assumes points represent meaningful profile transects
#
# ASSUMPTIONS:
# - XYZ files contain coordinate data in standard units (feet or meters)
# - Points are organized in roughly linear profile transects
# - Column order can be determined from data patterns or user input
# - Coordinate systems are consistent and properly referenced
# - Users understand XYZ data structure and coordinate conventions
#
# =============================================================================

"""XYZ format conversion utilities.

This module handles reading and writing XYZ format files, including
coordinate transformations and profile creation from XYZ points.
"""

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from profcalc.cli.file_dialogs import select_input_file, select_output_file
from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.common.bmap_io import Profile, write_bmap_profiles


def _read_xyz_format(
    input_file: str,
    column_order: Optional[Dict[str, int]] = None,
    delimiter: str = "auto",
) -> List[Profile]:
    """
    Read XYZ format file and convert to Profile objects.

    Parameters:
        input_file: Path to XYZ file
        column_order: Optional column mapping for X, Y, Z axes
        delimiter: Field delimiter ("auto", ",", " ", "\t", etc.)

    Returns:
        List of Profile objects
    """
    try:
        # Auto-detect delimiter if requested
        if delimiter == "auto":
            delimiter = _detect_xyz_delimiter(input_file)

        # Read the file
        df = pd.read_csv(
            input_file,
            delimiter=delimiter,
            header=None,
            comment="#",
            engine="python",  # More flexible delimiter handling
        )

        if df.empty:
            raise ValueError("XYZ file is empty or contains no valid data")

        # Determine column order
        if column_order is None:
            column_order = {"x": 0, "y": 1, "z": 2}  # Default X Y Z order

        # Validate we have enough columns
        max_col_idx = max(column_order.values())
        if df.shape[1] <= max_col_idx:
            raise ValueError(
                f"File has {df.shape[1]} columns, but column order requires "
                f"column {max_col_idx}"
            )

        # Extract coordinates
        x_col = column_order["x"]
        y_col = column_order.get("y", -1)  # Y is optional for 2D
        z_col = column_order["z"]

        # Convert to numeric, drop invalid rows
        df.iloc[:, x_col] = pd.to_numeric(df.iloc[:, x_col], errors="coerce")
        if y_col >= 0:
            df.iloc[:, y_col] = pd.to_numeric(df.iloc[:, y_col], errors="coerce")
        df.iloc[:, z_col] = pd.to_numeric(df.iloc[:, z_col], errors="coerce")

        # Drop rows with NaN in required columns
        required_cols = [x_col, z_col]
        if y_col >= 0:
            required_cols.append(y_col)

        df = df.dropna(subset=required_cols)

        if df.empty:
            raise ValueError("No valid numeric data found in XYZ file")

        # Group by profile (assuming sorted by profile)
        # For now, treat all points as one profile
        # TODO: Add profile grouping logic if profile IDs are present

        x_coords = df.iloc[:, x_col].values
        z_coords = df.iloc[:, z_col].values

        # Create profile metadata
        metadata = {}
        if y_col >= 0:
            y_coords = df.iloc[:, y_col].values
            metadata["y_coordinates"] = y_coords

        # Sort by X coordinate
        sort_indices = np.argsort(x_coords)
        x_coords = x_coords[sort_indices]
        z_coords = z_coords[sort_indices]

        if "y_coordinates" in metadata:
            metadata["y_coordinates"] = metadata["y_coordinates"][sort_indices]

        # Create profile
        profile = Profile(name="XYZ_Profile", x=x_coords, z=z_coords, metadata=metadata)

        return [profile]

    except (IOError, OSError, ValueError, UnicodeDecodeError) as e:
        log_quick_tool_error(
            "convert_xyz", f"Error reading XYZ file {input_file}: {e}", exc=e
        )
        raise


def _detect_xyz_delimiter(file_path: str) -> str:
    """
    Auto-detect delimiter in XYZ file.

    Parameters:
        file_path: Path to XYZ file

    Returns:
        Detected delimiter
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Read first few lines
            lines = []
            for i, line in enumerate(f):
                if line.strip() and not line.startswith("#"):
                    lines.append(line)
                if len(lines) >= 5:
                    break

        if not lines:
            return ","  # Default

        # Count potential delimiters
        delimiters = [",", "\t", " ", ";"]
        scores = {}

        for delim in delimiters:
            total_parts = 0
            consistent_parts = 0

            for line in lines:
                parts = line.split(delim)
                num_parts = len([p for p in parts if p.strip()])

                if total_parts == 0:
                    first_count = num_parts
                    total_parts = num_parts
                    consistent_parts = num_parts
                else:
                    total_parts += num_parts
                    if abs(num_parts - first_count) <= 1:  # Allow small variations
                        consistent_parts += num_parts

            if total_parts > 0:
                scores[delim] = consistent_parts / total_parts
            else:
                scores[delim] = 0

        # Return delimiter with highest consistency score
        best_delim = max(scores, key=scores.get)
        return best_delim

    except (ValueError, TypeError, IndexError):
        return ","  # Default fallback


def _create_profile_from_xyz_points(
    points_df: pd.DataFrame,
    profile_id: str = "XYZ_Profile",
    column_order: Optional[Dict[str, int]] = None,
) -> Profile:
    """
    Create a Profile object from XYZ point data.

    Parameters:
        points_df: DataFrame with XYZ point data
        profile_id: Name/ID for the profile
        column_order: Optional column mapping

    Returns:
        Profile object
    """
    if column_order is None:
        column_order = {"x": 0, "y": 1, "z": 2}

    # Extract coordinates
    x_coords = points_df.iloc[:, column_order["x"]].values
    z_coords = points_df.iloc[:, column_order["z"]].values

    # Sort by X coordinate
    sort_indices = np.argsort(x_coords)
    x_coords = x_coords[sort_indices]
    z_coords = z_coords[sort_indices]

    # Create metadata
    metadata = {"source": "xyz"}
    if "y" in column_order and column_order["y"] >= 0:
        y_coords = points_df.iloc[:, column_order["y"]].values
        metadata["y_coordinates"] = y_coords[sort_indices]

    return Profile(name=profile_id, x=x_coords, z=z_coords, metadata=metadata)


def _write_xyz_format(profiles: List[Profile], output_file: str) -> None:
    """
    Write profiles to XYZ format file.

    Parameters:
        profiles: List of Profile objects to write
        output_file: Output file path
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            # Write header comment
            f.write("# XYZ format export\n")
            f.write("# X Y Z (cross-shore, along-shore, elevation)\n")
            f.write("# Units: feet\n\n")

            for profile in profiles:
                if profile is None:
                    continue

                x_coords = profile.x
                z_coords = profile.z

                # Check if we have Y coordinates
                y_coords = None
                if hasattr(profile, "metadata") and profile.metadata:
                    y_coords = profile.metadata.get("y_coordinates")

                # Write points
                for i in range(len(x_coords)):
                    x = x_coords[i]
                    z = z_coords[i]

                    if y_coords is not None and i < len(y_coords):
                        y = y_coords[i]
                        f.write(f"{x:.3f},{y:.3f},{z:.3f}\n")
                    else:
                        # 2D format: X, 0, Z
                        f.write(f"{x:.3f},0.000,{z:.3f}\n")

                # Add blank line between profiles
                f.write("\n")

        print(f"✅ XYZ file written: {output_file}")

    except (IOError, OSError, ValueError, AttributeError) as e:
        log_quick_tool_error(
            "convert_xyz", f"Error writing XYZ file {output_file}: {e}", exc=e
        )
        raise


def _check_xyz_format(input_file: str) -> bool:
    """
    Check if file appears to be in XYZ format.

    Parameters:
        input_file: Path to file to check

    Returns:
        True if file appears to be XYZ format
    """
    try:
        # Quick check: read first few lines and look for numeric data
        with open(input_file, "r", encoding="utf-8") as f:
            lines = []
            for i, line in enumerate(f):
                line = line.strip()
                if line and not line.startswith("#"):
                    lines.append(line)
                if len(lines) >= 3:
                    break

        if len(lines) < 2:
            return False

        # Check if lines contain numeric coordinates
        numeric_lines = 0
        for line in lines:
            parts = line.replace(",", " ").split()
            if len(parts) >= 2:  # At least X and Z
                try:
                    coords = [float(p) for p in parts[:3]]  # Try first 3 parts
                    if len(coords) >= 2:  # At least X and Z
                        numeric_lines += 1
                except ValueError:
                    continue

        # If most lines are numeric, likely XYZ format
        return numeric_lines >= len(lines) * 0.8

    except (IOError, OSError, ValueError, UnicodeDecodeError):
        return False


def execute_xyz_to_bmap() -> None:
    """
    Interactive conversion of XYZ files to BMAP format.
    """
    from profcalc.cli.menu_system import notify_and_wait

    print("\n" + "=" * 60)
    print("CONVERT XYZ TO BMAP")
    print("=" * 60)

    # Get input file
    print("Select an XYZ input file...")
    input_file = select_input_file("Select XYZ Input File")
    if not input_file:
        print("No input file specified.")
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    input_path = Path(input_file)
    if not input_path.exists():
        print(f"File not found: {input_file}")
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    # Get output file
    print("Select a BMAP output file...")
    output_file = select_output_file("Select BMAP Output File")
    if not output_file:
        print("No output file specified.")
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    # Get column order
    print("\nColumn order options:")
    print("1. X Y Z (default)")
    print("2. Y X Z")
    print("3. Z X Y")
    print("4. Custom order")

    col_choice = input("Choose column order (1-4): ").strip()

    column_order = None
    if col_choice == "2":
        column_order = {"x": 1, "y": 0, "z": 2}
    elif col_choice == "3":
        column_order = {"x": 1, "y": 2, "z": 0}
    elif col_choice == "4":
        order_str = input("Enter column order (e.g., 'Y X Z'): ").strip()
        try:
            from .convert_core import _parse_column_order

            column_order = _parse_column_order(order_str)
        except ValueError as e:
            print(f"Invalid column order: {e}")
            notify_and_wait("", prompt="\nPress Enter to continue...")
            return

    # Get delimiter
    delimiter = input("Enter delimiter (default: auto-detect): ").strip() or "auto"

    try:
        # Read XYZ file
        print(f"🔍 Reading XYZ file: {input_file}")
        profiles = _read_xyz_format(input_file, column_order, delimiter)

        if not profiles:
            print("❌ No profiles found in XYZ file.")
            notify_and_wait("", prompt="\nPress Enter to continue...")
            return

        print(f"📊 Found {len(profiles)} profiles")

        # Write BMAP file
        print(f"💾 Writing BMAP file: {output_file}")
        write_bmap_profiles(profiles, output_file)

        print(f"✅ BMAP file created: {output_file}")

    except (IOError, OSError, ValueError, AttributeError, KeyError) as e:
        log_quick_tool_error(
            "convert_xyz", f"Error in XYZ to BMAP conversion: {e}", exc=e
        )
        print(f"❌ Error: {e}")

    notify_and_wait("", prompt="\nPress Enter to continue...")

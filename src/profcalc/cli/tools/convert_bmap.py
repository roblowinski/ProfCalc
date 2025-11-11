# =============================================================================
# BMAP Format Conversion Tool
# =============================================================================
#
# FILE: src/profcalc/cli/tools/convert_bmap.py
#
# PURPOSE:
# This module provides conversion utilities between BMAP (Beach Morphology
# Analysis Package) format files and other common data formats like CSV.
# It supports both 2D and 3D coordinate systems and handles the complex
# header structures and metadata associated with BMAP files.
#
# WHAT IT'S FOR:
# - Converts BMAP free-format files to CSV format for broader compatibility
# - Supports both 2D (X,Z) and 3D (X,Y,Z) coordinate output
# - Handles BMAP header metadata and profile information
# - Provides interactive file selection through graphical dialogs
# - Supports batch conversion workflows
# - Maintains data integrity during format conversion
#
# WORKFLOW POSITION:
# This tool is used when data needs to be exchanged between BMAP-specific
# analysis tools and more general-purpose data processing software. It's
# commonly used for data export, sharing with other teams, or integration
# with GIS systems that prefer CSV format over BMAP's specialized structure.
#
# LIMITATIONS:
# - Conversion is one-way (BMAP to CSV); reverse conversion requires other tools
# - Some BMAP-specific metadata may not translate directly to CSV format
# - Large BMAP files may require significant memory for conversion
# - CSV output may lose some structural information from BMAP headers
#
# ASSUMPTIONS:
# - Input BMAP files are properly formatted and contain valid profile data
# - Users understand the differences between BMAP and CSV data structures
# - Coordinate systems are appropriate for the target application
# - Output file locations have appropriate write permissions
#
# =============================================================================

"""BMAP conversion utilities.

This module handles conversion between BMAP format and other formats
like CSV, with support for 2D and 3D output.
"""

import csv
from typing import List, Optional

from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.common.bmap_io import read_bmap_freeformat

from .convert_core import (
    _calculate_real_world_coordinates,
    _read_baseline_file,
)


def execute_bmap_to_csv() -> None:
    """
    Interactive conversion of BMAP files to CSV format.
    """
    from profcalc.cli.file_dialogs import select_input_file, select_output_file
    from profcalc.cli.menu_system import notify_and_wait
    from profcalc.common.colors import (
        error,
        info,
        print_header,
        print_success,
        prompt,
        warning,
    )

    print_header("Convert BMAP to CSV")

    # Get input file
    print(info("Select a BMAP free format file..."))
    input_file = select_input_file("Select BMAP Free Format File")
    if not input_file:
        print(warning("No input file specified."))
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    # Get output file
    print(info("Select a CSV output file..."))
    output_file = select_output_file("Select CSV Output File")
    if not output_file:
        print(warning("No output file specified."))
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    # Get output format
    print()
    print(info("Output format options:"))
    print("1. 2D CSV (X, Z coordinates)")
    print("2. 3D CSV (X, Y, Z coordinates)")
    print("3. 9-column CSV (with metadata)")

    format_choice = input(prompt("Choose format (1-3): ")).strip()

    # Get baseline file if needed
    use_baselines = (
        input(prompt("Use baseline file for real-world coordinates? (y/N): "))
        .strip()
        .lower()
    )
    baseline_file = None
    if use_baselines == "y":
        print(info("Select a baseline file..."))
        baseline_file = select_input_file("Select Baseline File")
        if not baseline_file:
            print(error("No baseline file specified."))
            notify_and_wait("", prompt="\nPress Enter to continue...")
            return

    try:
        # Read BMAP file
        print(info(f"Reading BMAP file: {input_file}"))
        profiles = read_bmap_freeformat(input_file)

        if not profiles:
            print(error("No profiles found in BMAP file."))
            notify_and_wait("", prompt="\nPress Enter to continue...")
            return

        print(info(f"Found {len(profiles)} profiles"))

        # Apply baseline transformations if requested
        baseline_data = None
        if baseline_file:
            print(info("Reading baseline file..."))
            baseline_data = _read_baseline_file(baseline_file)

        # Convert based on format choice
        if format_choice == "1":
            convert_bmap_to_csv_2d(profiles, output_file, baseline_data)
        elif format_choice == "2":
            convert_bmap_to_csv_3d(profiles, output_file, baseline_data)
        elif format_choice == "3":
            convert_bmap_to_9column(profiles, output_file, baseline_data)
        else:
            print(error("Invalid format choice."))
            notify_and_wait("", prompt="\nPress Enter to continue...")
            return

        print_success(f"CSV file created: {output_file}")

    except (IOError, OSError, ValueError, AttributeError) as e:
        log_quick_tool_error(
            "convert_bmap", f"Error in BMAP to CSV conversion: {e}", exc=e
        )
        print(error(f"Error: {e}"))

    notify_and_wait("", prompt="\nPress Enter to continue...")


def convert_bmap_to_csv_2d(
    profiles: List, output_file: str, baseline_data: Optional[dict] = None
) -> None:
    """
    Convert BMAP profiles to 2D CSV format (X, Z coordinates).

    Parameters:
        profiles: List of profile objects
        output_file: Path to output CSV file
        baseline_data: Optional baseline transformation data
    """
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(["Profile", "X", "Z"])

            # Write data for each profile
            for profile in profiles:
                if profile is None:
                    continue

                profile_name = getattr(profile, "name", f"Profile_{id(profile)}")

                for i in range(len(profile.x)):
                    x_coord = profile.x[i]
                    z_coord = profile.z[i]

                    # Apply baseline transformation if available
                    if baseline_data:
                        real_coords = _calculate_real_world_coordinates(
                            x_coord, z_coord, baseline_data
                        )
                        x_coord, z_coord = real_coords["x"], real_coords["z"]

                    writer.writerow([profile_name, x_coord, z_coord])

    except (IOError, OSError, ValueError, AttributeError, KeyError) as e:
        log_quick_tool_error(
            "convert_bmap", f"Error converting BMAP to 2D CSV: {e}", exc=e
        )
        raise


def convert_bmap_to_csv_3d(
    profiles: List, output_file: str, baseline_data: Optional[dict] = None
) -> None:
    """
    Convert BMAP profiles to 3D CSV format (X, Y, Z coordinates).

    Parameters:
        profiles: List of profile objects
        output_file: Path to output CSV file
        baseline_data: Optional baseline transformation data
    """
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(["Profile", "X", "Y", "Z"])

            # Write data for each profile
            for profile in profiles:
                if profile is None:
                    continue

                profile_name = getattr(profile, "name", f"Profile_{id(profile)}")

                # Get Y coordinates (default to 0 if not available)
                y_coords = []
                if hasattr(profile, "metadata") and profile.metadata:
                    y_coords = profile.metadata.get("y_coordinates", [])

                for i in range(len(profile.x)):
                    x_coord = profile.x[i]
                    z_coord = profile.z[i]

                    # Get Y coordinate
                    if i < len(y_coords):
                        y_coord = y_coords[i]
                    else:
                        y_coord = 0.0

                    # Apply baseline transformation if available
                    if baseline_data:
                        real_coords = _calculate_real_world_coordinates(
                            x_coord, z_coord, baseline_data
                        )
                        x_coord, z_coord = real_coords["x"], real_coords["z"]

                    writer.writerow([profile_name, x_coord, y_coord, z_coord])

    except (IOError, OSError, ValueError, AttributeError, KeyError) as e:
        log_quick_tool_error(
            "convert_bmap", f"Error converting BMAP to 3D CSV: {e}", exc=e
        )
        raise


def convert_bmap_to_9column(
    profiles: List, output_file: str, baseline_data: Optional[dict] = None
) -> None:
    """
    Convert BMAP profiles to 9-column CSV format with metadata.

    Parameters:
        profiles: List of profile objects
        output_file: Path to output CSV file
        baseline_data: Optional baseline transformation data
    """
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Write header (9 columns)
            writer.writerow(
                [
                    "Profile",
                    "Point_ID",
                    "X",
                    "Y",
                    "Z",
                    "Distance",
                    "Bearing",
                    "Date",
                    "Time",
                ]
            )

            # Write data for each profile
            for profile in profiles:
                if profile is None:
                    continue

                profile_name = getattr(profile, "name", f"Profile_{id(profile)}")

                # Get metadata
                metadata = getattr(profile, "metadata", {}) or {}
                y_coords = metadata.get("y_coordinates", [])
                distances = metadata.get("distances", [])
                bearings = metadata.get("bearings", [])
                dates = metadata.get("dates", [])
                times = metadata.get("times", [])

                for i in range(len(profile.x)):
                    x_coord = profile.x[i]
                    z_coord = profile.z[i]

                    # Get additional data with defaults
                    point_id = i + 1
                    y_coord = y_coords[i] if i < len(y_coords) else 0.0
                    distance = distances[i] if i < len(distances) else ""
                    bearing = bearings[i] if i < len(bearings) else ""
                    date = dates[i] if i < len(dates) else ""
                    time = times[i] if i < len(times) else ""

                    # Apply baseline transformation if available
                    if baseline_data:
                        real_coords = _calculate_real_world_coordinates(
                            x_coord, z_coord, baseline_data
                        )
                        x_coord, z_coord = real_coords["x"], real_coords["z"]

                    writer.writerow(
                        [
                            profile_name,
                            point_id,
                            x_coord,
                            y_coord,
                            z_coord,
                            distance,
                            bearing,
                            date,
                            time,
                        ]
                    )

    except (IOError, OSError, ValueError, AttributeError, KeyError) as e:
        log_quick_tool_error(
            "convert_bmap", f"Error converting BMAP to 9-column CSV: {e}", exc=e
        )
        raise

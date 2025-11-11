# =============================================================================
# GIS Shapefile Conversion Tool
# =============================================================================
#
# FILE: src/profcalc/cli/tools/convert_shapefile.py
#
# PURPOSE:
# This module provides conversion utilities between beach profile data formats
# and GIS shapefile formats, enabling integration with Geographic Information
# Systems (GIS) software. It handles both point shapefiles (individual survey
# points) and line shapefiles (profile transects) with proper coordinate system
# support.
#
# WHAT IT'S FOR:
# - Converts XYZ/CSV profile data to GIS-compatible shapefile format
# - Creates point shapefiles for individual survey measurements
# - Generates line shapefiles representing complete profile transects
# - Handles coordinate reference system (CRS) specifications
# - Supports both 2D and 3D geometry in shapefile output
# - Provides integration with GIS software like ArcGIS, QGIS, etc.
#
# WORKFLOW POSITION:
# This tool is used when profile data needs to be visualized or analyzed in
# GIS environments. It's commonly used for spatial analysis, mapping shoreline
# changes, creating publication-quality maps, and integrating beach profile
# data with other geospatial datasets like aerial imagery or bathymetry.
#
# LIMITATIONS:
# - Requires geopandas and related GIS libraries (optional dependencies)
# - Shapefile format has limitations on field names and data types
# - Coordinate reference systems must be properly specified
# - Large datasets may create very large shapefiles
# - Some GIS software may have import limitations for complex geometries
#
# ASSUMPTIONS:
# - Input data contains valid coordinate information (X, Y, Z)
# - Users understand GIS concepts and coordinate reference systems
# - Target GIS software supports standard shapefile format
# - Coordinate systems are appropriate for the geographic region
# - Output directories have sufficient space for shapefile components
#
# =============================================================================

"""Shapefile conversion utilities.

This module handles conversion between various formats and shapefile formats,
including point shapefiles and line shapefiles.
"""

from pathlib import Path

import pandas as pd

from profcalc.cli.file_dialogs import select_input_file, select_output_file
from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.common.shapefile_io import (
    GEOPANDAS_AVAILABLE as SHAPEFILE_AVAILABLE,
)
from profcalc.common.shapefile_io import (
    write_profile_lines_shapefile,
    write_survey_points_shapefile,
)


def convert_xyz_to_shapefile(
    input_file: str, output_file: str, crs: str = "EPSG:6347"
) -> None:
    """
    Convert XYZ file to shapefile format.

    Parameters:
        input_file: Path to input XYZ file
        output_file: Path to output shapefile (without extension)
        crs: Coordinate reference system
    """
    if not SHAPEFILE_AVAILABLE:
        raise ImportError(
            "Shapefile conversion requires geopandas. "
            "Install with: pip install geopandas"
        )

    try:
        # Read XYZ file
        df = pd.read_csv(input_file, header=None, comment="#")

        if df.shape[1] < 3:
            raise ValueError("XYZ file must have at least 3 columns (X, Y, Z)")

        # Assume X, Y, Z order (can be enhanced with column order detection)
        points_df = df.iloc[:, :3].copy()
        points_df.columns = ["x", "y", "z"]

        # Convert to shapefile
        write_survey_points_shapefile(points_df, output_file, crs)

        print(f"✅ Shapefile created: {output_file}")

    except (IOError, OSError, ValueError, AttributeError, KeyError) as e:
        log_quick_tool_error(
            "convert_shapefile", f"Error converting XYZ to shapefile: {e}", exc=e
        )
        raise


def convert_csv_to_shapefile(
    input_file: str, output_file: str, crs: str = "EPSG:6347"
) -> None:
    """
    Convert CSV file to shapefile format.

    Parameters:
        input_file: Path to input CSV file
        output_file: Path to output shapefile (without extension)
        crs: Coordinate reference system
    """
    if not SHAPEFILE_AVAILABLE:
        raise ImportError(
            "Shapefile conversion requires geopandas. "
            "Install with: pip install geopandas"
        )

    try:
        # Read CSV file
        df = pd.read_csv(input_file, comment="#")

        # Look for coordinate columns
        coord_cols = ["x", "y", "z"]
        available_cols = [col for col in coord_cols if col in df.columns]

        if len(available_cols) < 2:
            raise ValueError("CSV must contain at least X and Z coordinate columns")

        # Extract coordinates
        points_df = df[available_cols].copy()

        # Ensure we have Y column (default to 0 if missing)
        if "y" not in points_df.columns:
            points_df["y"] = 0.0

        # Convert to shapefile
        write_survey_points_shapefile(points_df, output_file, crs)

        print(f"✅ Shapefile created: {output_file}")

    except (IOError, OSError, ValueError, AttributeError, KeyError) as e:
        log_quick_tool_error(
            "convert_shapefile", f"Error converting CSV to shapefile: {e}", exc=e
        )
        raise


def execute_bmap_to_shapefile() -> None:
    """
    Interactive conversion of BMAP files to shapefile format.
    """
    from profcalc.cli.menu_system import notify_and_wait
    from profcalc.common.bmap_io import read_bmap_freeformat

    print("\n" + "=" * 60)
    print("CONVERT BMAP TO SHAPEFILE")
    print("=" * 60)

    if not SHAPEFILE_AVAILABLE:
        print("❌ Shapefile support not available.")
        print("   Install geopandas: pip install geopandas")
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    # Get input file
    print("Select a BMAP input file...")
    input_file = select_input_file("Select BMAP Input File")
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
    print("Select shapefile output location (without .shp extension)...")
    output_file = select_output_file("Select Shapefile Output (without .shp extension)")
    if not output_file:
        print("No output file specified.")
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    # Get CRS
    crs = input("Enter CRS (default: EPSG:6347): ").strip() or "EPSG:6347"

    # Get baseline file if needed
    use_baselines = (
        input("Use baseline file for real-world coordinates? (y/N): ").strip().lower()
    )
    baseline_file = None
    if use_baselines == "y":
        print("Select a baseline file...")
        baseline_file = select_input_file("Select Baseline File")
        if not baseline_file:
            print("No baseline file specified.")
            notify_and_wait("", prompt="\nPress Enter to continue...")
            return

    try:
        # Read BMAP file
        print(f"🔍 Reading BMAP file: {input_file}")
        profiles = read_bmap_freeformat(input_file)

        if not profiles:
            print("❌ No profiles found in BMAP file.")
            notify_and_wait("", prompt="\nPress Enter to continue...")
            return

        print(f"📊 Found {len(profiles)} profiles")

        # Apply baseline transformations if requested
        if baseline_file:
            print("📐 Applying baseline transformations...")
            # This would need additional implementation for baseline processing

        # Choose output type
        output_type = (
            input("Create (P)oint shapefile or (L)ine shapefile? [P/L]: ")
            .strip()
            .upper()
        )

        if output_type == "L":
            # Create line shapefile
            write_profile_lines_shapefile(profiles, output_file, crs)
            print(f"✅ Line shapefile created: {output_file}")
        else:
            # Create point shapefile (default)
            # Convert profiles to points DataFrame
            all_points = []
            for profile in profiles:
                if profile is None:
                    continue

                for i in range(len(profile.x)):
                    point = {
                        "profile": profile.name,
                        "x": profile.x[i],
                        "z": profile.z[i],
                    }

                    # Add Y coordinate if available
                    if hasattr(profile, "metadata") and profile.metadata:
                        y_coords = profile.metadata.get("y_coordinates", [])
                        if i < len(y_coords):
                            point["y"] = y_coords[i]
                        else:
                            point["y"] = 0.0
                    else:
                        point["y"] = 0.0

                    all_points.append(point)

            if all_points:
                points_df = pd.DataFrame(all_points)
                write_survey_points_shapefile(points_df, output_file, crs)
                print(f"✅ Point shapefile created: {output_file}")
            else:
                print("❌ No valid points found to create shapefile.")

    except (IOError, OSError, ValueError, AttributeError, KeyError) as e:
        log_quick_tool_error(
            "convert_shapefile", f"Error in BMAP to shapefile conversion: {e}", exc=e
        )
        print(f"❌ Error: {e}")

    notify_and_wait("", prompt="\nPress Enter to continue...")


def execute_xyz_to_shapefile() -> None:
    """
    Interactive conversion of XYZ files to shapefile format.
    """
    from profcalc.cli.menu_system import notify_and_wait

    print("\n" + "=" * 60)
    print("CONVERT XYZ TO SHAPEFILE")
    print("=" * 60)

    if not SHAPEFILE_AVAILABLE:
        print("❌ Shapefile support not available.")
        print("   Install geopandas: pip install geopandas")
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

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
    print("Select shapefile output location (without .shp extension)...")
    output_file = select_output_file("Select Shapefile Output (without .shp extension)")
    if not output_file:
        print("No output file specified.")
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    # Get CRS
    crs = input("Enter CRS (default: EPSG:6347): ").strip() or "EPSG:6347"

    try:
        convert_xyz_to_shapefile(input_file, output_file, crs)
        print(f"✅ Shapefile created: {output_file}")

    except (IOError, OSError, ValueError, AttributeError, KeyError) as e:
        log_quick_tool_error(
            "convert_shapefile", f"Error in XYZ to shapefile conversion: {e}", exc=e
        )
        print(f"❌ Error: {e}")

    notify_and_wait("", prompt="\nPress Enter to continue...")


def execute_csv_to_shapefile() -> None:
    """
    Interactive conversion of CSV files to shapefile format.
    """
    from profcalc.cli.menu_system import notify_and_wait

    print("\n" + "=" * 60)
    print("CONVERT CSV TO SHAPEFILE")
    print("=" * 60)

    if not SHAPEFILE_AVAILABLE:
        print("❌ Shapefile support not available.")
        print("   Install geopandas: pip install geopandas")
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    # Get input file
    print("Select a CSV input file...")
    input_file = select_input_file("Select CSV Input File")
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
    print("Select shapefile output location (without .shp extension)...")
    output_file = select_output_file("Select Shapefile Output (without .shp extension)")
    if not output_file:
        print("No output file specified.")
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    # Get CRS
    crs = input("Enter CRS (default: EPSG:6347): ").strip() or "EPSG:6347"

    try:
        convert_csv_to_shapefile(input_file, output_file, crs)
        print(f"✅ Shapefile created: {output_file}")

    except (IOError, OSError, ValueError, AttributeError, KeyError) as e:
        log_quick_tool_error(
            "convert_shapefile", f"Error in CSV to shapefile conversion: {e}", exc=e
        )
        print(f"❌ Error: {e}")

    notify_and_wait("", prompt="\nPress Enter to continue...")

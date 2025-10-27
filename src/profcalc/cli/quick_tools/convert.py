"""
Format Converter - Convert between BMAP, CSV, XYZ, and Shapefile formats.

Supports conversions:
- BMAP free format → CSV (2D: X,Z or 3D: X,Y,Z)
- BMAP free format → XYZ (X,Y,Z coordinates)
- BMAP free format → Shapefile (Point or Line features with 3D geometry)
- CSV → BMAP free format
- CSV → Shapefile (Point or Line features with 3D geometry)
- XYZ → BMAP free format
- XYZ → Shapefile (Point or Line features with 3D geometry)

Shapefile exports require:
- geopandas installed: pip install profile-analysis[gis]
- Origin azimuth file with origin_x, origin_y, azimuth for line shapefiles
- Y coordinates in profile metadata for point shapefiles
"""

import argparse
import math
from pathlib import Path
from typing import Literal

import pandas as pd

from profcalc.common.bmap_io import (
    read_bmap_freeformat,
    write_bmap_profiles,
)
from profcalc.common.csv_io import (
    read_csv_profiles,
    write_csv_profiles,
)
from profcalc.common.error_handler import LogComponent, get_logger

# Lazy import for optional shapefile support
try:
    from profcalc.common.shapefile_io import (
        write_profile_lines_shapefile,
        write_survey_points_shapefile,
    )
    SHAPEFILE_AVAILABLE = True
except ImportError:
    SHAPEFILE_AVAILABLE = False

FormatType = Literal["bmap", "csv", "xyz", "shp-points", "shp-lines"]


def _parse_column_order(order_string: str) -> dict[str, int]:
    """
    Parse user-specified column order.

    Parameters:
        order_string: Column order specification
                     Examples: "Y X Z", "1 0 2", "y x z"

    Returns:
        Dictionary mapping 'x', 'y', 'z' to column indices

    Raises:
        ValueError: If order string is invalid

    Example:
        >>> _parse_column_order("Y X Z")
        {'x': 1, 'y': 0, 'z': 2}

        >>> _parse_column_order("1 0 2")
        {'x': 1, 'y': 0, 'z': 2}
    """
    parts = order_string.upper().strip().split()

    if len(parts) != 3:
        raise ValueError(
            f"Column order must specify exactly 3 columns, got {len(parts)}"
        )

    # Check if numeric indices (e.g., "1 0 2")
    if all(part.isdigit() for part in parts):
        indices = [int(p) for p in parts]
        if not all(0 <= i <= 2 for i in indices):
            raise ValueError("Column indices must be 0, 1, or 2")
        if len(set(indices)) != 3:
            raise ValueError("Column order must specify each index exactly once")
        return {"x": indices[0], "y": indices[1], "z": indices[2]}

    # Parse letter order (e.g., "Y X Z")
    valid_letters = {"X", "Y", "Z"}
    if not all(p in valid_letters for p in parts):
        raise ValueError(
            f"Column order must be X/Y/Z letters or 0/1/2 indices. Got: {order_string}"
        )

    if len(set(parts)) != 3:
        raise ValueError("Column order must specify each coordinate exactly once")

    # Map letters to positions
    order_map = {}
    for idx, letter in enumerate(parts):
        order_map[letter.lower()] = idx

    return order_map


def execute_from_cli(args: list[str]) -> None:
    """
    Execute format conversion from command line.

    Args:
        args: Command-line arguments (excluding the -c flag)
    """
    parser = argparse.ArgumentParser(
        prog="profcalc -c",
        description="Convert between BMAP, CSV, XYZ, and Shapefile formats",
    )
    parser.add_argument("input_file", help="Input file to convert")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument(
        "--from",
        dest="from_format",
        choices=["bmap", "csv", "xyz"],
        help="Input format (auto-detected if not specified)",
    )
    parser.add_argument(
        "--to",
        dest="to_format",
        choices=["bmap", "csv", "xyz", "shp-points", "shp-lines"],
        help="Output format (auto-detected from extension if not specified). "
             "shp-points: Point shapefile with survey locations. "
             "shp-lines: Line shapefile with 3D profile geometry.",
    )
    parser.add_argument(
        "--mode",
        choices=["2d", "3d"],
        default="2d",
        help="Coordinate mode: 2d (X,Z) or 3d (X,Y,Z). Default: 2d",
    )
    parser.add_argument(
        "--baselines",
        help="Path to origin azimuth file (required for BMAP→CSV/XYZ conversions with real-world coordinates, "
             "and for shapefile line exports with origin_x, origin_y, azimuth)",
    )
    parser.add_argument(
        "--crs",
        default="EPSG:6347",
        help="Coordinate reference system for shapefile exports. "
             "Default: EPSG:6347 (NAD83(2011) State Plane New Jersey, US Feet). "
             "Other options: EPSG:6348 (Delaware), EPSG:2272 (Pennsylvania), EPSG:2252 (Maryland)",
    )
    parser.add_argument(
        "--columns",
        type=str,
        metavar="ORDER",
        help='Column order override for XYZ files (default: X Y Z). Examples: "Y X Z" or "1 0 2"',
    )

    parsed_args = parser.parse_args(args)

    # Parse column order if provided
    column_order = None
    if parsed_args.columns:
        try:
            column_order = _parse_column_order(parsed_args.columns)
            print(
                f"📐 Using column order: X=col{column_order['x']}, "
                f"Y=col{column_order['y']}, Z=col{column_order['z']}"
            )
        except ValueError as e:
            print(f"❌ Error: {e}")
            return

    # Auto-detect formats if not specified
    from_format = parsed_args.from_format or _detect_format(parsed_args.input_file)
    to_format = parsed_args.to_format or _detect_format(parsed_args.output)

    # Check for shapefile support
    if to_format in ("shp-points", "shp-lines") and not SHAPEFILE_AVAILABLE:
        print("❌ Error: Shapefile export requires geopandas.")
        print("   Install with: pip install profile-analysis[gis]")
        print("   Or: pip install geopandas>=0.14.0")
        return

    print(f"🔄 Converting {from_format.upper()} → {to_format.upper()}...")
    print(f"   Input: {parsed_args.input_file}")
    print(f"   Output: {parsed_args.output}")
    if to_format not in ("shp-points", "shp-lines"):
        print(f"   Mode: {parsed_args.mode.upper()}")
    if to_format in ("shp-points", "shp-lines"):
        print(f"   CRS: {parsed_args.crs}")

    # Perform conversion
    convert_format(
        input_file=parsed_args.input_file,
        output_file=parsed_args.output,
        from_format=from_format,
        to_format=to_format,
        mode=parsed_args.mode,
        baselines_file=parsed_args.baselines,
        column_order=column_order,
        crs=parsed_args.crs,
    )

    print("✅ Conversion complete!")


def convert_format(
    input_file: str,
    output_file: str,
    from_format: FormatType,
    to_format: FormatType,
    mode: str = "2d",
    baselines_file: str | None = None,
    column_order: dict[str, int] | None = None,
    crs: str = "EPSG:6347",
) -> None:
    """
    Convert between profile data formats.

    Args:
        input_file: Path to input file
        output_file: Path to output file
        from_format: Input format (bmap, csv, xyz)
        to_format: Output format (bmap, csv, xyz, shp-points, shp-lines)
        mode: Coordinate mode (2d or 3d)
        baselines_file: Path to origin azimuth file with origin coordinates and azimuths
                       (required for BMAP→CSV/XYZ conversions and shapefile line exports)
        column_order: Optional column order mapping for XYZ files
                     Example: {'x': 1, 'y': 0, 'z': 2} for Y X Z order
        crs: Coordinate reference system for shapefile exports
             Default: EPSG:6347 (NAD83 State Plane New Jersey, US Feet)

    Raises:
        ValueError: If conversion is not supported
        FileNotFoundError: If input file doesn't exist
    """
    # Validate input file exists
    if not Path(input_file).exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Read profiles based on input format
    if from_format == "bmap":
        profiles = read_bmap_freeformat(input_file)

        # If converting to CSV/XYZ, check if we need Y coordinates
        if to_format in ("csv", "xyz") and baselines_file:
            # Load origin azimuth data and calculate real-world coordinates
            baselines = _read_baseline_file(baselines_file)
            profiles = _calculate_real_world_coordinates(profiles, baselines)
        elif to_format in ("csv", "xyz") and not baselines_file:
            # Warn user that Y coordinates will default to 0.0
            print("⚠️  WARNING: No origin azimuth file provided.")
            print("   Y coordinates will default to 0.0 for all points.")
            print("   To calculate real-world Y coordinates from cross-shore distances,")
            print("   provide a origin azimuth file with --baselines <file>")

    elif from_format == "csv":
        profiles = read_csv_profiles(input_file)
    elif from_format == "xyz":
        profiles = _read_xyz_format(input_file, column_order)
    else:
        raise ValueError(f"Unsupported input format: {from_format}")

    if not profiles:
        raise ValueError("No profiles found in input file")

    print(f"   Read {len(profiles)} profile(s) with {sum(len(p.x) for p in profiles)} total points")

    # Check for data loss when converting to BMAP
    if to_format == "bmap":
        _warn_bmap_data_loss(profiles)

    # Write profiles based on output format
    if to_format == "bmap":
        # Pass source filename for date extraction when converting to BMAP
        write_bmap_profiles(profiles, output_file, source_filename=input_file)
    elif to_format == "csv":
        write_csv_profiles(profiles, output_file)
    elif to_format == "xyz":
        _write_xyz_format(profiles, output_file)
    elif to_format == "shp-points":
        # Export point shapefile with actual survey locations
        if not SHAPEFILE_AVAILABLE:
            raise ImportError(
                "Shapefile export requires geopandas. "
                "Install with: pip install profile-analysis[gis]"
            )
        write_survey_points_shapefile(profiles, Path(output_file), crs=crs)
    elif to_format == "shp-lines":
        # Export line shapefile with 3D profile geometry
        if not SHAPEFILE_AVAILABLE:
            raise ImportError(
                "Shapefile export requires geopandas. "
                "Install with: pip install profile-analysis[gis]"
            )
        if not baselines_file:
            raise ValueError(
                "Line shapefile export requires an origin azimuth file with origin_x, origin_y, and azimuth. "
                "Provide with --baselines <file>"
            )
        # Load baseline data and add to profile metadata
        baselines = _read_baseline_file(baselines_file)
        for profile in profiles:
            if profile.name in baselines:
                baseline = baselines[profile.name]
                if profile.metadata is None:
                    profile.metadata = {}
                profile.metadata['origin_x'] = baseline['origin_x']
                profile.metadata['origin_y'] = baseline['origin_y']
                profile.metadata['azimuth'] = baseline['azimuth']
        write_profile_lines_shapefile(profiles, Path(output_file), crs=crs)
    else:
        raise ValueError(f"Unsupported output format: {to_format}")



def _detect_format(file_path: str) -> FormatType:
    """
    Auto-detect file format by inspecting file contents.

    Detection logic:
    - CSV: First line contains commas and looks like headers (profile_id, x, z, etc.)
    - XYZ: Lines with 3+ whitespace-separated numbers, optional # comment headers
    - BMAP: Profile name, then point count, then coordinate pairs

    Args:
        file_path: Path to file

    Returns:
        Detected format (bmap, csv, or xyz)
    """
    try:
        with open(file_path, 'r') as f:
            # Read first few lines for detection
            lines = []
            for _ in range(20):  # Sample first 20 lines
                line = f.readline()
                if not line:
                    break
                lines.append(line.strip())

            if not lines:
                raise ValueError(f"File {file_path} is empty")

            # Check for CSV format
            first_line = lines[0]
            if ',' in first_line:
                # Check if first line looks like CSV headers
                fields = [f.strip().lower() for f in first_line.split(',')]
                csv_indicators = ['profile', 'x', 'y', 'z', 'survey', 'date', 'point']
                if any(indicator in field for field in fields for indicator in csv_indicators):
                    return "csv"

            # Collect non-empty, non-comment lines for analysis
            data_lines = [
                line for line in lines
                if line and not line.startswith('#') and not line.startswith('>')
            ]

            if not data_lines:
                # Only comments found - likely XYZ with headers
                return "xyz"

            # Check for BMAP format pattern:
            # Line 1: Profile name (text, no spaces or single word)
            # Line 2: Point count (integer)
            # Line 3+: Coordinate pairs (two numbers)
            if len(data_lines) >= 3:
                line2_parts = data_lines[1].split()
                line3_parts = data_lines[2].split()

                # BMAP: Line 2 should be a single integer (point count)
                if (len(line2_parts) == 1 and
                    line2_parts[0].isdigit() and
                    len(line3_parts) == 2):
                    # Check if line 3 has two floats (BMAP coordinate pair)
                    try:
                        float(line3_parts[0])
                        float(line3_parts[1])
                        return "bmap"
                    except ValueError:
                        pass

            # Check for XYZ format: Lines with 3 whitespace-separated numbers
            xyz_line_count = 0
            for line in data_lines[:10]:  # Check first 10 data lines
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        float(parts[0])
                        float(parts[1])
                        float(parts[2])
                        xyz_line_count += 1
                    except ValueError:
                        continue

            # If most lines look like XYZ (3 numbers), it's XYZ format
            if xyz_line_count >= len(data_lines) * 0.5:
                return "xyz"

            # Default to BMAP if uncertain
            return "bmap"

    except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError) as e:
        # If detection fails, fall back to extension-based detection
        logger = get_logger(LogComponent.FILE_IO)
        logger.warning(f"Failed to detect format by content analysis for {file_path}, falling back to extension-based detection: {e}")
        ext = Path(file_path).suffix.lower()
        if ext == ".csv":
            return "csv"
        elif ext == ".xyz":
            return "xyz"
        else:
            return "bmap"


def _warn_bmap_data_loss(profiles: list) -> None:
    """
    Warn user about data loss when converting to BMAP format.

    BMAP format only supports 2D coordinates (X, Z), so any Y coordinates
    or extra columns will be lost during conversion.

    Args:
        profiles: List of Profile objects
    """
    fields_to_lose = set()

    for profile in profiles:
        if not profile.metadata:
            continue

        # Check for Y coordinates
        if "y" in profile.metadata or "y_coordinates" in profile.metadata:
            fields_to_lose.add("Y coordinates")

        # Check for extra columns
        if "extra_columns" in profile.metadata:
            extra_info = profile.metadata["extra_columns"]
            if isinstance(extra_info, dict) and "names" in extra_info:
                for col_name in extra_info["names"]:
                    fields_to_lose.add(col_name)

    if fields_to_lose:
        print("\n⚠️  WARNING: Data Loss During BMAP Conversion")
        print("   BMAP format only supports 2D coordinates (X, Z).")
        print("   The following fields will NOT be preserved:")
        for field in sorted(fields_to_lose):
            print(f"      - {field}")
        print()


def _read_baseline_file(baselines_file: str) -> dict[str, dict[str, float]]:
    """
    Read origin azimuth file with origin coordinates and azimuths.

    Expected format (CSV):
    Profile,Origin_X,Origin_Y,Azimuth
    OC117,1234567.89,987654.32,90.5

    Note: Handles comma-formatted numbers (e.g., "1,234,567.89").

    Args:
        baselines_file: Path to baseline CSV file

    Returns:
        Dictionary mapping profile names to baseline data:
        {"OC117": {"origin_x": 1234567.89, "origin_y": 987654.32, "azimuth": 90.5}}

    Raises:
        FileNotFoundError: If origin azimuth file doesn't exist
        ValueError: If origin azimuth file format is invalid
    """
    if not Path(baselines_file).exists():
        raise FileNotFoundError(f"Origin azimuth file not found: {baselines_file}")

    baselines = {}

    try:
        df = pd.read_csv(baselines_file)

        # Check for required columns
        required_cols = ["Profile", "Origin_X", "Origin_Y", "Azimuth"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"Origin azimuth file missing required columns: {', '.join(missing_cols)}"
            )

        for _, row in df.iterrows():
            profile_name = str(row["Profile"]).strip()

            # Parse coordinates (handle comma-formatted numbers)
            origin_x = _parse_coordinate(row["Origin_X"])
            origin_y = _parse_coordinate(row["Origin_Y"])
            azimuth = float(row["Azimuth"])

            baselines[profile_name] = {
                "origin_x": origin_x,
                "origin_y": origin_y,
                "azimuth": azimuth,
            }

        return baselines

    except Exception as e:
        raise ValueError(f"Error reading origin azimuth file: {e}") from e


def _parse_coordinate(value: str | float) -> float:
    """
    Parse coordinate value, handling comma-formatted numbers.

    Args:
        value: Coordinate value (may contain commas)

    Returns:
        Parsed float value
    """
    if isinstance(value, (int, float)):
        return float(value)

    # Remove commas and parse
    return float(str(value).replace(",", ""))


def _calculate_real_world_coordinates(
    profiles: list,
    baselines: dict[str, dict[str, float]],
) -> list:
    """
    Calculate real-world X,Y coordinates from cross-shore distances using baseline data.

    Formula:
        real_x = origin_x + (distance * cos(azimuth_radians))
        real_y = origin_y + (distance * sin(azimuth_radians))

    Args:
        profiles: List of Profile objects with cross-shore distances (X)
        baselines: Dictionary mapping profile names to baseline data

    Returns:
        Updated profiles with Y coordinates in metadata
    """
    import numpy as np

    for profile in profiles:
        # Find baseline data for this profile
        baseline = baselines.get(profile.name)

        if not baseline:
            print(f"⚠️  WARNING: No baseline found for profile '{profile.name}'")
            print("   Y coordinates will default to 0.0")
            # Set Y to zeros
            profile.metadata = profile.metadata or {}
            profile.metadata["y"] = np.zeros_like(profile.x)
            continue

        # Extract baseline parameters
        origin_x = baseline["origin_x"]
        origin_y = baseline["origin_y"]
        azimuth_deg = baseline["azimuth"]

        # Convert azimuth to radians
        azimuth_rad = math.radians(azimuth_deg)

        # Calculate real-world coordinates for each point
        # distance is the cross-shore distance (profile.x)
        real_x = origin_x + (profile.x * math.cos(azimuth_rad))
        real_y = origin_y + (profile.x * math.sin(azimuth_rad))

        # Store Y coordinates in metadata
        profile.metadata = profile.metadata or {}
        profile.metadata["y"] = real_y

        # Update X to real-world coordinates
        profile.x = real_x

    return profiles


def _read_xyz_format(file_path: str, column_order: dict[str, int] | None = None) -> list:
    """
    Read XYZ format (X, Y, Z coordinates with optional extra columns).

    XYZ format expects:
    - One point per line
    - Space or comma separated
    - X Y Z coordinates (required)
    - Optional additional columns (slope, roughness, sediment_type, etc.)
    - Optional profile name in header lines starting with '>' or '#'

    Extra columns beyond X, Y, Z are preserved in metadata['extra_columns'].

    Args:
        file_path: Path to XYZ file
        column_order: Optional column order mapping (default: {'x': 0, 'y': 1, 'z': 2})
                     Example: {'x': 1, 'y': 0, 'z': 2} for Y X Z order

    Returns:
        List of Profile objects

    Raises:
        ValueError: If file has insufficient columns for specified column_order
    """
    # Set default column order if not provided
    if column_order is None:
        column_order = {"x": 0, "y": 1, "z": 2}

    # Determine minimum required columns from column_order
    max_col_index = max(column_order.values())
    min_required_cols = max_col_index + 1

    profiles = []
    current_name = "Unknown"
    current_points: list[tuple] = []
    extra_column_names: list[str] = []
    line_number = 0
    column_count_validated = False

    with open(file_path, "r") as f:
        for line in f:
            line_number += 1
            line = line.strip()
            if not line:
                continue

            # Check for profile name header
            if line.startswith(">") or line.startswith("#"):
                # Save previous profile if exists
                if current_points:
                    profile = _create_profile_from_xyz_points(
                        current_name, current_points, extra_column_names
                    )
                    profiles.append(profile)
                    current_points = []

                # Extract profile name
                name_text = line[1:].strip() or "Unknown"
                # Strip common prefixes like "Profile:" or "Profile "
                if name_text.lower().startswith("profile:"):
                    name_text = name_text[8:].strip()
                elif name_text.lower().startswith("profile "):
                    name_text = name_text[8:].strip()
                current_name = name_text or "Unknown"
                continue

            # Parse coordinate line
            try:
                parts = line.replace(",", " ").split()

                # Validate column count on first data line
                if not column_count_validated:
                    if len(parts) < min_required_cols:
                        raise ValueError(
                            f"❌ Column count validation failed\n"
                            f"   File: {file_path}\n"
                            f"   Line {line_number}: Only {len(parts)} column(s) found, "
                            f"but column order requires {min_required_cols}\n"
                            f"   Column order: X=column {column_order['x']}, "
                            f"Y=column {column_order['y']}, Z=column {column_order['z']}\n"
                            f"   Line content: {line}\n\n"
                            f"   Suggestions:\n"
                            f"   • If file has standard X Y Z order, don't use --columns flag\n"
                            f"   • If file has only 2 columns (X Z), ensure column order doesn't exceed index 1\n"
                            f"   • Check that column indices in --columns match your file structure"
                        )
                    column_count_validated = True

                # Check column count for this specific line (in case it varies)
                if len(parts) < min_required_cols:
                    print(
                        f"⚠️  Warning: Line {line_number} has only {len(parts)} column(s), "
                        f"skipping (need {min_required_cols})"
                    )
                    continue

                # Use column order to extract X, Y, Z from correct positions
                x = float(parts[column_order["x"]])
                y = float(parts[column_order["y"]])
                z = float(parts[column_order["z"]])

                # Remaining columns are extra fields (after the 3 coordinate columns)
                extra_values: list[float | str] = []
                if len(parts) > 3:
                    for val in parts[3:]:
                        try:
                            extra_values.append(float(val))
                        except ValueError:
                            # Non-numeric extra field (e.g., sediment_type)
                            extra_values.append(val)

                current_points.append((x, y, z, extra_values))

            except (ValueError, IndexError) as e:
                # Skip invalid lines but don't re-raise ValueError from column validation
                if "Column count validation failed" in str(e):
                    raise
                continue

    # Save last profile
    if current_points:
        profile = _create_profile_from_xyz_points(
            current_name, current_points, extra_column_names
        )
        profiles.append(profile)

    return profiles


def _create_profile_from_xyz_points(
    name: str,
    points: list[tuple],
    column_names: list[str] | None = None,
) -> object:
    """
    Create a Profile object from XYZ point data.

    Args:
        name: Profile name
        points: List of (x, y, z, extra_values) tuples
        column_names: Names of extra columns (if known)

    Returns:
        Profile object with metadata containing Y coordinates and extra columns
    """
    import numpy as np

    from profcalc.common.bmap_io import Profile

    x_coords = np.array([p[0] for p in points])
    y_coords = np.array([p[1] for p in points])
    z_coords = np.array([p[2] for p in points])

    metadata: dict = {"y": y_coords}

    # Extract extra columns if present
    if points and len(points[0]) > 3 and points[0][3]:
        extra_data = [p[3] for p in points]
        num_extra_cols = len(extra_data[0])

        # Generate column names if not provided
        if not column_names or len(column_names) < num_extra_cols:
            column_names = [f"extra_{i+1}" for i in range(num_extra_cols)]

        metadata["extra_columns"] = {
            "names": column_names[:num_extra_cols],
            "data": extra_data,
        }

    return Profile(
        name=name,
        date=None,
        description=None,
        x=x_coords,
        z=z_coords,
        metadata=metadata,
    )


def _write_xyz_format(profiles: list, output_file: str) -> None:
    """
    Write profiles to XYZ format with optional extra columns.

    Args:
        profiles: List of Profile objects
        output_file: Output file path
    """
    lines = []

    for profile in profiles:
        # Write profile header
        lines.append(f"> {profile.name}")

        # Get Y coordinates from metadata (check both 'y' and 'y_coordinates')
        y_coords = None
        if profile.metadata:
            if "y" in profile.metadata:
                y_coords = profile.metadata["y"]
            elif "y_coordinates" in profile.metadata:
                y_coords = profile.metadata["y_coordinates"]

        # Get extra columns from metadata
        extra_columns = None
        if profile.metadata and "extra_columns" in profile.metadata:
            extra_columns = profile.metadata["extra_columns"]

        # Write coordinates
        for i in range(len(profile.x)):
            x = profile.x[i]
            y = y_coords[i] if y_coords is not None and len(y_coords) > i else 0.0
            z = profile.z[i]

            # Build line with X, Y, Z
            line_parts = [f"{x:.2f}", f"{y:.2f}", f"{z:.2f}"]

            # Add extra columns if present
            if extra_columns and "data" in extra_columns:
                extra_data = extra_columns["data"]
                if i < len(extra_data):
                    for val in extra_data[i]:
                        if isinstance(val, (int, float)):
                            line_parts.append(f"{val:.4f}")
                        else:
                            line_parts.append(str(val))

            lines.append(" ".join(line_parts))

    Path(output_file).write_text("\n".join(lines))


def execute_from_menu() -> None:
    """Execute format conversion from interactive menu."""
    print("\n" + "=" * 60)
    print("FORMAT CONVERTER")
    print("=" * 60)

    # Get user inputs
    input_file = input("Enter input file path: ").strip()
    output_file = input("Enter output file path: ").strip()

    print("\nAvailable formats:")
    print("  1. BMAP free format")
    print("  2. CSV (Comma-Separated Values)")
    print("  3. XYZ (X Y Z coordinates)")

    from_choice = input("\nInput format (1-3) [auto-detect]: ").strip()
    to_choice = input("Output format (1-3) [auto-detect]: ").strip()

    format_map = {"1": "bmap", "2": "csv", "3": "xyz"}
    from_format_str = format_map.get(from_choice) or _detect_format(input_file)
    to_format_str = format_map.get(to_choice) or _detect_format(output_file)

    # Cast to FormatType for type safety
    from_format: FormatType = from_format_str  # type: ignore[assignment]  # String to Literal conversion
    to_format: FormatType = to_format_str  # type: ignore[assignment]  # String to Literal conversion

    mode = "2d"
    if to_format == "csv":
        mode_choice = input("\nCSV mode - 2D (X,Z) or 3D (X,Y,Z)? [2d]: ").strip().lower()
        mode = "3d" if mode_choice == "3d" else "2d"

    try:
        print(f"\n🔄 Converting {from_format.upper()} → {to_format.upper()}...")

        convert_format(
            input_file=input_file,
            output_file=output_file,
            from_format=from_format,
            to_format=to_format,
            mode=mode,
        )

        print("\n✅ Conversion complete!")
        print(f"   Output saved to: {output_file}")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

    input("\nPress Enter to continue...")


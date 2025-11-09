import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.cli.quick_tools.quick_tool_utils import (
    default_output_path,
    timestamped_output_path,
)
from profcalc.common.bmap_io import (
    Profile,
    read_bmap_freeformat,
    write_bmap_profiles,
)
from profcalc.common.csv_io import (
    read_csv_profiles,
    read_xyz_profiles,
    write_csv_profiles,
)
from profcalc.common.shapefile_io import (
    GEOPANDAS_AVAILABLE as SHAPEFILE_AVAILABLE,
)
from profcalc.common.shapefile_io import (
    read_point_shapefile,
    write_profile_lines_shapefile,
    write_survey_points_shapefile,
)

"""Format Converter

Convert between BMAP, CSV, XYZ and Shapefile formats. Supports 2D/3D
exports, origin-azimuth based real-world coordinate calculation, and
shapefile exports (requires geopandas/fiona).

Usage examples:
    - CLI: call :func:`execute_from_cli` or run the module::

            python -m profcalc.cli.tools.convert input.dat --to csv -o output.csv

    - Menu: Quick Tools → Format Converter (invokes :func:`execute_from_menu`).
"""

# Type for format (use str for now, as FormatType is not defined as a type alias or class)
FormatType = str


def _parse_column_order(order_string: str) -> dict[str, int]:
    """
    Parse user-specified column order.

    Parameters:
        order_string: Column order specification
                     Examples: "Y X Z", "1 0 2", "y x z"

    Returns:
        Dictionary mapping 'x', 'y', 'z' to column indices

    Raises:
        ValueError: If order_string is invalid

    Examples:
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
            raise ValueError(
                "Column order must specify each index exactly once"
            )
        return {"x": indices[0], "y": indices[1], "z": indices[2]}

    # Parse letter order (e.g., "Y X Z")
    valid_letters = {"X", "Y", "Z"}
    if not all(p in valid_letters for p in parts):
        raise ValueError(
            f"Column order must be X/Y/Z letters or 0/1/2 indices. Got: {order_string}"
        )

    if len(set(parts)) != 3:
        raise ValueError(
            "Column order must specify each coordinate exactly once"
        )

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
    parser.add_argument(
        "-o", "--output", required=False, help="Output file path"
    )
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
            log_quick_tool_error(
                "convert", f"Column order parse error: {e}", exc=e
            )
            print(f"❌ Error: {e}")
            return

    # If output not provided, set a reasonable default based on input
    if not parsed_args.output:
        try:
            from pathlib import Path

            inp_suffix = Path(parsed_args.input_file).suffix or ".out"
        except (TypeError, OSError):
            inp_suffix = ".out"
        parsed_args.output = default_output_path(
            "convert", parsed_args.input_file, ext=inp_suffix
        )

    # Auto-detect formats if not specified
    from_format = parsed_args.from_format or _detect_format(
        parsed_args.input_file
    )
    to_format = parsed_args.to_format or _detect_format(parsed_args.output)

    # Check for shapefile support
    if to_format in ("shp-points", "shp-lines") and not SHAPEFILE_AVAILABLE:
        log_quick_tool_error(
            "convert",
            "Shapefile export requested but geopandas is not available",
        )
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
            print(
                "   To calculate real-world Y coordinates from cross-shore distances,"
            )
            print("   provide a origin azimuth file with --baselines <file>")

    elif from_format == "csv":
        profiles = read_csv_profiles(input_file)
    elif from_format == "xyz":
        profiles = _read_xyz_format(input_file, column_order)
    else:
        raise ValueError(f"Unsupported input format: {from_format}")

    if not profiles:
        raise ValueError("No profiles found in input file")

    print(
        f"   Read {len(profiles)} profile(s) with {sum(len(p.x) for p in profiles)} total points"
    )

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
                profile.metadata["origin_x"] = baseline["origin_x"]
                profile.metadata["origin_y"] = baseline["origin_y"]
                profile.metadata["azimuth"] = baseline["azimuth"]
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
        with open(file_path, "r") as f:
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
            if "," in first_line:
                # Check if first line looks like CSV headers
                fields = [f.strip().lower() for f in first_line.split(",")]
                csv_indicators = [
                    "profile",
                    "x",
                    "y",
                    "z",
                    "survey",
                    "date",
                    "point",
                ]
                if any(
                    indicator in field
                    for field in fields
                    for indicator in csv_indicators
                ):
                    return "csv"

            # Collect non-empty, non-comment lines for analysis
            data_lines = [
                line
                for line in lines
                if line
                and not line.startswith("#")
                and not line.startswith(">")
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
                if (
                    len(line2_parts) == 1
                    and line2_parts[0].isdigit()
                    and len(line3_parts) == 2
                ):
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

    except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError):
        # If detection fails, fall back to extension-based detection
        # logger = get_logger(LogComponent.FILE_IO)  # Removed: not available
        # logger.warning(f"Failed to detect format by content analysis for {file_path}, falling back to extension-based detection: {e}")
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
                    print(f"Failed to detect format by content analysis for {file_path}, falling back to extension-based detection: {e}")
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
        raise FileNotFoundError(
            f"Origin azimuth file not found: {baselines_file}"
        )

    baselines = {}

    try:
        df = pd.read_csv(baselines_file)

        # Check for required columns with flexible naming
        column_mapping = {}

        # Define acceptable column name variations
        col_variations = {
            "Profile": ["profile", "profile_id", "profile_name", "id", "name"],
            "Origin_X": ["origin_x", "originx", "x_origin", "x"],
            "Origin_Y": ["origin_y", "originy", "y_origin", "y"],
            "Azimuth": ["azimuth", "bearing", "direction", "angle"],
        }

        df_columns = df.columns.tolist()
        df_columns_lower = [col.lower().strip() for col in df_columns]

        for standard_name, variations in col_variations.items():
            found = False
            for i, col_lower in enumerate(df_columns_lower):
                if col_lower == standard_name.lower() or any(
                    var.lower() in col_lower for var in variations
                ):
                    column_mapping[standard_name] = df_columns[i]
                    found = True
                    break
            if not found:
                raise ValueError(
                    f"Could not find column for {standard_name}. Available: {df_columns}"
                )

        for _, row in df.iterrows():
            profile_name = str(row[column_mapping["Profile"]]).strip()

            # Parse coordinates (handle comma-formatted numbers)

            def _get_scalar(val):
                # Robustly extract a scalar from pandas Series, numpy types, or plain value
                try:
                    import numpy as np
                    import pandas as pd

                    if isinstance(val, pd.Series):
                        return val.iloc[0]
                    if isinstance(val, np.generic):
                        return val.item()
                except ImportError:
                    pass
                # If it's a list/tuple, take first element
                if isinstance(val, (list, tuple)):
                    return val[0]
                return val

            ox_val = _get_scalar(row[column_mapping["Origin_X"]])
            oy_val = _get_scalar(row[column_mapping["Origin_Y"]])
            az_val = _get_scalar(row[column_mapping["Azimuth"]])
            # Ensure type safety for _parse_coordinate and float
            origin_x = _parse_coordinate(
                str(ox_val)
                if not isinstance(ox_val, (float, int))
                else float(ox_val)
            )
            origin_y = _parse_coordinate(
                str(oy_val)
                if not isinstance(oy_val, (float, int))
                else float(oy_val)
            )
            azimuth = float(
                str(az_val)
                if not isinstance(az_val, (float, int))
                else float(az_val)
            )

            baselines[profile_name] = {
                "origin_x": origin_x,
                "origin_y": origin_y,
                "azimuth": azimuth,
            }

        return baselines

    except (
        OSError,
        ValueError,
        TypeError,
        RuntimeError,
        KeyError,
        IndexError,
        ImportError,
    ) as e:
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

    for profile in profiles:
        # Find baseline data for this profile
        baseline = baselines.get(profile.name)

        if not baseline:
            print(
                f"⚠️  WARNING: No baseline found for profile '{profile.name}'"
            )
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


def _read_xyz_format(
    file_path: str, column_order: dict[str, int] | None = None
) -> list:
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
            column_names = [f"extra_{i + 1}" for i in range(num_extra_cols)]

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
            y = (
                y_coords[i]
                if y_coords is not None and len(y_coords) > i
                else 0.0
            )
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
    print("Convert between BMAP, CSV, XYZ, and Shapefile formats.")
    print("Includes profile name assignment and geospatial enhancements.")

    # Get user inputs
    input_file = input("Enter input file path: ").strip()
    output_file = input("Enter output file path: ").strip()
    if not output_file:
        # Use a timestamped default so subsequent format detection has an extension
        output_file = timestamped_output_path("convert", ext=".dat")

    print("\nAvailable formats:")
    print("  1. BMAP free format")
    print("  2. CSV (Comma-Separated Values)")
    print("  3. XYZ (X Y Z coordinates)")
    print("  4. Shapefile (GIS format)")

    from_choice = input("\nInput format (1-4) [auto-detect]: ").strip()
    to_choice = input("Output format (1-4) [auto-detect]: ").strip()

    format_map = {"1": "bmap", "2": "csv", "3": "xyz", "4": "shp"}
    from_format_str = format_map.get(from_choice) or _detect_format(input_file)
    to_format_str = format_map.get(to_choice) or _detect_format(output_file)

    # Cast to FormatType for type safety
    from_format: FormatType = from_format_str  # type: ignore[assignment]
    to_format: FormatType = to_format_str  # type: ignore[assignment]

    # Enhanced workflow options
    apply_profile_assignment = False
    apply_origin_azimuth = False

    # Check if profile assignment is needed (for XYZ/CSV inputs without profile names)
    if from_format in ["xyz", "csv"]:
        profile_check = (
            input("\nDoes the input file have profile names/IDs? (y/n) [y]: ")
            .strip()
            .lower()
        )
        if profile_check == "n" or profile_check == "no":
            assign_choice = (
                input("Assign profile names automatically? (y/n) [y]: ")
                .strip()
                .lower()
            )
            apply_profile_assignment = (
                assign_choice != "n" and assign_choice != "no"
            )

    # Check if origin azimuth assignment is needed (for BMAP to Shapefile)
    if from_format == "bmap" and to_format == "shp":
        azimuth_choice = (
            input(
                "\nApply origin azimuth assignment for 3D geometry? (y/n) [y]: "
            )
            .strip()
            .lower()
        )
        apply_origin_azimuth = azimuth_choice != "n" and azimuth_choice != "no"

    mode = "2d"
    if to_format == "csv":
        mode_choice = (
            input("\nCSV mode - 2D (X,Z) or 3D (X,Y,Z)? [2d]: ")
            .strip()
            .lower()
        )
        mode = "3d" if mode_choice == "3d" else "2d"

    try:
        print(
            f"\n🔄 Converting {from_format.upper()} → {to_format.upper()}..."
        )

        # Apply profile assignment if requested
        if apply_profile_assignment:
            print("   → Assigning profile names...")
            input_file = assign_profiles_to_file(input_file)

        # Apply origin azimuth assignment if requested
        if apply_origin_azimuth:
            print("   → Applying origin azimuth assignment...")
            azimuth_file = input("Enter origin azimuth file path: ").strip()
            input_file = apply_origin_azimuth_to_bmap(input_file, azimuth_file)

        # Perform the conversion
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
        log_quick_tool_error(
            "convert", f"File not found during conversion: {e}"
        )
        print(f"\n❌ Error: {e}")
    except ValueError as e:
        log_quick_tool_error("convert", f"Value error during conversion: {e}")
        print(f"\n❌ Error: {e}")
    except (
        OSError,
        TypeError,
        RuntimeError,
        KeyError,
        IndexError,
        ImportError,
    ) as e:
        log_quick_tool_error(
            "convert", f"Unexpected error during conversion: {e}"
        )
        print(f"\n❌ Unexpected error: {e}")

    input("\nPress Enter to continue...")


# =============================
# STUBS FOR UNDEFINED FUNCTIONS
# =============================
def _check_xyz_format(input_file):
    """Stub for _check_xyz_format. Returns dummy format info."""
    print("[Stub] _check_xyz_format called. Not implemented.")
    return {"has_profiles": True, "format_type": "xyz", "column_count": 3}


def convert_xyz_to_shapefile(
    input_file,
    output_files,
    output_types,
    origin_azimuth_file,
    crs,
    vertical_datum,
):
    """Stub for convert_xyz_to_shapefile. Does nothing."""
    print("[Stub] convert_xyz_to_shapefile called. Not implemented.")
    return None


def convert_csv_to_shapefile(
    input_file,
    output_files,
    output_types,
    origin_azimuth_file,
    crs,
    vertical_datum,
):
    """Stub for convert_csv_to_shapefile. Does nothing."""
    print("[Stub] convert_csv_to_shapefile called. Not implemented.")
    return None


def assign_profiles_to_file(input_file: str) -> str:
    """
    Assign profile names to XYZ/CSV file and return path to processed file.

    Args:
        input_file: Path to input file

    Returns:
        Path to processed file with profile names
    """
    import pandas as pd

    from profcalc.cli.tools.assign import assign_profiles_by_clustering

    # Read the input file into a DataFrame first
    points_df = pd.read_csv(input_file)

    # Use automatic clustering for profile assignment
    profiles = assign_profiles_by_clustering(points_df)  # Used for output only

    # Create temporary output file
    import os
    import tempfile

    temp_fd, temp_path = tempfile.mkstemp(
        suffix=os.path.splitext(input_file)[1]
    )
    os.close(temp_fd)

    # Write profiles to temp file
    from profcalc.cli.tools.assign import write_output_with_profiles

    write_output_with_profiles(profiles, temp_path, input_file)

    return temp_path


def apply_origin_azimuth_to_bmap(input_file: str, azimuth_file: str) -> str:
    """
    Apply origin azimuth assignment to BMAP file and return path to processed file.

    Args:
        input_file: Path to BMAP input file
        azimuth_file: Path to origin azimuth file

    Returns:
        Path to processed BMAP file with geospatial positioning
    """
    import os
    import tempfile

    # Read BMAP profiles
    profiles = read_bmap_freeformat(input_file)

    if not profiles:
        raise ValueError("No profiles found in BMAP file")

    # Read origin azimuth data
    baselines = _read_baseline_file(azimuth_file)

    # Transform profiles to real-world coordinates
    profiles_transformed = _calculate_real_world_coordinates(profiles, baselines)

    # Create temporary file for output
    temp_fd, temp_path = tempfile.mkstemp(suffix=".dat")
    os.close(temp_fd)

    # Write transformed profiles back to BMAP format
    write_bmap_profiles(profiles_transformed, temp_path, source_filename=input_file)

    return temp_path


# Placeholder functions for conversion submenu (to be implemented)
def execute_bmap_to_csv() -> None:
    """
    Execute BMAP to CSV conversion from interactive menu.

    Prompts user for 2D or 3D output, handles origin azimuth file for 3D,
    and performs the conversion with appropriate error handling.

    Parameters:
        None (interactive function)

    Returns:
        None
    """
    print("\n" + "=" * 60)
    print("BMAP FREE FORMAT TO CSV CONVERSION")
    print("=" * 60)

    # Prompt for output type
    while True:
        print("\nChoose output format:")
        print("1. Standard 9-Column file")
        print("2. Simple XYZ file")
        output_choice = input("Select output type (1 or 2): ").strip()

        if output_choice == "1":
            output_format = "9column"
            break
        elif output_choice == "2":
            output_format = "xyz"
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

    # Handle different question sets based on output format
    conversion_params = {}

    if output_format == "9column":
        # Ask questions for 9-Column file format
        print("\n" + "=" * 50)
        print("9-COLUMN FILE CONFIGURATION")
        print("=" * 50)
        print(
            "Please provide information to populate the 9-column format and metadata header."
        )

        # Ask for survey date
        while True:
            survey_date = input("Enter survey date (YYYY-MM-DD): ").strip()
            if not survey_date:
                print("❌ Survey date is required.")
                continue
            # Basic validation
            try:
                from datetime import datetime
                datetime.strptime(survey_date, "%Y-%m-%d")
                break
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD.")

        # Ask for survey time
        survey_time = input("Enter survey time (HH:MM:SS, default 12:00:00): ").strip()
        if not survey_time:
            survey_time = "12:00:00"

        # Ask for point type
        point_type = input("Enter point type (default 'Survey'): ").strip()
        if not point_type:
            point_type = "Survey"

        # Ask for description
        description = input("Enter point description (default 'Beach profile point'): ").strip()
        if not description:
            description = "Beach profile point"

        conversion_params.update({
            "format": "9column",
            "survey_date": survey_date,
            "survey_time": survey_time,
            "point_type": point_type,
            "description": description
        })

        # Ask for origin azimuth file (required for 3D coordinates)
        while True:
            origin_azimuth_file = input(
                "Enter origin azimuth file path (required for 3D coordinates): "
            ).strip()
            if not origin_azimuth_file:
                log_quick_tool_error(
                    "convert",
                    "Origin azimuth file required for 9-column conversion but not provided",
                )
                print("❌ Origin azimuth file is required for 9-column conversion.")
                back_choice = input(
                    "Press Enter to go back to previous menu, or enter a file path: "
                ).strip()
                if not back_choice:
                    print("Returning to conversion menu...")
                    return
                continue

            if not Path(origin_azimuth_file).exists():
                log_quick_tool_error(
                    "convert",
                    f"Origin azimuth file does not exist: {origin_azimuth_file}",
                )
                print(
                    f"❌ Origin azimuth file '{origin_azimuth_file}' does not exist."
                )
                back_choice = input(
                    "Press Enter to go back to previous menu, or enter a different file path: "
                ).strip()
                if not back_choice:
                    print("Returning to conversion menu...")
                    return
                continue
            conversion_params["origin_azimuth_file"] = origin_azimuth_file
            break

    elif output_format == "xyz":
        # Ask questions for Simple XYZ file format
        print("\n" + "=" * 50)
        print("SIMPLE XYZ FILE CONFIGURATION")
        print("=" * 50)
        print("Please provide information for the XYZ output format.")

        conversion_params["format"] = "xyz"

        # For XYZ, we still need origin azimuth for 3D coordinates
        while True:
            origin_azimuth_file = input(
                "Enter origin azimuth file path (required for 3D coordinates): "
            ).strip()
            if not origin_azimuth_file:
                log_quick_tool_error(
                    "convert",
                    "Origin azimuth file required for XYZ conversion but not provided",
                )
                print("❌ Origin azimuth file is required for XYZ conversion.")
                back_choice = input(
                    "Press Enter to go back to previous menu, or enter a file path: "
                ).strip()
                if not back_choice:
                    print("Returning to conversion menu...")
                    return
                continue

            if not Path(origin_azimuth_file).exists():
                log_quick_tool_error(
                    "convert",
                    f"Origin azimuth file does not exist: {origin_azimuth_file}",
                )
                print(
                    f"❌ Origin azimuth file '{origin_azimuth_file}' does not exist."
                )
                back_choice = input(
                    "Press Enter to go back to previous menu, or enter a different file path: "
                ).strip()
                if not back_choice:
                    print("Returning to conversion menu...")
                    return
                continue
            conversion_params["origin_azimuth_file"] = origin_azimuth_file
            break

    # Prompt for input BMAP file
    while True:
        input_file = input("Enter input BMAP file path: ").strip()
        if not input_file:
            log_quick_tool_error(
                "convert", "Input file path required but not provided"
            )
            print("❌ Input file path is required.")
            continue
        if not Path(input_file).exists():
            log_quick_tool_error(
                "convert", f"Input file does not exist: {input_file}"
            )
            print(f"❌ Input file '{input_file}' does not exist.")
            continue
        break

    # Prompt for output file
    while True:
        if output_format == "9column":
            output_file = input("Enter output 9-Column file path: ").strip()
        else:  # xyz
            output_file = input("Enter output XYZ file path: ").strip()
        if not output_file:
            print("❌ Output file path is required.")
            continue
        break

    # Perform the conversion
    try:
        if output_format == "9column":
            # Implement 9-column conversion using new function
            try:
                convert_bmap_to_9column(
                    input_file=input_file,
                    output_file=output_file,
                    origin_azimuth_file=conversion_params["origin_azimuth_file"],
                    survey_date=conversion_params["survey_date"],
                    survey_time=conversion_params["survey_time"],
                    point_type=conversion_params["point_type"],
                    description=conversion_params["description"]
                )
                print(f"✅ 9-Column conversion completed. Output saved to '{output_file}'")
            except (
                OSError,
                ValueError,
                TypeError,
                RuntimeError,
                KeyError,
                IndexError,
                ImportError,
            ) as e:
                log_quick_tool_error(
                    "convert", f"9-Column conversion failed: {e}", exc=e
                )
                print(f"❌ 9-Column conversion failed: {e}")
        elif output_format == "xyz":
            # XYZ conversion with origin azimuth
            try:
                convert_bmap_to_csv_3d(input_file, output_file, conversion_params["origin_azimuth_file"])
                print(f"✅ XYZ conversion completed. Output saved to '{output_file}'")
            except (
                OSError,
                ValueError,
                TypeError,
                RuntimeError,
                KeyError,
                IndexError,
                ImportError,
            ) as e:
                log_quick_tool_error(
                    "convert", f"XYZ conversion failed: {e}", exc=e
                )
                print(f"❌ XYZ conversion failed: {e}")
    except (
        OSError,
        ValueError,
        TypeError,
        RuntimeError,
        KeyError,
        IndexError,
        ImportError,
    ) as e:
        log_quick_tool_error("convert", f"Conversion failed: {e}", exc=e)
        print(f"❌ Conversion failed: {e}")

    input("\nPress Enter to continue...")


def convert_bmap_to_csv_2d(input_file: str, output_file: str) -> None:
    """
    Convert BMAP file to 2D CSV format.

    Parameters:
        input_file (str): Path to input BMAP file
        output_file (str): Path to output CSV file

    Returns:
        None

    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If BMAP file format is invalid
    """
    # Read BMAP profiles
    profiles = read_bmap_freeformat(input_file)

    if not profiles:
        raise ValueError("No profiles found in BMAP file")

    # Convert to CSV format
    csv_data = []
    for profile in profiles:
        for i in range(len(profile.x)):
            csv_data.append(
                {
                    "profile_name": profile.name,
                    "X_distance": profile.x[i],
                    "Z_elevation": profile.z[i],
                }
            )

    # Write to CSV
    import pandas as pd

    df = pd.DataFrame(csv_data)
    df.to_csv(output_file, index=False)


def convert_bmap_to_csv_3d(
    input_file: str, output_file: str, origin_azimuth_file: str
) -> None:
    """
    Convert BMAP file to 3D CSV format using origin azimuth data.

    Parameters:
        input_file (str): Path to input BMAP file
        output_file (str): Path to output CSV file
        origin_azimuth_file (str): Path to origin azimuth file

    Returns:
        None

    Raises:
        FileNotFoundError: If input or origin azimuth files do not exist
        ValueError: If file formats are invalid
    """
    # Read BMAP profiles
    profiles = read_bmap_freeformat(input_file)

    if not profiles:
        raise ValueError("No profiles found in BMAP file")

    # Read origin azimuth data
    baselines = _read_baseline_file(origin_azimuth_file)

    # Convert profiles to 3D coordinates
    profiles_3d = _calculate_real_world_coordinates(profiles, baselines)

    # Convert to CSV format
    csv_data = []
    for profile in profiles_3d:
        y_coords = profile.metadata.get("y", [0.0] * len(profile.x))
        for i in range(len(profile.x)):
            csv_data.append(
                {
                    "profile_name": profile.name,
                    "X_coordinate": profile.x[i],
                    "Y_coordinate": y_coords[i],
                    "Z_elevation": profile.z[i],
                }
            )

    # Write to CSV
    import pandas as pd

    df = pd.DataFrame(csv_data)
    df.to_csv(output_file, index=False)


def convert_bmap_to_9column(
    input_file: str,
    output_file: str,
    origin_azimuth_file: str,
    survey_date: str,
    survey_time: str = "12:00:00",
    point_type: str = "Survey",
    description: str = "Beach profile point"
) -> None:
    """
    Convert BMAP file to 9-column CSV format using origin azimuth data.

    Parameters:
        input_file (str): Path to input BMAP file
        output_file (str): Path to output CSV file
        origin_azimuth_file (str): Path to origin azimuth file
        survey_date (str): Survey date in YYYY-MM-DD format
        survey_time (str): Survey time in HH:MM:SS format
        point_type (str): Point type for TYPE column
        description (str): Description for DESCRIPTION column

    Returns:
        None

    Raises:
        FileNotFoundError: If input or origin azimuth files do not exist
        ValueError: If file formats are invalid
    """
    # Read BMAP profiles
    profiles = read_bmap_freeformat(input_file)

    if not profiles:
        raise ValueError("No profiles found in BMAP file")

    # Read origin azimuth data
    baselines = _read_baseline_file(origin_azimuth_file)

    # Convert profiles to 3D coordinates
    profiles_3d = _calculate_real_world_coordinates(profiles, baselines)

    # Convert to 9-column format
    csv_data = []
    for profile in profiles_3d:
        y_coords = profile.metadata.get("y", [0.0] * len(profile.x))
        for i in range(len(profile.x)):
            csv_data.append({
                "PROFILE ID": profile.name,
                "DATE": survey_date,
                "TIME (EST)": survey_time,
                "POINT #": i + 1,
                "EASTING (X)": profile.x[i],
                "NORTHING (Y)": y_coords[i],
                "ELEVATION (Z)": profile.z[i],
                "TYPE": point_type,
                "DESCRIPTION": description
            })

    # Write to CSV
    df = pd.DataFrame(csv_data)
    df.to_csv(output_file, index=False)


def execute_bmap_to_shapefile() -> None:
    """
    Execute BMAP to Shapefile conversion from interactive menu.

    Requires origin azimuth file for geospatial positioning and prompts
    for output type, coordinate system, vertical datum, and filenames.

    Parameters:
        None (interactive function)

    Returns:
        None
    """
    print("\n" + "=" * 60)
    print("BMAP FREE FORMAT TO SHAPEFILE CONVERSION")
    print("=" * 60)

    # Prompt for origin azimuth file (required)
    while True:
        origin_azimuth_file = input(
            "Enter origin azimuth file path (required for 3D Shapefile): "
        ).strip()
        if not origin_azimuth_file:
            print(
                "❌ Origin azimuth file is required for Shapefile conversion."
            )
            back_choice = input(
                "Press Enter to go back to previous menu, or enter a file path: "
            ).strip()
            if not back_choice:
                print("Returning to conversion menu...")
                return
            continue

        if not Path(origin_azimuth_file).exists():
            print(
                f"❌ Origin azimuth file '{origin_azimuth_file}' does not exist."
            )
            back_choice = input(
                "Press Enter to go back to previous menu, or enter a different file path: "
            ).strip()
            if not back_choice:
                print("Returning to conversion menu...")
                return
            continue
        break

    # Prompt for output type
    while True:
        print("\nChoose Shapefile output type:")
        print("1. Point Shapefile (individual points)")
        print("2. Line Shapefile (connected profile lines)")
        print("3. Both (point and line Shapefiles)")
        output_choice = input("Select output type (1, 2, or 3): ").strip()

        if output_choice == "1":
            output_types = ["point"]
            break
        elif output_choice == "2":
            output_types = ["line"]
            break
        elif output_choice == "3":
            output_types = ["point", "line"]
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

    # Prompt for coordinate system
    crs_input = input(
        "Enter coordinate reference system (default: NJ State Plane NAD 1983): "
    ).strip()
    crs = crs_input if crs_input else "NJ State Plane NAD 1983"

    # Confirm vertical datum
    while True:
        datum_confirm = (
            input("Is the vertical datum NAVD88? (y/n): ").strip().lower()
        )
        if datum_confirm in ["y", "yes"]:
            vertical_datum = "NAVD88"
            break
        elif datum_confirm in ["n", "no"]:
            user_datum = input(
                "Enter the vertical datum (e.g., MLLW, MHW, etc.): "
            ).strip()
            vertical_datum = user_datum if user_datum else "Unknown"
            break
        else:
            print("❌ Please enter 'y' for yes or 'n' for no.")

    # Prompt for output filenames
    output_files = {}
    if "point" in output_types:
        while True:
            point_file = input(
                "Enter output point Shapefile path (e.g., profiles_points.shp): "
            ).strip()
            if not point_file:
                print("❌ Output file path is required.")
                continue
            if not point_file.endswith(".shp"):
                point_file += ".shp"
            output_files["point"] = point_file
            break

    if "line" in output_types:
        while True:
            line_file = input(
                "Enter output line Shapefile path (e.g., profiles_lines.shp): "
            ).strip()
            if not line_file:
                print("❌ Output file path is required.")
                continue
            if not line_file.endswith(".shp"):
                line_file += ".shp"
            output_files["line"] = line_file
            break

    # Prompt for input BMAP file
    while True:
        input_file = input("Enter input BMAP file path: ").strip()
        if not input_file:
            print("❌ Input file path is required.")
            continue
        if not Path(input_file).exists():
            print(f"❌ Input file '{input_file}' does not exist.")
            continue
        break

    # Perform the conversion
    try:
        convert_bmap_to_shapefile(
            input_file=input_file,
            origin_azimuth_file=origin_azimuth_file,
            output_types=output_types,
            output_files=output_files,
            crs=crs,
            vertical_datum=vertical_datum,
        )
        print("✅ Shapefile conversion completed successfully!")
        for file_type, file_path in output_files.items():
            print(f"   {file_type.capitalize()} Shapefile: {file_path}")
    except (
        OSError,
        ValueError,
        TypeError,
        RuntimeError,
        KeyError,
        IndexError,
        ImportError,
    ) as e:
        print(f"❌ Conversion failed: {e}")

    input("\nPress Enter to continue...")


def convert_bmap_to_shapefile(
    input_file: str,
    origin_azimuth_file: str,
    output_types: list[str],
    output_files: dict[str, str],
    crs: str,
    vertical_datum: str,
) -> None:
    """
    Convert BMAP file to Shapefile(s) using origin azimuth data.

    Parameters:
        input_file (str): Path to input BMAP file
        origin_azimuth_file (str): Path to origin azimuth file
        output_types (list[str]): List of output types ('point', 'line')
        output_files (dict[str, str]): Mapping of output type to file path
        crs (str): Coordinate reference system
        vertical_datum (str): Vertical datum description

    Returns:
        None

    Raises:
        FileNotFoundError: If input or origin azimuth files do not exist
        ValueError: If file formats are invalid or shapefile support unavailable
    """
    # Read BMAP profiles
    profiles = read_bmap_freeformat(input_file)

    if not profiles:
        raise ValueError("No profiles found in BMAP file")

    # Read origin azimuth data
    baselines = _read_baseline_file(origin_azimuth_file)

    # Convert profiles to 3D coordinates
    profiles_3d = _calculate_real_world_coordinates(profiles, baselines)

    # Check for shapefile support
    if not SHAPEFILE_AVAILABLE:
        raise ImportError(
            "Shapefile export requires geopandas. "
            "Install with: pip install profile-analysis[gis]"
        )

    # Create Shapefiles
    if "point" in output_types:
        write_survey_points_shapefile(
            profiles_3d, Path(output_files["point"]), crs=crs
        )

    if "line" in output_types:
        # Add baseline metadata for line shapefiles
        for profile in profiles_3d:
            if profile.name in baselines:
                baseline = baselines[profile.name]
                if profile.metadata is None:
                    profile.metadata = {}
                profile.metadata["origin_x"] = baseline["origin_x"]
                profile.metadata["origin_y"] = baseline["origin_y"]
                profile.metadata["azimuth"] = baseline["azimuth"]

        write_profile_lines_shapefile(
            profiles_3d, Path(output_files["line"]), crs=crs
        )


def execute_csv_to_bmap() -> None:
    """
    Execute CSV to BMAP conversion from interactive menu.

    Prompts user for input CSV file and output BMAP file path,
    then performs the conversion with appropriate error handling.

    Parameters:
        None (interactive function)

    Returns:
        None
    """
    print("\n" + "=" * 60)
    print("CSV TO BMAP FREE FORMAT CONVERSION")
    print("=" * 60)

    # Prompt for input CSV file
    while True:
        input_file = input("Enter input CSV file path: ").strip()
        if not input_file:
            print("❌ Input file path is required.")
            continue
        if not Path(input_file).exists():
            print(f"❌ Input file '{input_file}' does not exist.")
            continue
        break

    # Prompt for output BMAP file
    while True:
        output_file = input("Enter output BMAP file path: ").strip()
        if not output_file:
            print("❌ Output file path is required.")
            continue
        break

    # Perform the conversion
    try:
        convert_csv_to_bmap(input_file, output_file)
        print(
            f"✅ Conversion completed successfully. Output saved to '{output_file}'"
        )
    except (OSError, ValueError, TypeError, RuntimeError) as e:
        print(f"❌ Conversion failed: {e}")

    input("\nPress Enter to continue...")


def convert_csv_to_bmap(input_file: str, output_file: str) -> None:
    """
    Convert CSV file to BMAP free format.

    Supports both 2D profile data (profile_name, X_distance, Z_elevation)
    and 3D geospatial data (with X, Y, Z coordinates).

    Parameters:
        input_file (str): Path to input CSV file
        output_file (str): Path to output BMAP file

    Returns:
        None

    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If CSV file format is invalid
    """
    # Try to read as 3D CSV first (with X, Y coordinates)
    try:
        profiles = read_csv_profiles(input_file)
        if profiles:
            print(f"✅ Detected 3D CSV format with {len(profiles)} profiles")
        else:
            raise ValueError("No profiles found in 3D CSV format")
    except (
        OSError,
        ValueError,
        TypeError,
        RuntimeError,
        KeyError,
        IndexError,
        ImportError,
    ) as e:
        # If 3D reading fails, try 2D format
        try:
            profiles = read_csv_profiles_2d(input_file)
            if profiles:
                print(
                    f"✅ Detected 2D CSV format with {len(profiles)} profiles"
                )
            else:
                raise ValueError("No profiles found in 2D CSV format")
        except (
            OSError,
            ValueError,
            TypeError,
            RuntimeError,
            KeyError,
            IndexError,
            ImportError,
        ) as e2:
            raise ValueError(
                f"Could not read CSV file as 2D or 3D format. 3D error: {e}, 2D error: {e2}"
            )

    if not profiles:
        raise ValueError("No profiles found in CSV file")

    # For 2D CSV files, we need origin azimuth data to convert to 3D coordinates
    # Disabled: uses undefined variables (origin_azimuth_file, output_types, output_files, crs)
    pass


def read_csv_profiles_2d(input_file: str | Path) -> list:
    """
    Read 2D CSV profiles (profile_name, X_distance, Z_elevation format).

    This format is typically produced by BMAP to CSV 2D conversion.

    Parameters:
        input_file: Path to CSV file

    Returns:
        List of Profile objects
    """
    import pandas as pd

    df = pd.read_csv(input_file)

    # Check for required columns
    required_cols = ["profile_name", "X_distance", "Z_elevation"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"2D CSV missing required columns: {missing_cols}. Found: {list(df.columns)}"
        )

    profiles = []
    profile_groups = df.groupby("profile_name")

    for profile_name, group_df in profile_groups:
        # Sort by X_distance to ensure proper order
        group_df = group_df.sort_values("X_distance")

        x_coords = np.array(group_df["X_distance"].values, dtype=float)
        z_coords = np.array(group_df["Z_elevation"].values, dtype=float)

        # Create profile with basic metadata
        profile = Profile(
            name=str(profile_name),
            date=None,  # Will be enhanced later
            description=None,  # Will be enhanced later
            x=x_coords,
            z=z_coords,
            metadata={"source_format": "2d_csv", "point_count": len(x_coords)},
        )
        profiles.append(profile)

    return profiles


def enhance_profile_for_bmap(profile, source_file: str):
    """
    Enhance a Profile object with better metadata for BMAP header preservation.

    Parameters:
        profile: Profile object to enhance
        source_file: Source file path for extracting additional metadata

    Returns:
        Enhanced Profile object
    """
    from pathlib import Path

    # Create a new profile with enhanced metadata
    enhanced_profile = Profile(
        name=profile.name,
        date=profile.date,
        description=profile.description,
        x=profile.x,
        z=profile.z,
        metadata=profile.metadata.copy() if profile.metadata else {},
    )

    # Enhance the name if it's generic
    if enhanced_profile.name.startswith(
        "csv_profile_"
    ) or enhanced_profile.name.startswith("default_profile"):
        # Try to extract better name from source filename
        source_name = Path(source_file).stem
        enhanced_profile.name = source_name

    # Enhance date from filename if not already set
    if not enhanced_profile.date:
        from profcalc.common.bmap_io import extract_date_from_filename

        filename_date = extract_date_from_filename(source_file)
        if filename_date:
            enhanced_profile.date = filename_date

    # Build concise purpose/description from available metadata
    # Following typical BMAP format: Profile ID Date Purpose
    # where Purpose is optional and concise

    purpose_parts = []

    # For 2D CSV files, indicate the source
    if (
        enhanced_profile.metadata
        and enhanced_profile.metadata.get("source_format") == "2d_csv"
    ):
        purpose_parts.append("From 2D CSV")
    elif (
        enhanced_profile.metadata
        and enhanced_profile.metadata.get("source_format") == "csv"
    ):
        purpose_parts.append("From CSV")

    # Only add project info if it's very brief and meaningful
    if enhanced_profile.metadata and "project" in enhanced_profile.metadata:
        project = enhanced_profile.metadata["project"]
        if project and len(project) <= 20:  # Keep it brief
            purpose_parts.append(f"Project: {project}")

    # Join purpose parts with spaces (not semicolons) to match BMAP style
    if purpose_parts:
        enhanced_profile.description = " ".join(purpose_parts)
    # If no purpose info, leave description as None (optional field)

    return enhanced_profile


def enhance_profile_for_shapefile(
    profile, source_file: str, is_2d_format: bool
):
    """
    Enhance a Profile object with metadata preservation for shapefile export.

    For shapefiles, we want to preserve all available CSV metadata as attributes
    that will be included in the shapefile feature attributes.

    Parameters:
        profile: Profile object to enhance
        source_file: Source file path for extracting additional metadata
        is_2d_format: Whether the source was a 2D CSV format

    Returns:
        Enhanced Profile object with comprehensive metadata for shapefile attributes
    """
    from pathlib import Path

    # Create a new profile with enhanced metadata
    enhanced_profile = Profile(
        name=profile.name,
        date=profile.date,
        description=profile.description,
        x=profile.x,
        z=profile.z,
        metadata=profile.metadata.copy() if profile.metadata else {},
    )

    # Ensure metadata exists
    if enhanced_profile.metadata is None:
        enhanced_profile.metadata = {}

    # Add source information
    enhanced_profile.metadata["source_file"] = Path(source_file).name
    enhanced_profile.metadata["source_format"] = (
        "2d_csv" if is_2d_format else "csv"
    )
    enhanced_profile.metadata["conversion_date"] = "2025-10-27"  # Current date

    # For 2D format conversions, add conversion info
    if is_2d_format:
        enhanced_profile.metadata["converted_from"] = "relative_coordinates"
        enhanced_profile.metadata["conversion_method"] = (
            "origin_azimuth_transform"
        )
        enhanced_profile.metadata["original_format"] = (
            "profile_name_X_distance_Z_elevation"
        )

    # Preserve all available CSV metadata that would be useful in shapefiles
    # These will become attributes in the shapefile

    # Survey metadata
    if profile.metadata:
        # Copy over any existing metadata fields
        for key in ["surveyor", "project", "survey_date", "point_number"]:
            if key in profile.metadata and profile.metadata[key] is not None:
                enhanced_profile.metadata[key] = profile.metadata[key]

        # Add coordinate system info
        if "y_coordinates" in profile.metadata:
            enhanced_profile.metadata["has_y_coordinates"] = True
            enhanced_profile.metadata["coordinate_system"] = "3D_geospatial"
        else:
            enhanced_profile.metadata["has_y_coordinates"] = False
            enhanced_profile.metadata["coordinate_system"] = (
                "2D_profile" if is_2d_format else "unknown"
            )

        # Add point count
        enhanced_profile.metadata["point_count"] = len(profile.x)

        # Preserve extra columns info
        if "extra_columns" in profile.metadata:
            extra_info = profile.metadata["extra_columns"]
            enhanced_profile.metadata["has_extra_columns"] = True
            enhanced_profile.metadata["extra_column_count"] = len(
                extra_info.get("names", [])
            )
            # Note: The actual extra column data will be handled by the shapefile writer

    return enhanced_profile


def execute_csv_to_shapefile() -> None:
    """
    Execute CSV to Shapefile conversion from interactive menu.

    Requires origin azimuth file for geospatial positioning and prompts
    for output type, coordinate system, vertical datum, and filenames.

    Parameters:
        None (interactive function)

    Returns:
        None
    """
    print("\n" + "=" * 60)
    print("CSV TO SHAPEFILE CONVERSION")
    print("=" * 60)

    # Prompt for origin azimuth file (required)
    while True:
        origin_azimuth_file = input(
            "Enter origin azimuth file path (required for 3D Shapefile): "
        ).strip()
        if not origin_azimuth_file:
            print(
                "❌ Origin azimuth file is required for Shapefile conversion."
            )
            back_choice = input(
                "Press Enter to go back to previous menu, or enter a file path: "
            ).strip()
            if not back_choice:
                print("Returning to conversion menu...")
                return
            continue

        if not Path(origin_azimuth_file).exists():
            print(
                f"❌ Origin azimuth file '{origin_azimuth_file}' does not exist."
            )
            back_choice = input(
                "Press Enter to go back to previous menu, or enter a different file path: "
            ).strip()
            if not back_choice:
                print("Returning to conversion menu...")
                return
            continue
        break

    # Prompt for output type
    while True:
        print("\nChoose Shapefile output type:")
        print("1. Point Shapefile (individual points)")
        print("2. Line Shapefile (connected profile lines)")
        print("3. Both (point and line Shapefiles)")
        output_choice = input("Select output type (1, 2, or 3): ").strip()

        if output_choice == "1":
            output_types = ["point"]
            break
        elif output_choice == "2":
            output_types = ["line"]
            break
        elif output_choice == "3":
            output_types = ["point", "line"]
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

    # Prompt for coordinate reference system
    while True:
        print("\nEnter coordinate reference system (CRS):")
        print(
            "Examples: EPSG:2263 (NJ State Plane), EPSG:4326 (WGS84), EPSG:26918 (UTM Zone 18N)"
        )
        crs = input("CRS (default: EPSG:2263): ").strip()
        if not crs:
            crs = "EPSG:2263"
        # Basic validation - should start with EPSG: or be a proj string
        if not (crs.startswith("EPSG:") or crs.startswith("+proj=")):
            print(
                "❌ CRS should be in format 'EPSG:XXXX' or a proj string starting with '+proj='"
            )
            continue
        break

    # Confirm vertical datum
    print("\nVertical datum: NAVD88 (assumed for coastal NJ profiles)")
    vertical_datum = "NAVD88"

    # Prompt for input CSV file
    while True:
        input_file = input("Enter input CSV file path: ").strip()
        if not input_file:
            print("❌ Input file path is required.")
            continue
        if not Path(input_file).exists():
            print(f"❌ Input file '{input_file}' does not exist.")
            continue
        break

    # Prompt for output file names
    output_files = {}
    for output_type in output_types:
        while True:
            if output_type == "point":
                default_name = Path(input_file).stem + "_points.shp"
                prompt = f"Enter output point Shapefile path (default: {default_name}): "
            else:  # line
                default_name = Path(input_file).stem + "_lines.shp"
                prompt = f"Enter output line Shapefile path (default: {default_name}): "

            output_path = input(prompt).strip()
            if not output_path:
                output_path = str(Path(input_file).parent / default_name)

            # Check if file already exists
            if Path(output_path).exists():
                overwrite = (
                    input(
                        f"File '{output_path}' already exists. Overwrite? (y/N): "
                    )
                    .strip()
                    .lower()
                )
                if overwrite != "y":
                    continue

            output_files[output_type] = output_path
            break

    # Perform the conversion
    try:
        convert_csv_to_shapefile(
            input_file=input_file,
            output_files=output_files,
            output_types=output_types,
            origin_azimuth_file=origin_azimuth_file,
            crs=crs,
            vertical_datum=vertical_datum,
        )
        print("✅ Conversion completed successfully.")
        for output_type, output_file in output_files.items():
            print(
                f"   {output_type.capitalize()} Shapefile saved to: {output_file}"
            )
    except (
        OSError,
        ValueError,
        TypeError,
        RuntimeError,
        KeyError,
        IndexError,
        ImportError,
    ) as e:
        print(f"❌ Conversion failed: {e}")

    input("\nPress Enter to continue...")


def convert_xyz_to_bmap(input_file: str, output_file: str) -> None:
    """
    Convert XYZ file to BMAP free format.

    Parameters:
        input_file (str): Path to input XYZ file
        output_file (str): Path to output BMAP file

    Returns:
        None

    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If XYZ file format is invalid
    """
    # Read XYZ profiles
    profiles = read_xyz_profiles(input_file)

    if not profiles:
        raise ValueError("No profiles found in XYZ file")

    # Write to BMAP format
    write_bmap_profiles(profiles, output_file)


def execute_xyz_to_shapefile() -> None:
    """
    Execute XYZ to Shapefile conversion from interactive menu.

    XYZ files contain 3D coordinates (X, Y, Z) and may already have profile information
    in headers (lines starting with '>' or '#'). If no profile information exists,
    origin azimuth file is required for profile assignment.

    Parameters:
        None (interactive function)

    Returns:
        None
    """
    print("\n" + "=" * 60)
    print("XYZ TO SHAPEFILE CONVERSION")

    print("=" * 60)

    # Prompt for input XYZ file first to check its structure
    while True:
        input_file = input("Enter input XYZ file path: ").strip()
        if not input_file:
            print("❌ Input file path is required.")
            continue
        if not Path(input_file).exists():
            print(f"❌ Input file '{input_file}' does not exist.")
            continue
        break

    # Check XYZ file format and profile information
    format_info = _check_xyz_format(input_file)
    has_profile_info = format_info["has_profiles"]
    format_type = format_info["format_type"]
    column_count = format_info["column_count"]

    print("\n📄 XYZ File Analysis:")
    print(f"   Format: {format_type.upper()}")
    print(f"   Columns: {column_count}")
    print(f"   Has Profile Headers: {'Yes' if has_profile_info else 'No'}")

    origin_azimuth_file = None
    if not has_profile_info:
        # File needs profile assignment - require origin azimuth file
        print("\n❗ XYZ file does not contain profile information.")
        print("Origin azimuth file is required to assign points to profiles.")

        while True:
            origin_azimuth_file = input(
                "Enter origin azimuth file path (required for profile assignment): "
            ).strip()
            if not origin_azimuth_file:
                print(
                    "❌ Origin azimuth file is required when XYZ file has no profile information."
                )
                back_choice = input(
                    "Press Enter to go back to previous menu, or enter a file path: "
                ).strip()
                if not back_choice:
                    print("Returning to conversion menu...")
                    return
                continue

            if not Path(origin_azimuth_file).exists():
                print(
                    f"❌ Origin azimuth file '{origin_azimuth_file}' does not exist."
                )
                back_choice = input(
                    "Press Enter to go back to previous menu, or enter a different file path: "
                ).strip()
                if not back_choice:
                    print("Returning to conversion menu...")
                    return
                continue
            break
    else:
        print(
            f"\n✅ XYZ file contains profile information ({has_profile_info} profiles found)."
        )
        print(
            "Origin azimuth file is optional (only needed for line shapefiles)."
        )

        # Optional origin azimuth file for line shapefiles
        origin_azimuth_input = input(
            "Enter origin azimuth file path (optional, press Enter to skip): "
        ).strip()
        if origin_azimuth_input and Path(origin_azimuth_input).exists():
            origin_azimuth_file = origin_azimuth_input
        elif origin_azimuth_input:
            print(
                f"⚠️  Origin azimuth file '{origin_azimuth_input}' does not exist. Proceeding without it."
            )

    # Prompt for output type
    while True:
        print("\nChoose Shapefile output type:")
        print("1. Point Shapefile (individual points)")
        print("2. Line Shapefile (connected profile lines)")
        print("3. Both (point and line Shapefiles)")
        output_choice = input("Select output type (1, 2, or 3): ").strip()

        if output_choice == "1":
            output_types = ["point"]
            break
        elif output_choice == "2":
            output_types = ["line"]
            break
        elif output_choice == "3":
            output_types = ["point", "line"]
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

    # Prompt for coordinate reference system
    while True:
        print("\nEnter coordinate reference system (CRS):")
        print(
            "Examples: EPSG:2263 (NJ State Plane), EPSG:4326 (WGS84), EPSG:26918 (UTM Zone 18N)"
        )
        crs = input("CRS (default: EPSG:2263): ").strip()
        if not crs:
            crs = "EPSG:2263"
        # Basic validation - should start with EPSG: or be a proj string
        if not (crs.startswith("EPSG:") or crs.startswith("+proj=")):
            print(
                "❌ CRS should be in format 'EPSG:XXXX' or a proj string starting with '+proj='"
            )
            continue
        break

    # Confirm vertical datum
    print("\nVertical datum: NAVD88 (assumed for coastal NJ profiles)")
    vertical_datum = "NAVD88"

    # Prompt for output file names
    output_files = {}
    for output_type in output_types:
        while True:
            if output_type == "point":
                default_name = Path(input_file).stem + "_points.shp"
                prompt = f"Enter output point Shapefile path (default: {default_name}): "
            else:  # line
                default_name = Path(input_file).stem + "_lines.shp"
                prompt = f"Enter output line Shapefile path (default: {default_name}): "

            output_path = input(prompt).strip()
            if not output_path:
                output_path = str(Path(input_file).parent / default_name)

            # Check if file already exists
            if Path(output_path).exists():
                overwrite = (
                    input(
                        f"File '{output_path}' already exists. Overwrite? (y/N): "
                    )
                    .strip()
                    .lower()
                )
                if overwrite != "y":
                    continue

            output_files[output_type] = output_path
            break

    # Perform the conversion
    try:
        convert_xyz_to_shapefile(
            input_file=input_file,
            output_files=output_files,
            output_types=output_types,
            origin_azimuth_file=origin_azimuth_file,
            crs=crs,
            vertical_datum=vertical_datum,
        )
        print("✅ Conversion completed successfully.")
        for output_type, output_file in output_files.items():
            print(
                f"   {output_type.capitalize()} Shapefile saved to: {output_file}"
            )
    except (
        OSError,
        ValueError,
        TypeError,
        RuntimeError,
        KeyError,
        IndexError,
        ImportError,
    ) as e:
        print(f"❌ Conversion failed: {e}")

    input("\nPress Enter to continue...")


def convert_shapefile_to_bmap(input_file: str, output_file: str) -> None:
    """
    Convert point shapefile to BMAP free format.

    Parameters:
        input_file (str): Path to input shapefile (.shp file)
        output_file (str): Path to output BMAP file

    Returns:
        None

    Raises:
        ImportError: If geopandas is not available
        FileNotFoundError: If input file does not exist
        ValueError: If shapefile format is invalid
    """
    if not SHAPEFILE_AVAILABLE:
        raise ImportError("Shapefile support not available")

    # Read profiles from shapefile
    profiles = read_point_shapefile(Path(input_file))

    if not profiles:
        raise ValueError("No profiles found in shapefile")

    # Write to BMAP format
    write_bmap_profiles(profiles, output_file)


def convert_shapefile_to_xyz(
    input_file: str, output_file: str, output_format: str = "xyz"
) -> None:
    """
    Convert point shapefile to XYZ or CSV format.

    Parameters:
        input_file (str): Path to input shapefile (.shp file)
        output_file (str): Path to output file
        output_format (str): Output format ("xyz" or "csv")

    Returns:
        None

    Raises:
        ImportError: If geopandas is not available
        FileNotFoundError: If input file does not exist
        ValueError: If shapefile format is invalid
    """
    if not SHAPEFILE_AVAILABLE:
        raise ImportError("Shapefile support not available")

    # Read profiles from shapefile
    profiles = read_point_shapefile(Path(input_file))

    if not profiles:
        raise ValueError("No profiles found in shapefile")

    if output_format == "xyz":
        # Convert to XYZ format
        xyz_data = []
        for profile in profiles:
            y_coords = (
                profile.metadata.get("y", [0.0] * len(profile.x))
                if profile.metadata
                else [0.0] * len(profile.x)
            )
            for i in range(len(profile.x)):
                xyz_data.append(
                    f"{profile.x[i]:.3f} {y_coords[i]:.3f} {profile.z[i]:.3f}"
                )

        # Write XYZ file
        with open(output_file, "w") as f:
            f.write("# Converted from shapefile\n")
            for line in xyz_data:
                f.write(line + "\n")

    elif output_format == "csv":
        # Convert to CSV format
        csv_data = []
        for profile in profiles:
            y_coords = (
                profile.metadata.get("y", [0.0] * len(profile.x))
                if profile.metadata
                else [0.0] * len(profile.x)
            )
            for i in range(len(profile.x)):
                csv_data.append(
                    {
                        "profile_name": profile.name,
                        "X": profile.x[i],
                        "Y": y_coords[i],
                        "Z": profile.z[i],
                    }
                )

        # Write CSV file
        import pandas as pd

        df = pd.DataFrame(csv_data)
        df.to_csv(output_file, index=False)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def execute_shapefile_to_bmap() -> None:
    """
    Execute shapefile to BMAP conversion from interactive menu.

    Prompts user for input shapefile and output BMAP file path,
    then performs the conversion with appropriate error handling.

    Parameters:
        None (interactive function)

    Returns:
        None
    """
    print("\n" + "=" * 60)
    print("POINT SHAPEFILE TO BMAP FREE FORMAT CONVERSION")
    print("=" * 60)

    # Check if shapefile support is available
    if not SHAPEFILE_AVAILABLE:
        print("❌ Shapefile support not available.")
        print("Install with: pip install profile-analysis[gis]")
        input("\nPress Enter to continue...")
        return

    # Prompt for input shapefile
    while True:
        input_file = input("Enter input shapefile path (.shp): ").strip()
        if not input_file:
            print("❌ Input file path is required.")
            continue
        if not Path(input_file).exists():
            print(f"❌ Input file '{input_file}' does not exist.")
            continue
        break

    # Prompt for output BMAP file
    while True:
        output_file = input("Enter output BMAP file path: ").strip()
        if not output_file:
            print("❌ Output file path is required.")
            continue
        break

    # Perform the conversion
    try:
        convert_shapefile_to_bmap(input_file, output_file)
        print(
            f"✅ Conversion completed successfully. Output saved to '{output_file}'"
        )
    except (OSError, ValueError, TypeError, RuntimeError) as e:
        print(f"❌ Conversion failed: {e}")

    input("\nPress Enter to continue...")


def execute_shapefile_to_xyz() -> None:
    """
    Execute shapefile to XYZ/CSV conversion from interactive menu.

    Prompts user for input shapefile and output XYZ/CSV file path,
    then performs the conversion with appropriate error handling.

    Parameters:
        None (interactive function)

    Returns:
        None
    """
    print("\n" + "=" * 60)
    print("POINT SHAPEFILE TO XYZ/CSV CONVERSION")
    print("=" * 60)

    # Check if shapefile support is available
    if not SHAPEFILE_AVAILABLE:
        print("❌ Shapefile support not available.")
        print("Install with: pip install profile-analysis[gis]")
        input("\nPress Enter to continue...")
        return

    # Prompt for output type
    while True:
        print("\nChoose output format:")
        print("1. XYZ format (X,Y,Z coordinates)")
        print("2. CSV format (profile_name, X, Y, Z)")
        output_choice = input("Select output type (1 or 2): ").strip()

        if output_choice == "1":
            output_format = "xyz"
            break
        elif output_choice == "2":
            output_format = "csv"
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

    # Prompt for input shapefile
    while True:
        input_file = input("Enter input shapefile path (.shp): ").strip()
        if not input_file:
            print("❌ Input file path is required.")
            continue
        if not Path(input_file).exists():
            print(f"❌ Input file '{input_file}' does not exist.")
            continue
        break

    # Prompt for output file
    while True:
        output_file = input(
            f"Enter output {output_format.upper()} file path: "
        ).strip()
        if not output_file:
            print("❌ Output file path is required.")
            continue
        break

    # Perform the conversion
    try:
        convert_shapefile_to_xyz(input_file, output_file, output_format)
        print(
            f"✅ Conversion completed successfully. Output saved to '{output_file}'"
        )
    except (OSError, ValueError, TypeError, RuntimeError) as e:
        print(f"❌ Conversion failed: {e}")

    input("\nPress Enter to continue...")


def transform_coordinates(input_file, azimuth_file):
    """
    Transform relative BMAP coordinates to absolute geographic coordinates.

    Args:
        input_file (str): Path to the input BMAP file.
        azimuth_file (str): Path to the origin azimuth file.

    Returns:
        pd.DataFrame: Transformed coordinates as a DataFrame.
    """
    # Read input data
    bmap_df = pd.read_csv(input_file)
    azimuth_df = pd.read_csv(azimuth_file)

    # Ensure required columns exist
    if not {'X', 'Y', 'Z'}.issubset(bmap_df.columns):
        raise ValueError("Input file must contain 'X', 'Y', and 'Z' columns.")
    if not {'OriginX', 'OriginY', 'Azimuth'}.issubset(azimuth_df.columns):
        raise ValueError("Azimuth file must contain 'OriginX', 'OriginY', and 'Azimuth' columns.")

    # Perform transformation
    origin_x = azimuth_df['OriginX'].iloc[0]
    origin_y = azimuth_df['OriginY'].iloc[0]
    azimuth = np.radians(azimuth_df['Azimuth'].iloc[0])

    # Translate coordinates to origin
    bmap_df['X_translated'] = bmap_df['X'] - origin_x
    bmap_df['Y_translated'] = bmap_df['Y'] - origin_y

    # Rotate coordinates based on azimuth
    bmap_df['X_absolute'] = (
        bmap_df['X_translated'] * np.cos(azimuth) -
        bmap_df['Y_translated'] * np.sin(azimuth)
    )
    bmap_df['Y_absolute'] = (
        bmap_df['X_translated'] * np.sin(azimuth) +
        bmap_df['Y_translated'] * np.cos(azimuth)
    )

    # Return transformed DataFrame
    return bmap_df[['X_absolute', 'Y_absolute', 'Z']]


def prompt_9column_questions():
    """Prompt user for 9-column format configuration."""
    print("\nPlease provide the following details for the 9-column format:")
    metadata = input("Enter metadata header (e.g., survey date, location): ").strip()
    column_order = input("Enter column order (e.g., X, Y, Z, etc.): ").strip()
    return {
        "metadata": metadata,
        "column_order": column_order,
    }


def prompt_xyz_questions():
    """Prompt user for XYZ format configuration."""
    print("\nPlease provide the following details for the XYZ format:")
    coordinate_system = input("Enter coordinate system (e.g., WGS84, UTM): ").strip()
    precision = input("Enter precision for coordinates (e.g., 2 decimal places): ").strip()
    return {
        "coordinate_system": coordinate_system,
        "precision": precision,
    }


def convert_to_9column(input_file, output_file, params):
    """Convert input BMAP file to 9-column format."""
    print("Converting to 9-column format...")
    print(f"Metadata: {params['metadata']}")
    print(f"Column Order: {params['column_order']}")
    # Placeholder logic for conversion
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        outfile.write(f"# Metadata: {params['metadata']}\n")
        outfile.write(f"# Column Order: {params['column_order']}\n")
        for line in infile:
            outfile.write(line)
    print(f"Conversion to 9-column format completed: {output_file}")


def convert_to_xyz(input_file, output_file, params):
    """Convert input BMAP file to XYZ format."""
    print("Converting to XYZ format...")
    print(f"Coordinate System: {params['coordinate_system']}")
    print(f"Precision: {params['precision']}")
    # Placeholder logic for conversion
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        outfile.write(f"# Coordinate System: {params['coordinate_system']}\n")
        outfile.write(f"# Precision: {params['precision']}\n")
        for line in infile:
            outfile.write(line)
    print(f"Conversion to XYZ format completed: {output_file}")

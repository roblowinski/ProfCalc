# =============================================================================
# Core Data Conversion and Format Detection Utilities
# =============================================================================
#
# FILE: src/profcalc/cli/tools/convert_core.py
#
# PURPOSE:
# This module contains the core conversion logic and utility functions that
# are shared across different data conversion operations in ProfCalc. It
# provides format detection, column parsing, coordinate transformations, and
# other foundational functionality used by various conversion tools.
#
# WHAT IT'S FOR:
# - Provides automatic file format detection for various data types
# - Handles column order parsing and axis mapping for coordinate data
# - Implements coordinate transformations between different systems
# - Supports baseline file reading and real-world coordinate calculations
# - Offers shared validation and error handling for conversion operations
# - Enables consistent conversion behavior across different tools
#
# WORKFLOW POSITION:
# This module serves as the foundation for all data conversion operations in
# ProfCalc. It's used by various conversion tools (BMAP, XYZ, shapefile, etc.)
# to provide consistent format detection, parsing, and transformation logic.
# It ensures that conversion operations behave predictably and handle edge
# cases appropriately.
#
# LIMITATIONS:
# - Format detection relies on file content patterns and heuristics
# - Column parsing assumes standard delimiter-separated formats
# - Coordinate transformations require valid baseline definitions
# - Some format detection may have false positives or negatives
#
# ASSUMPTIONS:
# - Input files contain structured data with recognizable patterns
# - Coordinate systems are properly defined and consistent
# - Baseline files contain valid azimuth and origin information
# - Users understand coordinate transformation concepts
# - File formats follow expected conventions and structures
#
# =============================================================================

"""Core conversion utilities and format detection.

This module contains the core conversion logic and utility functions
shared across different conversion operations.
"""

import math
from pathlib import Path

from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error

# Type for format (use str for now, as FormatType is not defined as a type alias or class)
FormatType = str


def _parse_column_order(order_string: str) -> dict[str, int]:
    """
    Parse user-specified column order.

    Parameters:
        order_string: Column order specification

    Returns:
        Dictionary mapping axis names to column indices

    Examples:
        "X Y Z" -> {"x": 0, "y": 1, "z": 2}
        "1 0 2" -> {"x": 1, "y": 0, "z": 2}
    """
    parts = order_string.strip().split()
    if len(parts) != 3:
        raise ValueError("Column order must specify exactly 3 columns (X Y Z)")

    # Check if it's numeric indices or axis names
    try:
        indices = [int(p) for p in parts]
        if not all(0 <= i <= 2 for i in indices):
            raise ValueError("Column indices must be 0, 1, or 2")
        return {"x": indices[0], "y": indices[1], "z": indices[2]}
    except ValueError:
        # Try axis names
        axis_map = {"x": 0, "y": 1, "z": 2}
        try:
            return {
                axis: axis_map[axis_name.lower()]
                for axis, axis_name in zip(["x", "y", "z"], parts)
            }
        except KeyError as e:
            raise ValueError(f"Unknown axis name: {e}")


def _detect_format(file_path: str) -> FormatType:
    """
    Auto-detect file format from path and content.

    Parameters:
        file_path: Path to the file to analyze

    Returns:
        Detected format: "bmap", "csv", "xyz", or "shp"
    """
    path = Path(file_path)

    # Check extension first
    ext = path.suffix.lower()
    if ext == ".shp":
        return "shp"

    # Read first few lines to detect format
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = []
            for i, line in enumerate(f):
                lines.append(line.strip())
                if i >= 10:  # Read first 10 lines
                    break

        if not lines:
            raise ValueError("File is empty")

        # Check for BMAP format (free format with profile headers)
        first_line = lines[0]
        if any(
            keyword in first_line.upper() for keyword in ["PROFILE", "DATE", "TYPE"]
        ):
            return "bmap"

        # Check for CSV/XYZ format
        # Look for numeric data patterns
        data_lines = [line for line in lines if line and not line.startswith("#")]
        if len(data_lines) < 2:
            return "csv"  # Default to CSV if unclear

        # Sample some data lines
        sample_lines = data_lines[: min(5, len(data_lines))]
        numeric_counts = []

        for line in sample_lines:
            parts = line.split(",")
            if len(parts) < 3:
                parts = line.split()  # Try space-separated

            numeric_count = sum(1 for part in parts if _is_numeric(part.strip()))
            numeric_counts.append(numeric_count)

        avg_numeric = sum(numeric_counts) / len(numeric_counts) if numeric_counts else 0

        # Heuristic: if mostly numeric data, likely XYZ; otherwise CSV
        if avg_numeric >= 2.5:  # At least 2.5 numeric columns on average
            return "xyz"
        else:
            return "csv"

    except (OSError, UnicodeDecodeError) as e:
        log_quick_tool_error(
            "convert_core", f"Error reading file for format detection: {e}", exc=e
        )
        # Default to CSV if we can't read the file
        return "csv"


def _is_numeric(value: str) -> bool:
    """Check if a string represents a numeric value."""
    try:
        float(value)
        return True
    except ValueError:
        return False


def _warn_bmap_data_loss(profiles: list) -> None:
    """
    Warn about potential data loss when converting from BMAP to other formats.

    Parameters:
        profiles: List of Profile objects to check
    """
    has_metadata = any(
        hasattr(p, "metadata") and p.metadata for p in profiles if p is not None
    )

    if has_metadata:
        print(
            "⚠️  Warning: BMAP files contain additional metadata (profile names, dates, etc.)"
        )
        print("   that will not be preserved in the output format.")
        print("   Consider using CSV format to retain more information.")


def _read_baseline_file(baselines_file: str) -> dict[str, dict[str, float]]:
    """
    Read baseline/origin file for coordinate transformations.

    Parameters:
        baselines_file: Path to baseline file

    Returns:
        Dictionary mapping profile IDs to baseline data
    """
    baselines = {}

    try:
        with open(baselines_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split(",")
                if len(parts) < 4:
                    parts = line.split()  # Try space-separated

                if len(parts) < 4:
                    log_quick_tool_error(
                        "convert_core",
                        f"Invalid baseline format at line {line_num}: {line}",
                    )
                    continue

                try:
                    profile_id = parts[0].strip()
                    origin_x = float(parts[1])
                    origin_y = float(parts[2])
                    azimuth = float(parts[3])

                    baselines[profile_id] = {
                        "origin_x": origin_x,
                        "origin_y": origin_y,
                        "azimuth": azimuth,
                    }
                except (ValueError, IndexError) as e:
                    log_quick_tool_error(
                        "convert_core",
                        f"Error parsing baseline at line {line_num}: {e}",
                    )
                    continue

    except (OSError, IOError) as e:
        log_quick_tool_error(
            "convert_core", f"Error reading baseline file {baselines_file}: {e}", exc=e
        )
        raise

    if not baselines:
        raise ValueError(f"No valid baseline data found in {baselines_file}")

    return baselines


def _parse_coordinate(value: str | float) -> float:
    """
    Parse a coordinate value, handling various formats.

    Parameters:
        value: Coordinate value as string or number

    Returns:
        Parsed coordinate as float
    """
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Remove common separators and try to parse
        cleaned = value.strip().replace(",", "").replace(" ", "")
        try:
            return float(cleaned)
        except ValueError:
            raise ValueError(f"Cannot parse coordinate: {value}")

    raise TypeError(f"Unsupported coordinate type: {type(value)}")


def _calculate_real_world_coordinates(
    cross_shore: float,
    elevation: float,
    origin_x: float,
    origin_y: float,
    azimuth: float,
) -> tuple[float, float]:
    """
    Calculate real-world coordinates from cross-shore distance and elevation.

    Parameters:
        cross_shore: Cross-shore distance (X coordinate in profile space)
        elevation: Elevation (Z coordinate)
        origin_x: Profile origin X coordinate
        origin_y: Profile origin Y coordinate
        azimuth: Profile azimuth in degrees (0° = north, 90° = east)

    Returns:
        Tuple of (real_x, real_y) coordinates
    """
    # Convert azimuth to radians
    azimuth_rad = math.radians(azimuth)

    # Calculate real-world coordinates
    real_x = origin_x + cross_shore * math.sin(azimuth_rad)
    real_y = origin_y + cross_shore * math.cos(azimuth_rad)

    return real_x, real_y

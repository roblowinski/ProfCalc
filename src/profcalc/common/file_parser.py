"""
File Parser Module - Unified parsing for all supported formats in ProfCalc.

This module provides centralized file parsing that handles:
- BMAP Free Format files
- Delimited files (CSV/TSV/space-delimited, 3-9 columns, with/without headers)

All parsers return standardized data structures for downstream processing.
"""

from pathlib import Path
from typing import Any, Optional

from .format_detection import (
    FormatDetectionResult,
    detect_csv_has_header,
    detect_file_format_detailed,
    get_format_description,
)


class ParsedFile:
    """
    Container for parsed file data with standardized structure.

    Attributes:
        format_type: Detected format ('bmap', 'csv')
        profiles: List of profile dictionaries
        metadata: Optional metadata from file headers
        has_header: Whether delimited file has header row(s)
        column_mapping: Mapping of column names to indices
        delimiter: Delimiter character used (for CSV files)
    """

    def __init__(
        self,
        format_type: str,
        profiles: list[dict[str, Any]],
        metadata: Optional[dict[str, Any]] = None,
        has_header: bool = False,
        column_mapping: Optional[dict[str, int]] = None,
        delimiter: str = ",",
    ):
        self.format_type = format_type
        self.profiles = profiles
        self.metadata = metadata or {}
        self.has_header = has_header
        self.column_mapping = column_mapping or {}
        self.delimiter = delimiter

    def __repr__(self) -> str:
        return (
            f"ParsedFile(format={self.format_type}, "
            f"profiles={len(self.profiles)}, "
            f"has_header={self.has_header})"
        )


def parse_file(file_path: Path, skip_confirmation: bool = False) -> ParsedFile:
    """
    Parse a file and return standardized data structure.

    Args:
        file_path: Path to file to parse
        skip_confirmation: If False, will prompt user to confirm detected format

    Returns:
        ParsedFile object with structured data

    Raises:
        ValueError: If file format is unknown or parsing fails
        FileNotFoundError: If file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Detect format with detailed analysis
    detection_result = detect_file_format_detailed(file_path)

    if detection_result.format_type == "unknown":
        error_msg = f"Cannot determine file format for: {file_path}\n"
        error_msg += "Supported formats: BMAP free format, CSV (automatic column detection)\n"
        if detection_result.warnings:
            error_msg += f"Warnings: {', '.join(detection_result.warnings)}"
        raise ValueError(error_msg)

    # Show detection summary and get user confirmation (unless skipped)
    if not skip_confirmation:
        confirmed = _confirm_format_detection(detection_result, file_path)
        if not confirmed:
            raise ValueError("Format detection cancelled by user")

    # Read file lines (try multiple encodings)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n\r") for line in f.readlines()]
    except UnicodeDecodeError:
        # Try with different encodings if UTF-8 fails
        for encoding in [
            "utf-16",
            "utf-16-le",
            "utf-16-be",
            "latin-1",
            "cp1252",
        ]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    lines = [line.rstrip("\n\r") for line in f.readlines()]
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            raise ValueError("Unable to read file with standard encodings")

    # Parse based on format
    format_type = detection_result.format_type
    if format_type == "bmap":
        return parse_bmap(lines, file_path, detection_result)
    elif format_type == "csv":
        return parse_csv(lines, file_path, detection_result)
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def _confirm_format_detection(
    detection: FormatDetectionResult, file_path: Path
) -> bool:
    """
    Display format detection results and get user confirmation.

    Args:
        detection: Format detection result
        file_path: Path to file being analyzed

    Returns:
        True if user confirms, False otherwise
    """
    print("\n" + "=" * 70)
    print("FILE FORMAT DETECTION")
    print("=" * 70)
    print(f"File: {file_path.name}")
    print()
    print(detection.get_summary())
    print()
    print("=" * 70)

    # For high confidence, default to yes
    if detection.confidence == "high" and not detection.warnings:
        response = input("Proceed with this format? [Y/n]: ")

        return response in ["", "y", "yes"]
    else:
        # For medium/low confidence or warnings, require explicit yes
        response = input("Proceed with this format? [y/N]: ")

        return response in ["y", "yes"]


def parse_bmap(
    lines: list[str],
    file_path: Path,
    detection_result: Optional[FormatDetectionResult] = None,
) -> ParsedFile:
    """
    Parse BMAP free format file.

    BMAP structure:
    - Profile header line (Profile ID, optional date/purpose)
    - Point count line (integer)
    - Coordinate pairs (X Y per line)

    Args:
        lines: List of file lines
        file_path: Path to source file
        detection_result: Optional detection result for additional context

    Returns:
        ParsedFile with BMAP profiles
    """
    profiles: list[dict[str, Any]] = []
    i: int = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Check if this could be a profile header
        if i + 2 < len(lines):
            count_line = lines[i + 1].strip()

            # Try to parse as point count
            try:
                point_count = int(count_line)
                if point_count > 0:
                    # Found a profile
                    profile_header = line
                    profile_data = _parse_bmap_profile_header(profile_header)

                    # Read coordinate pairs
                    coordinates = []
                    for j in range(
                        i + 2, min(i + 2 + point_count, len(lines))
                    ):
                        coord_line = lines[j].strip()
                        if not coord_line:
                            continue

                        parts = coord_line.split()
                        if len(parts) >= 2:
                            try:
                                x = float(parts[0])
                                y = float(parts[1])
                                coordinates.append({"x": x, "y": y})
                            except ValueError:
                                continue

                    profile_data["point_count"] = point_count
                    profile_data["actual_point_count"] = len(coordinates)
                    profile_data["coordinates"] = coordinates

                    profiles.append(profile_data)

                    # Move index past this profile
                    i += 2 + point_count
                    continue
            except ValueError:
                pass

        i += 1

    metadata = {
        "source_file": str(file_path),
        "format_description": get_format_description("bmap"),
    }

    return ParsedFile(format_type="bmap", profiles=profiles, metadata=metadata)


def _parse_bmap_profile_header(header: str) -> dict[str, Any]:
    """
    Parse BMAP profile header line to extract profile ID, date, and purpose.

    Args:
        header: Profile header line

    Returns:
        Dictionary with profile_id, date, purpose fields
    """
    parts: list[str] = header.split()

    profile_data: dict[str, Any] = {
        "profile_id": parts[0] if parts else "UNKNOWN",
        "date": None,
        "purpose": None,
        "raw_header": header,
    }

    if len(parts) >= 2:
        # Second part might be date (YYYY_MM_DD or similar)
        if "_" in parts[1] or "-" in parts[1]:
            profile_data["date"] = parts[1]
        else:
            profile_data["purpose"] = parts[1]

    if len(parts) >= 3:
        # Third part is purpose if second was date
        if profile_data["date"]:
            profile_data["purpose"] = " ".join(parts[2:])
        else:
            profile_data["date"] = parts[1]
            profile_data["purpose"] = " ".join(parts[2:])

    return profile_data


def parse_csv(
    lines: list[str],
    file_path: Path,
    detection_result: Optional[FormatDetectionResult] = None,
) -> ParsedFile:
    """
    Parse delimited file (CSV/TSV/space-delimited, 3-9 columns, with/without headers).

    Supports:
    - Comma, tab, or space-delimited files
    - Optional header lines (1-2 lines)
    - 3-9 columns with flexible column naming
    - Profile ID columns: PROFILE, NAME, PROFILE_NAME, PROFILE_ID, ID
    - X coordinate: EASTING, X
    - Y coordinate: NORTHING, Y
    - Z coordinate: ELEVATION, ELEV, Z
    - Additional metadata columns (preserved but not required)

    Args:
        lines: List of file lines
        file_path: Path to source file
        detection_result: Optional detection result for delimiter info

    Returns:
        ParsedFile with parsed profiles
    """
    # Get delimiter from detection result
    delimiter = ","
    if detection_result and "delimiter" in detection_result.details:
        delimiter = detection_result.details["delimiter"]

    # Detect if file has headers
    has_header = detect_csv_has_header(lines, delimiter)

    # Find data start (skip metadata header lines if present)
    data_start: int = 0
    metadata_lines: list[str] = []

    if has_header:
        # Check for multi-line headers or metadata
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # Check if this looks like a data line (all numeric columns after first)
            parts = [p.strip() for p in line.split(delimiter)]
            if len(parts) >= 3:
                # Count how many parts (after first) are numeric
                numeric_count = sum(1 for p in parts[1:] if _is_numeric(p))

                # If most parts are numeric, this is data
                if numeric_count >= len(parts) - 2:
                    data_start = i
                    break
                else:
                    # This is a header/metadata line
                    metadata_lines.append(stripped)

        # If we didn't find data, assume header is just first line
        if data_start == 0 and metadata_lines:
            data_start = len(metadata_lines)

    # Get header line (last metadata line before data)
    header_line: Optional[str] = metadata_lines[-1] if metadata_lines else None

    # Build column mapping from header
    column_mapping: dict[str, int] = (
        _build_column_mapping(header_line, delimiter) if header_line else {}
    )

    # Parse data rows
    profiles_dict: dict[str, dict[str, Any]] = {}  # Group by profile ID

    for i in range(data_start, len(lines)):
        line = lines[i].strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(delimiter)]

        # Skip if insufficient columns
        if len(parts) < 3:
            continue

        # Determine profile ID using flexible matching
        profile_id: str = _extract_profile_id(parts, column_mapping)

        # Initialize profile if not exists
        if profile_id not in profiles_dict:
            profiles_dict[profile_id] = {
                "profile_id": profile_id,
                "date": None,
                "coordinates": [],
                "all_columns": [],  # Preserve all data
            }

        # Extract coordinates using flexible column matching
        coord_data = _extract_coordinates(parts, column_mapping)

        if (
            coord_data
            and coord_data.get("x") is not None
            and coord_data.get("y") is not None
        ):
            profiles_dict[profile_id]["coordinates"].append(coord_data)

            # Extract date from first row if available
            if (
                not profiles_dict[profile_id]["date"]
                and "DATE" in column_mapping
            ):
                try:
                    profiles_dict[profile_id]["date"] = parts[
                        column_mapping["DATE"]
                    ]
                except IndexError:
                    pass

        # Preserve all columns
        profiles_dict[profile_id]["all_columns"].append(parts)

    # Convert to list
    profiles = list(profiles_dict.values())

    # Add point counts
    for profile in profiles:
        profile["point_count"] = len(profile["coordinates"])
        profile["actual_point_count"] = len(profile["coordinates"])

    metadata = {
        "source_file": str(file_path),
        "format_description": get_format_description("csv"),
        "has_header": has_header,
        "header_lines": metadata_lines,
        "delimiter": delimiter,
    }

    return ParsedFile(
        format_type="csv",
        profiles=profiles,
        metadata=metadata,
        has_header=has_header,
        column_mapping=column_mapping,
        delimiter=delimiter,
    )


def _is_numeric(value: str) -> bool:
    """Check if string represents a numeric value."""
    try:
        float(value)
        return True
    except (ValueError, AttributeError):
        return False


def _build_column_mapping(
    header_line: Optional[str], delimiter: str
) -> dict[str, int]:
    """
    Build column mapping from header line with flexible column name matching.

    Recognizes:
    - Profile ID: PROFILE, NAME, PROFILE_NAME, PROFILE_ID, ID
    - X: EASTING, X
    - Y: NORTHING, Y
    - Z: ELEVATION, ELEV, Z
    - Plus DATE, TIME, POINT_NUM, TYPE, DESCRIPTION

    Args:
        header_line: Header line string
        delimiter: Delimiter character

    Returns:
        Dictionary mapping standard names to column indices
    """
    if not header_line:
        return {}

    mapping: dict[str, int] = {}
    headers: list[str] = [
        h.strip().upper() for h in header_line.split(delimiter)
    ]

    for i, header in enumerate(headers):
        # Store original header
        mapping[header] = i

        # Profile ID variants
        if header in ("PROFILE", "NAME", "PROFILE_NAME", "PROFILE_ID", "ID"):
            if (
                "PROFILE_ID" not in mapping or header == "PROFILE"
            ):  # Prefer PROFILE
                mapping["PROFILE_ID"] = i

        # X coordinate variants
        elif header in ("EASTING", "X"):
            mapping["X"] = i

        # Y coordinate variants
        elif header in ("NORTHING", "Y"):
            mapping["Y"] = i

        # Z coordinate variants
        elif header in ("ELEVATION", "ELEV", "Z"):
            mapping["Z"] = i

        # Other common columns
        elif "DATE" in header:
            mapping["DATE"] = i
        elif "TIME" in header:
            mapping["TIME"] = i
        elif "POINT" in header and "NUM" in header:
            mapping["POINT_NUM"] = i
        elif "TYPE" in header:
            mapping["TYPE"] = i
        elif "DESC" in header:
            mapping["DESCRIPTION"] = i

    return mapping


def _extract_profile_id(
    parts: list[str], column_mapping: dict[str, int]
) -> str:
    """
    Extract profile ID from data row using column mapping or heuristics.

    Args:
        parts: Split data row parts
        column_mapping: Column name to index mapping

    Returns:
        Profile ID string
    """
    # Try mapped PROFILE_ID column
    if "PROFILE_ID" in column_mapping:
        try:
            return parts[column_mapping["PROFILE_ID"]]
        except IndexError:
            pass

    # Fallback: if first column is not numeric, use it as ID
    if len(parts) >= 4 and not _is_numeric(parts[0]):
        return parts[0]

    return "UNKNOWN"


def _extract_coordinates(
    parts: list[str], column_mapping: dict[str, int]
) -> Optional[dict[str, Any]]:
    """
    Extract coordinate data from row parts using column mapping or heuristics.

    Args:
        parts: Split data row parts
        column_mapping: Column name to index mapping

    Returns:
        Dictionary with x, y, z and optional metadata fields
    """
    coord: dict[str, Any] = {}

    # Try to extract using column mapping
    if "X" in column_mapping and "Y" in column_mapping:
        try:
            coord["x"] = float(parts[column_mapping["X"]])
            coord["y"] = float(parts[column_mapping["Y"]])
            if "Z" in column_mapping:
                coord["z"] = float(parts[column_mapping["Z"]])

            # Add optional metadata fields
            if "TIME" in column_mapping and column_mapping["TIME"] < len(
                parts
            ):
                coord["time"] = parts[column_mapping["TIME"]]
            if "POINT_NUM" in column_mapping and column_mapping[
                "POINT_NUM"
            ] < len(parts):
                coord["point_num"] = parts[column_mapping["POINT_NUM"]]
            if "TYPE" in column_mapping and column_mapping["TYPE"] < len(
                parts
            ):
                coord["type"] = parts[column_mapping["TYPE"]]
            if "DESCRIPTION" in column_mapping and column_mapping[
                "DESCRIPTION"
            ] < len(parts):
                coord["description"] = parts[column_mapping["DESCRIPTION"]]

            return coord
        except (ValueError, IndexError):
            pass

    # Fallback: guess based on column count and numeric detection
    try:
        if len(parts) == 3:
            # X, Y, Z
            x: float = float(parts[0])
            y: float = float(parts[1])
            z: float = float(parts[2])
            coord["x"] = x
            coord["y"] = y
            coord["z"] = z
            return coord
        elif len(parts) == 4:
            # Profile ID, X, Y, Z
            x = float(parts[1])
            y = float(parts[2])
            z = float(parts[3])
            coord["x"] = x
            coord["y"] = y
            coord["z"] = z
            return coord
        elif len(parts) >= 4:
            # Try to find X, Y, Z sequence
            for j in range(len(parts) - 2):
                try:
                    x = float(parts[j])
                    y = float(parts[j + 1])
                    z = float(parts[j + 2])
                    coord["x"] = x
                    coord["y"] = y
                    coord["z"] = z
                    return coord
                except ValueError:
                    continue
    except (ValueError, IndexError):
        pass

    return None


def parse_csv_standard(
    lines: list[str],
    file_path: Path,
    detection_result: Optional[FormatDetectionResult] = None,
) -> ParsedFile:
    """
    DEPRECATED: Use parse_csv() instead.

    Parse standard CSV file (3-9 columns, with/without header).

    Args:
        lines: List of file lines
        file_path: Path to source file
        detection_result: Optional detection result for additional context

    Returns:
        ParsedFile with CSV profiles
    """
    return parse_csv(lines, file_path, detection_result)


def parse_csv_9col(
    lines: list[str],
    file_path: Path,
    detection_result: Optional[FormatDetectionResult] = None,
) -> ParsedFile:
    """
    DEPRECATED: Use parse_csv() instead.

    Parse special 9-column CSV format with extensive metadata header.

    9-column format:
    - Metadata header lines (~30+ lines)
    - "(START OF DATA)" marker
    - 9-column data: PROFILE ID, DATE, TIME, POINT #, X, Y, Z, TYPE, DESCRIPTION

    Args:
        lines: List of file lines
        file_path: Path to source file
        detection_result: Optional detection result for additional context

    Returns:
        ParsedFile with 9-column profiles and preserved metadata
    """
    return parse_csv(lines, file_path, detection_result)

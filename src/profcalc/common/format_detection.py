# =============================================================================
# File Format Detection and Analysis Module
# =============================================================================
#
# FILE: src/profcalc/common/format_detection.py
#
# PURPOSE:
# This module provides intelligent content-based file format detection for
# beach profile data files. It analyzes file structure and content to
# automatically identify supported formats (BMAP, CSV, etc.) without relying
# on file extensions, ensuring accurate format recognition for data import.
#
# WHAT IT'S FOR:
# - Detecting BMAP Free Format files with profile headers and coordinate pairs
# - Identifying CSV/delimited files with 3-9 columns and various delimiters
# - Providing confidence levels and detailed detection results
# - Analyzing file content structure rather than extensions
# - Supporting user confirmation for ambiguous format detection
# - Determining if CSV files have header rows
# - Auto-detecting delimiters in delimited text files
#
# WORKFLOW POSITION:
# This module is used early in the data import process to determine how to
# parse incoming files. It ensures that the appropriate parser is selected
# and provides users with confidence information about format detection
# before proceeding with data processing.
#
# LIMITATIONS:
# - Detection accuracy depends on file content following expected patterns
# - May require user confirmation for files with ambiguous structure
# - Limited to supported formats (BMAP, delimited text)
# - Memory usage for reading file samples during detection
# - Complex or corrupted files may not be detected correctly
#
# ASSUMPTIONS:
# - Files contain valid beach profile data structures
# - File content is text-based and readable
# - Supported formats have distinctive structural patterns
# - Users can interpret confidence levels and detection details
# - File samples provide representative content for analysis
#
# =============================================================================

"""
File Format Detection Module - Content-based format detection for ProfCalc.

This module provides centralized format detection logic for all ProfCalc tools.
Detection is based on file content structure, not file extensions.

Supported Formats:
- BMAP Free Format: Profile header + count line + coordinate pairs
- CSV/Delimited: 3-9 columns, delimited by comma/tab/space, may have header row(s)
"""

from pathlib import Path
from typing import Any, Optional


class FormatDetectionResult:
    """
    Container for format detection results with confidence and details.

    Attributes:
        format_type: Detected format ('bmap', 'csv', 'unknown')
        confidence: Confidence level ('high', 'medium', 'low')
        details: Dictionary with detection details for user confirmation
        warnings: List of any issues or ambiguities detected
    """

    def __init__(
        self,
        format_type: str,
        confidence: str = "high",
        details: Optional[dict] = None,
        warnings: Optional[list] = None,
    ):
        self.format_type = format_type
        self.confidence = confidence
        self.details = details or {}
        self.warnings = warnings or []

    def __repr__(self) -> str:
        return f"FormatDetectionResult(format={self.format_type}, confidence={self.confidence})"

    def get_summary(self) -> str:
        """Get human-readable summary for user confirmation."""
        lines = []
        lines.append(f"Detected Format: {get_format_description(self.format_type)}")
        lines.append(f"Confidence: {self.confidence.upper()}")

        if self.details:
            lines.append("\nFormat Details:")
            for key, value in self.details.items():
                lines.append(f"  - {key}: {value}")

        if self.warnings:
            lines.append("\nWarnings:")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")

        return "\n".join(lines)


def detect_file_format(file_path: Path) -> str:
    """
    Detect the format of an input file based on content analysis.

    Args:
        file_path: Path to the file to analyze

    Returns:
        Format type: 'bmap', 'csv_standard', 'csv_9col', or 'unknown'

    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read

    Note:
        For detailed detection results with confidence levels, use detect_file_format_detailed()
    """
    result = detect_file_format_detailed(file_path)
    return result.format_type


def detect_file_format_detailed(file_path: Path) -> FormatDetectionResult:
    """
    Detect file format with detailed results including confidence and warnings.

    Args:
        file_path: Path to the file to analyze

    Returns:
        FormatDetectionResult with format type, confidence, details, and warnings

    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

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
            return FormatDetectionResult(
                "unknown",
                confidence="low",
                warnings=["Unable to read file with standard encodings"],
            )

    if not lines:
        return FormatDetectionResult(
            "unknown", confidence="low", warnings=["File is empty"]
        )

    # Check for BMAP format first
    result = _check_bmap_format(lines, file_path)
    if result.format_type == "bmap":
        return result

    # Check for delimited (CSV/TSV/space-delimited) format
    result = _check_delimited_format(lines, file_path)
    if result.format_type == "csv":
        return result

    return FormatDetectionResult(
        "unknown",
        confidence="low",
        warnings=["File does not match any known format patterns"],
    )


def _check_bmap_format(lines: list[str], file_path: Path) -> FormatDetectionResult:
    """
    Check if file content matches BMAP free format structure with detailed analysis.

    BMAP format characteristics:
    - Profile header line (text, may contain profile ID, date, purpose)
    - Point count line (single integer, may have leading/trailing whitespace)
    - Coordinate pairs (two space-separated numeric values per line)
    - May have blank lines or comments between profiles

    Args:
        lines: List of file lines
        file_path: Path to source file

    Returns:
        FormatDetectionResult with BMAP detection details
    """
    if len(lines) < 3:
        return FormatDetectionResult("unknown", confidence="low")

    profiles_found: int = 0
    warnings: list[str] = []
    details: dict[str, Any] = {}

    # Look for pattern: text line, number line, coordinate pairs
    i = 0
    while i < len(lines) - 2:
        line1 = lines[i].strip()

        # Skip empty lines and comments
        if not line1 or line1.startswith("#") or line1.startswith("//"):
            i += 1
            continue

        # Check next non-empty line for point count
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1

        if j >= len(lines):
            break

        line2 = lines[j].strip()

        # Try to parse as point count
        try:
            point_count = int(line2)
            if point_count <= 0:
                i += 1
                continue
        except ValueError:
            i += 1
            continue

        # Check next non-empty line for coordinate pair
        k = j + 1
        while k < len(lines) and not lines[k].strip():
            k += 1

        if k >= len(lines):
            break

        line3 = lines[k].strip()

        # Should be two space-separated numbers (or tab-separated)
        parts = line3.split()
        if len(parts) >= 2:
            try:
                float(parts[0])
                float(parts[1])
                # Found BMAP pattern
                profiles_found += 1
                i = k + point_count  # Skip past this profile
                continue
            except ValueError:
                pass

        i += 1

    if profiles_found > 0:
        details["profiles_detected"] = profiles_found
        details["extension"] = file_path.suffix or "no extension"

        if profiles_found == 1:
            confidence = "medium"
            warnings.append("Only 1 profile detected - could be partial file")
        else:
            confidence = "high"

        return FormatDetectionResult(
            "bmap", confidence=confidence, details=details, warnings=warnings
        )

    return FormatDetectionResult("unknown", confidence="low")


def _check_delimited_format(lines: list[str], file_path: Path) -> FormatDetectionResult:
    """
    Check if file content matches delimited format (CSV/TSV/space-delimited) with detailed analysis.

    Delimited file characteristics:
    - Values separated by comma, tab, or spaces
    - 3 to 9 columns
    - May have header row(s) (1-2 lines)
    - Consistent column count across rows
    - Tolerates blank lines and metadata at top

    Args:
        lines: List of file lines
        file_path: Path to source file

    Returns:
        FormatDetectionResult with CSV detection details
    """
    if len(lines) < 2:
        return FormatDetectionResult("unknown", confidence="low")

    # Detect delimiter type
    delimiter_result = _detect_delimiter(lines)
    if not delimiter_result:
        return FormatDetectionResult("unknown", confidence="low")

    delimiter, delimiter_name = delimiter_result

    # Find first data line (skip potential metadata)
    first_data_line = None
    data_start_idx = 0

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Skip potential metadata lines (all text, no delimiters with numbers)
        if delimiter in stripped:
            parts = [p.strip() for p in stripped.split(delimiter)]
            # Check if this looks like data (has some numbers)
            numeric_parts = sum(1 for p in parts if p and _is_numeric(p))
            if numeric_parts > 0 or idx > 50:  # Found data or scanned enough
                first_data_line = stripped
                data_start_idx = idx
                break

    if not first_data_line:
        return FormatDetectionResult("unknown", confidence="low")

    # Count columns
    parts = [p.strip() for p in first_data_line.split(delimiter)]
    col_count = len(parts)

    # Must be 3-9 columns
    if col_count < 3 or col_count > 9:
        return FormatDetectionResult("unknown", confidence="low")

    # Verify consistent column count across data rows
    details: dict[str, Any] = {}
    warnings: list[str] = []
    consistent_count = 0
    inconsistent_lines = []
    sample_size = min(20, len(lines) - data_start_idx)
    checked = 0

    for idx in range(
        data_start_idx, min(data_start_idx + sample_size + 10, len(lines))
    ):
        line = lines[idx].strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(delimiter)]
        checked += 1

        if len(parts) == col_count:
            consistent_count += 1
        elif len(parts) > 0:
            inconsistent_lines.append(idx + 1)

        if checked >= sample_size:
            break

    if checked == 0:
        return FormatDetectionResult("unknown", confidence="low")

    consistency_ratio = consistent_count / max(1, checked)

    details["columns"] = col_count
    details["delimiter"] = delimiter  # Store actual delimiter character
    details["delimiter_name"] = delimiter_name  # Also store human-readable name
    details["extension"] = file_path.suffix or "no extension"
    details["data_rows_sampled"] = checked
    details["consistent_rows"] = consistent_count

    # Check for metadata header
    metadata_lines = data_start_idx
    if metadata_lines > 2:
        details["metadata_lines"] = metadata_lines

    # Determine confidence based on consistency
    if consistency_ratio >= 0.95:
        confidence = "high"
    elif consistency_ratio >= 0.80:
        confidence = "medium"
        warnings.append(
            f"Some rows have inconsistent column counts (lines: {inconsistent_lines[:5]})"
        )
    else:
        return FormatDetectionResult(
            "unknown",
            confidence="low",
            warnings=["Too many inconsistent rows for delimited format"],
        )

    # Check if first data row looks like header
    numeric_count = 0
    for part in parts:
        if _is_numeric(part):
            numeric_count += 1

    if numeric_count < len(parts) * 0.5:
        details["header_detected"] = "yes"
    else:
        details["header_detected"] = "no"

    return FormatDetectionResult(
        "csv", confidence=confidence, details=details, warnings=warnings
    )


def _detect_delimiter(lines: list[str]) -> Optional[tuple[str, str]]:
    """
    Detect the delimiter used in a file.

    Args:
        lines: List of file lines

    Returns:
        Tuple of (delimiter_char, delimiter_name) or None if no clear delimiter found
    """
    # Check first few non-empty lines
    sample_lines = []
    for line in lines[:50]:
        if line.strip():
            sample_lines.append(line.strip())
        if len(sample_lines) >= 10:
            break

    if not sample_lines:
        return None

    # Count occurrences of potential delimiters
    delimiters = [
        (",", "comma"),
        ("\t", "tab"),
        ("  ", "space"),  # Two or more spaces
    ]

    best_delimiter = None
    best_score = 0.0

    for delim_char, delim_name in delimiters:
        # Count how many lines have this delimiter
        lines_with_delim = 0
        total_count = 0

        for line in sample_lines:
            if delim_char in line:
                lines_with_delim += 1
                if delim_char == "  ":
                    # Count groups of spaces
                    import re

                    total_count += len(re.findall(r" {2,}", line))
                else:
                    total_count += line.count(delim_char)

        # Score: percentage of lines with delimiter * average count per line
        if lines_with_delim > 0:
            score = (lines_with_delim / len(sample_lines)) * (
                total_count / lines_with_delim
            )
            if score > best_score:
                best_score = score
                best_delimiter = (delim_char, delim_name)

    # Need at least 50% of lines to have the delimiter
    if best_delimiter and best_score >= 0.5:
        return best_delimiter

    return None


def _is_numeric(value: str) -> bool:
    """Check if a string represents a numeric value."""
    try:
        float(value)
        return True
    except ValueError:
        return False


def get_format_description(format_type: str) -> str:
    """
    Get a human-readable description of a detected format.

    Args:
        format_type: Format identifier ('bmap', 'csv', 'unknown')

    Returns:
        Description string
    """
    descriptions = {
        "bmap": "BMAP Free Format (profile header + point count + coordinates)",
        "csv": "Delimited file (CSV/TSV/space-delimited, automatic column detection)",
        "unknown": "Unknown or unsupported format",
    }
    return descriptions.get(format_type, "Unknown format")


def detect_csv_has_header(lines: list[str], delimiter: str = ",") -> bool:
    """
    Detect if a delimited file has a header row.

    Args:
        lines: List of file lines
        delimiter: Delimiter character (default: comma)

    Returns:
        True if header row is present
    """
    if not lines:
        return False

    # Skip metadata lines and find first potential data line
    first_line = None
    for line in lines:
        stripped = line.strip()
        if stripped and delimiter in stripped:
            first_line = stripped
            break

    if not first_line:
        return False

    # Split by delimiter
    parts = [p.strip() for p in first_line.split(delimiter)]

    # Try to parse each part as a number
    numeric_count = 0
    for part in parts:
        if _is_numeric(part):
            numeric_count += 1

    # If most parts are non-numeric, it's likely a header
    return numeric_count < len(parts) * 0.5

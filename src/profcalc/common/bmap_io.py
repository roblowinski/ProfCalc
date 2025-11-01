"""
BMAP I/O Module for Beach Profile Data

This module provides functionality to read BMAP (Beach Morphology Analysis Package)
free format files. BMAP files contain beach profile survey data with header lines
describing survey metadata and coordinate pairs representing profile points.

Supported BMAP features:
- Header parsing with profile name, date, description, and purpose
- Variable point counts per profile
- Multiple profiles per file
- Flexible header formats with date and purpose detection
"""

import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .data_validation import validate_array_properties
from .error_handler import (
    BeachProfileError,
    ErrorCategory,
    LogComponent,
    get_logger,
)
from .file_parser import ParsedFile
from .file_parser import parse_file as parse_file_centralized


def extract_date_from_filename(filename: str) -> Optional[str]:
    """
    Extract date from common filename patterns.

    Recognizes patterns:
    - YYYYMMDD: beach_20241026.xyz → 26OCT2024
    - YYYY-MM-DD: survey_2024-10-26.csv → 26OCT2024
    - MM-DD-YYYY: data_10-26-2024.xyz → 26OCT2024
    - YYYY_MM_DD: profiles_2024_10_26.dat → 26OCT2024

    Args:
        filename: Filename or path to parse

    Returns:
        Date string in DDMMMYYYY format, or None if no date found
    """
    basename = Path(filename).stem

    # Try various date patterns
    patterns = [
        # YYYYMMDD
        (r"(\d{4})(\d{2})(\d{2})", "%Y%m%d"),
        # YYYY-MM-DD or YYYY_MM_DD
        (r"(\d{4})[-_](\d{2})[-_](\d{2})", "%Y-%m-%d"),
        # MM-DD-YYYY or MM_DD_YYYY
        (r"(\d{2})[-_](\d{2})[-_](\d{4})", "%m-%d-%Y"),
    ]

    for pattern, date_format in patterns:
        match = re.search(pattern, basename)
        if match:
            try:
                date_str = match.group(0).replace("_", "-")
                date_obj = datetime.strptime(date_str, date_format)
                return date_obj.strftime("%d%b%Y").upper()
            except (ValueError, IndexError):
                continue

    return None


def format_date_for_bmap(date_input: str | datetime) -> Optional[str]:
    """
    Convert various date formats to BMAP format: DDMMMYYYY

    Handles:
    - ISO format: 2024-10-26 → 26OCT2024
    - US format: 10/26/2024 → 26OCT2024
    - Existing BMAP: 26OCT2024 → 26OCT2024 (pass-through)
    - datetime objects → 26OCT2024

    Args:
        date_input: Date string or datetime object

    Returns:
        Date in DDMMMYYYY format, or None if parsing fails
    """
    if isinstance(date_input, datetime):
        return date_input.strftime("%d%b%Y").upper()

    if not isinstance(date_input, str):
        return None

    date_str = date_input.strip()
    if not date_str:
        return None

    # Check if already in BMAP format (DDMMMYYYY)
    if re.match(r"^\d{2}[A-Z]{3}\d{4}$", date_str.upper()):
        return date_str.upper()

    # Try various formats
    formats = [
        "%Y-%m-%d",  # 2024-10-26
        "%m/%d/%Y",  # 10/26/2024
        "%d/%m/%Y",  # 26/10/2024
        "%Y/%m/%d",  # 2024/10/26
        "%d-%m-%Y",  # 26-10-2024
        "%m-%d-%Y",  # 10-26-2024
        "%d%b%Y",  # 26Oct2024
        "%d-%b-%Y",  # 26-Oct-2024
        "%b %d, %Y",  # Oct 26, 2024
    ]

    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%d%b%Y").upper()
        except ValueError:
            continue

    return None


@dataclass
class Profile:
    """Represents a single beach profile from a BMAP free format file."""

    name: str
    date: Optional[str]
    description: Optional[str]
    x: np.ndarray
    z: np.ndarray
    metadata: Optional[Dict[str, Any]] = None


class BMAPImportError(Exception):
    """Raised when BMAP import fails."""

    pass


class BMAPParser:
    """Parser for BMAP free format files.

    Handles the parsing of BMAP format files containing beach profile
    survey data. BMAP files have header lines followed by point count
    and coordinate pairs.
    """

    PURPOSE_BD = "BD"
    PURPOSE_AD = "AD"
    PURPOSE_TEMPLATE = "T"
    PURPOSE_OTHER = "O"
    PURPOSE_STUDY = "S"
    PURPOSE_PRECON_PS = "PP"
    PURPOSE_PRECON_INFO = "PI"
    PURPOSE_PREPLACE = "PR"
    PURPOSE_PRESTORM = "PS"
    PURPOSE_POSTPLACE = "PO"
    PURPOSE_POSTSTORM = "PT"
    PURPOSE_POSTPLACE2 = "PX"
    PURPOSE_ANNUAL = "A"
    PURPOSE_PRESTORM2 = "P2"
    PURPOSE_POSTSTORM2 = "PT2"
    PURPOSE_DESIGN = "D"

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the BMAP parser.

        Args:
            config: Optional configuration dictionary for parsing options
        """
        self.config = config or {}
        self.logger = get_logger(LogComponent.FILE_IO)

    def parse_header(
        self, header: str
    ) -> tuple[str, Optional[datetime], str, str]:
        """Parse a BMAP header line.

        Args:
            header: Header line from BMAP file

        Returns:
            Tuple of (profile_name, date, description, purpose)

        Notes:
            This parser now handles profile names with spaces by:
            1. First extracting known components (date, purpose codes)
            2. Then treating the remainder as the profile name
            3. Supporting formats like "OC 117 15AUG2020" or "Site Name 01/01/2020"
        """
        header = (header or "").strip()
        if not header:
            return "", None, "", self.PURPOSE_OTHER

        # First, find and extract the date (if present)
        date = None
        date_match = None
        for pat, fmt in [
            (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
            (r"\d{2}/\d{2}/\d{4}", "%m/%d/%Y"),
            (r"\d{2}[A-Za-z]{3}\d{4}", "%d%b%Y"),
        ]:
            m = re.search(pat, header)
            if m:
                try:
                    date = datetime.strptime(m.group(0), fmt)
                    date_match = m
                except ValueError as e:
                    self.logger.warning(
                        f"Failed to parse date '{m.group(0)}' with format '{fmt}' in header '{header}': {e}"
                    )
                    date = None
                    date_match = None
                break

        # Find purpose code (if present)
        purpose = self.PURPOSE_OTHER
        purpose_match = None
        for tok in [
            self.PURPOSE_BD,
            self.PURPOSE_AD,
            self.PURPOSE_TEMPLATE,
            self.PURPOSE_STUDY,
            self.PURPOSE_DESIGN,
            self.PURPOSE_PRECON_PS,
            self.PURPOSE_PRECON_INFO,
            self.PURPOSE_PREPLACE,
            self.PURPOSE_PRESTORM,
            self.PURPOSE_POSTPLACE,
            self.PURPOSE_POSTSTORM,
            self.PURPOSE_POSTPLACE2,
            self.PURPOSE_ANNUAL,
            self.PURPOSE_PRESTORM2,
            self.PURPOSE_POSTSTORM2,
        ]:
            match = re.search(rf"\b{re.escape(tok)}\b", header, re.IGNORECASE)
            if match:
                purpose = tok
                purpose_match = match
                break

        # Extract profile name by removing known components
        # Start with the full header
        remaining = header

        # Remove date if found
        if date_match:
            remaining = (
                remaining[: date_match.start()] + remaining[date_match.end() :]
            )

        # Remove purpose if found
        if purpose_match:
            remaining = (
                remaining[: purpose_match.start()]
                + remaining[purpose_match.end() :]
            )

        # The remaining text is the profile name (may contain spaces)
        profile_name = remaining.strip()

        # If profile name is empty, use first word from original header as fallback
        if not profile_name:
            parts = header.split()
            profile_name = parts[0] if parts else ""

        # Description is original header minus profile name
        desc = header
        if profile_name and profile_name in desc:
            # Remove first occurrence of profile name
            desc = desc.replace(profile_name, "", 1).strip()

        return profile_name, date, desc, purpose

    def read_profiles(self, filepath: str | Path) -> List[dict[str, Any]]:
        """Read profiles from a BMAP file.

        Args:
            filepath: Path to the BMAP file

        Returns:
            List of profile dictionaries
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)

        with open(filepath, encoding="utf-8", errors="ignore") as fh:
            lines = [ln.strip() for ln in fh if ln.strip()]

        profiles = []
        i = 0
        while i < len(lines):
            header = lines[i]
            i += 1
            if i >= len(lines):
                break
            try:
                count = int(lines[i])
            except ValueError as e:
                self.logger.warning(
                    f"Invalid point count '{lines[i]}' in BMAP file {filepath}, skipping profile: {e}"
                )
                continue
            i += 1
            data_pairs = []
            for _ in range(count):
                if i >= len(lines):
                    break
                try:
                    a, b = lines[i].split()[:2]
                    data_pairs.append((float(a), float(b)))
                except (ValueError, IndexError) as e:
                    self.logger.warning(
                        f"Invalid coordinate pair '{lines[i]}' in BMAP file {filepath}, skipping point: {e}"
                    )
                    pass
                i += 1

            profile_name, date, desc, purpose = self.parse_header(header)
            profiles.append(
                {
                    "profile_name": profile_name,
                    "date": date,
                    "description": desc,
                    "purpose": purpose,
                    "data": data_pairs,
                    "original_header": header,
                    "source_format": "BMAP",
                }
            )

        return profiles

    def parse_file(self, file_path: str | Path) -> List[Profile]:
        """Parse a BMAP file and extract beach profile data.

        Args:
            file_path: Path to the BMAP file

        Returns:
            List of Profile objects

        Raises:
            BeachProfileError: If parsing fails
        """
        try:
            # Read profiles from BMAP file
            profile_data_list = self.read_profiles(file_path)

            profiles = []
            for profile_data in profile_data_list:
                profile = self._convert_to_profile(profile_data)
                if profile:
                    profiles.append(profile)

            return profiles

        except Exception as e:
            raise BeachProfileError(
                f"Failed to parse BMAP file: {e}",
                category=ErrorCategory.FILE_IO,
            ) from e

    def _convert_to_profile(
        self, profile_data: dict[str, Any]
    ) -> Optional[Profile]:
        """Convert profile data dictionary to Profile object.

        Args:
            profile_data: Profile data from BMAP parser

        Returns:
            Profile object or None if invalid
        """
        try:
            profile_name = profile_data.get("profile_name", "").strip()
            if not profile_name:
                profile_name = f"bmap_profile_{uuid.uuid4().hex[:8]}"

            # Extract coordinates from data pairs (x, z)
            data_pairs = profile_data.get("data", [])
            if not data_pairs:
                self.logger.warning(
                    f"No coordinate data found for profile {profile_name}"
                )
                return None

            x_coords = []
            z_coords = []
            for x, z in data_pairs:
                x_coords.append(x)
                z_coords.append(z)

            # Validate coordinate arrays
            x_array = np.array(x_coords, dtype=float)
            z_array = np.array(z_coords, dtype=float)

            x_validation = validate_array_properties(
                x_array, "x_coordinates", allow_nan=False
            )
            z_validation = validate_array_properties(
                z_array, "z_coordinates", allow_nan=False
            )

            if x_validation or z_validation:
                all_errors = x_validation + z_validation
                self.logger.warning(
                    f"Coordinate validation errors for profile {profile_name}: {all_errors}"
                )
                # Continue processing but log the issues

            # Create metadata
            metadata: dict[str, Any] = {
                "source_format": "BMAP",
                "original_header": profile_data.get("original_header", ""),
                "purpose": profile_data.get("purpose", ""),
            }

            # Add date if available
            date = profile_data.get("date")
            date_str = None
            if date:
                date_str = date.strftime("%Y-%m-%d")
                metadata["survey_date"] = date_str

            # Create description from available info
            description_parts = []
            desc = profile_data.get("description", "").strip()
            if desc:
                description_parts.append(desc)
            purpose = profile_data.get("purpose", "")
            if purpose:
                description_parts.append(f"Purpose: {purpose}")

            description = (
                "; ".join(description_parts) if description_parts else None
            )

            profile = Profile(
                name=profile_name,
                date=date_str,
                description=description,
                x=x_array,
                z=z_array,
                metadata=metadata,
            )

            return profile

        except Exception as e:
            self.logger.error(
                f"Failed to convert profile data to Profile object: {e}"
            )
            return None


def read_bmap_profiles(
    file_path: str | Path, config: dict[str, Any] | None = None
) -> List[Profile]:
    """Read beach profile data from a BMAP file.

    Args:
        file_path: Path to the BMAP file
        config: Optional configuration for parsing

    Returns:
        List of Profile objects

    Raises:
        BeachProfileError: If reading fails
    """
    parser = BMAPParser(config)
    return parser.parse_file(file_path)


# Legacy BMAP free format functions (for backward compatibility)


def is_header_line(line: str) -> bool:
    """
    Returns True if a line likely marks the start of a new profile block.

    Improved logic to correctly identify headers vs coordinates:
    - Headers: Multi-part lines (profile name + optional date/description)
    - Count lines: Single integer numbers
    - Coordinate lines: Two numeric values (X Z coordinates)
    """
    if not line.strip():
        return False

    parts = line.strip().split()

    # If only one part, check if it's a count (single integer)
    if len(parts) == 1:
        return not parts[
            0
        ].isdigit()  # If it's not a digit, it might be a header

    # If exactly two parts, check if they're both numeric (coordinate pair)
    if len(parts) == 2:
        try:
            float(parts[0])
            float(parts[1])
            return False  # Two numbers = coordinate line, not header
        except ValueError:
            pass  # Not numeric, could be header

    # Multi-part lines are likely headers (unless they're all numbers)
    # Headers typically have profile names that may include numbers but also text
    return True


def parse_header(line: str):
    """
    Parse a BMAP free-format header line.

    Expected: <ProfileName> [<Date>] [<Description...>]

    Profile names may contain spaces. This parser:
    1. Extracts known date patterns (DDMMMYYYY, YYYY-MM-DD, MM/DD/YYYY)
    2. Extracts "from_filename" identifiers
    3. Treats remaining text as the profile name

    Returns (name, date, description)

    Examples:
        "OC 117 15AUG2020" → ("OC 117", "15AUG2020", "")
        "Site Name 01/01/2020 Description" → ("Site Name", "01/01/2020", "Description")
        "OC 117 from_test" → ("OC 117", None, "from_test")
    """
    line = line.strip()
    if not line:
        return None, None, None

    # Find and extract date pattern
    date = None
    date_match = None
    for pat in [
        r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
        r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
        r"\d{2}[A-Za-z]{3}\d{4}",  # DDMMMYYYY
    ]:
        match = re.search(pat, line)
        if match:
            date = match.group(0)
            date_match = match
            break

    # Remove date from line if found
    remaining = line
    if date_match:
        remaining = (
            remaining[: date_match.start()] + remaining[date_match.end() :]
        )

    # Check for "from_filename" pattern (added by writer when no date available)
    from_pattern = r"\bfrom_\w+"
    from_match = re.search(from_pattern, remaining)
    desc_parts = []

    if from_match:
        # "from_filename" becomes part of description
        desc_parts.append(from_match.group(0))
        # Remove from_filename from remaining
        remaining = (
            remaining[: from_match.start()] + remaining[from_match.end() :]
        )

    # What's left is the profile name
    name = remaining.strip()

    # If name is empty, use first word from original line as fallback
    if not name:
        parts = line.split()
        name = parts[0] if parts else None  # type: ignore[assignment]

    # Build description from collected parts
    desc = " ".join(desc_parts) if desc_parts else None

    return name, date, desc


def _convert_parsed_file_to_profiles(parsed_file: ParsedFile) -> List[Profile]:
    """
    Convert a ParsedFile object to the legacy Profile format expected by existing tools.

    Args:
        parsed_file: ParsedFile from the centralized parser

    Returns:
        List of Profile objects in the legacy format
    """
    profiles = []

    for profile_dict in parsed_file.profiles:
        # Extract profile name/ID
        name = profile_dict.get("profile_id", "UNKNOWN")

        # Extract date if available
        date = profile_dict.get("date")

        # Create description from available metadata
        desc_parts = []
        if profile_dict.get("purpose"):
            desc_parts.append(profile_dict["purpose"])
        if profile_dict.get("raw_header"):
            desc_parts.append(profile_dict["raw_header"])
        desc = " ".join(desc_parts) if desc_parts else None

        # Extract coordinates
        coordinates = profile_dict.get("coordinates", [])
        if coordinates:
            # Convert coordinate dicts to separate x, z arrays
            x_vals = []
            z_vals = []

            for coord in coordinates:
                if "x" in coord and "y" in coord:
                    x_vals.append(coord["x"])
                    # For BMAP format, we typically use Y as Z (elevation)
                    z_vals.append(coord.get("z", coord.get("y", 0)))
                elif "x" in coord and "z" in coord:
                    x_vals.append(coord["x"])
                    z_vals.append(coord["z"])

            if x_vals and z_vals:
                profiles.append(
                    Profile(
                        name=name,
                        date=date,
                        description=desc,
                        x=np.array(x_vals, dtype=float),
                        z=np.array(z_vals, dtype=float),
                        metadata=profile_dict.get("metadata"),
                    )
                )

    return profiles


def read_bmap_freeformat(file_path: str) -> List[Profile]:
    """
    Reads a BMAP Free Format file with one or more profiles.
    Automatically corrects for mismatched point counts.

    Now uses the centralized format detection and parsing system.
    """
    # Use the centralized parser
    parsed_file = parse_file_centralized(
        Path(file_path), skip_confirmation=True
    )

    # Convert to legacy Profile format
    return _convert_parsed_file_to_profiles(parsed_file)


def write_bmap_profiles(
    profiles: List[Profile],
    file_path: str | Path,
    source_filename: Optional[str] = None,
) -> None:
    """Write beach profile data to a BMAP file.

    Args:
        profiles: List of Profile objects to write
        file_path: Path where to write the BMAP file
        source_filename: Optional source filename for date extraction fallback

    Raises:
        BeachProfileError: If writing fails
    """
    try:
        # Try to extract date from source filename if provided
        filename_date = (
            extract_date_from_filename(source_filename)
            if source_filename
            else None
        )
        filename_identifier = None
        if source_filename and not filename_date:
            basename = (
                Path(source_filename).stem.replace(" ", "_").replace("-", "_")
            )
            filename_identifier = f"from_{basename}"

        with open(file_path, "w") as f:
            for profile in profiles:
                # Write header line: profile_name [date] [description]
                header_parts = [profile.name]

                # Priority 1: Use profile.date if available
                date_added = False
                if profile.date:
                    formatted_date = format_date_for_bmap(profile.date)
                    if formatted_date:
                        header_parts.append(formatted_date)
                        date_added = True

                # Priority 2: Use date from source filename
                if not date_added and filename_date:
                    header_parts.append(filename_date)
                    date_added = True

                # Priority 3: Add filename identifier if no date found
                if not date_added and filename_identifier:
                    header_parts.append(filename_identifier)

                # Add description if present
                if profile.description:
                    header_parts.append(profile.description)

                f.write(" ".join(header_parts) + "\n")

                # Write point count
                f.write(f"{len(profile.x)}\n")

                # Write coordinate pairs
                for x, z in zip(profile.x, profile.z):
                    f.write(f"{x:.3f} {z:.3f}\n")

                # Add blank line between profiles
                f.write("\n")

    except Exception as e:
        raise BeachProfileError(
            f"Failed to write BMAP file {file_path}: {e}",
            category=ErrorCategory.FILE_IO,
        )

"""
9-Column I/O Module for Beach Profile Data

This module provides functionality to read 9-column ASCII format files containing
beach profile survey data. 9-column files contain survey points with coordinates
and elevations that form profile line surveys.

Supported 9-column features:
- Multiple profiles per file (grouped by PROFILE ID and DATE)
- Survey metadata (date, time, point numbers)
- 3D coordinates (Easting, Northing, Elevation)
- Point types and descriptions
"""

import os
import uuid
from io import StringIO
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
import pandas as pd

from .bmap_io import Profile
from .data_validation import validate_array_properties
from .error_handler import (
    BeachProfileError,
    ErrorCategory,
    LogComponent,
    get_logger,
)


class NineColImportError(Exception):
    """Raised when 9-column import fails."""

    pass


class NineColumnParser:
    """Parser for 9-column ASCII files.

    Handles the parsing of 9-column format files containing beach profile
    survey points. Files have a header row followed by data rows with
    survey information and coordinates.
    """

    required_columns = [
        "PROFILE ID",
        "DATE",
        "TIME (EST)",
        "POINT #",
        "EASTING (X)",
        "NORTHING (Y)",
        "ELEVATION (Z)",
        "TYPE",
        "DESCRIPTION",
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the 9-column parser.

        Args:
            config: Optional configuration dictionary for parsing options
        """
        self.config = config or {}
        self.logger = get_logger(LogComponent.FILE_IO)

    def parse_9col_file(self, filepath: str | Path) -> pd.DataFrame:
        """Parse a 9-column ASCII file.

        Args:
            filepath: Path to the 9-column file

        Returns:
            DataFrame with parsed data

        Raises:
            BeachProfileError: If parsing fails
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)

        with open(filepath, encoding="utf-8", errors="ignore") as fh:
            lines = fh.readlines()

        header_idx = None
        for i, ln in enumerate(lines):
            if "PROFILE ID" in ln:
                header_idx = i
                break

        if header_idx is None:
            raise BeachProfileError(
                "Could not find header row containing 'PROFILE ID'",
                category=ErrorCategory.FILE_IO,
            )

        # Use the header line to name columns. Some inputs have spaces after
        # commas which results in column names with leading/trailing
        # whitespace (e.g. ' DATE'). Strip whitespace from column names so
        # they match the expected required column names.
        header_line = lines[header_idx].strip()
        content = header_line + "\n" + "".join(lines[header_idx + 1 :])
        df = pd.read_csv(StringIO(content), header=0)

        # Normalize column names by stripping surrounding whitespace.
        # Use Index.map to preserve the pandas Index type (avoids mypy complaint).
        df.columns = df.columns.map(
            lambda c: c.strip() if isinstance(c, str) else c
        )

        # Check for required columns
        missing_columns = set(self.required_columns) - set(df.columns)
        if missing_columns:
            raise BeachProfileError(
                f"Missing required columns: {missing_columns}",
                category=ErrorCategory.FILE_IO,
            )

        return df

    def parse_file(self, file_path: str | Path) -> List[Profile]:
        """Parse a 9-column file and extract beach profile data.

        Args:
            file_path: Path to the 9-column file

        Returns:
            List of Profile objects

        Raises:
            BeachProfileError: If parsing fails
        """
        try:
            # Parse the 9-column file
            df = self.parse_9col_file(file_path)

            # Group by profile and date to create profiles
            profiles = []
            grouped = df.groupby(["PROFILE ID", "DATE"])

            for (profile_id, date_str), profile_points in grouped:
                profile = self._convert_to_profile(
                    profile_id, date_str, profile_points
                )
                if profile:
                    profiles.append(profile)

            return profiles

        except (ValueError, TypeError, OSError, KeyError, IndexError) as e:
            raise BeachProfileError(
                f"Failed to parse 9-column file: {e}",
                category=ErrorCategory.FILE_IO,
            ) from e

    def _convert_to_profile(
        self, profile_id: str, date_str: str, profile_points: pd.DataFrame
    ) -> Optional[Profile]:
        """Convert grouped profile data to Profile object.

        Args:
            profile_id: Profile identifier
            date_str: Date string
            profile_points: DataFrame with points for this profile

        Returns:
            Profile object or None if invalid
        """
        try:
            # Clean profile ID
            profile_name = str(profile_id).strip()
            if not profile_name:
                profile_name = f"9col_profile_{uuid.uuid4().hex[:8]}"

            # Parse date
            date_obj = None
            try:
                if (
                    len(str(date_str).strip()) == 8
                    and str(date_str).strip().isdigit()
                ):
                    # YYYYMMDD format
                    date_obj = pd.to_datetime(
                        str(date_str).strip(), format="%Y%m%d"
                    )
                else:
                    date_obj = pd.to_datetime(date_str)
            except (ValueError, TypeError) as e:
                self.logger.warning(
                    f"Could not parse date '{date_str}' for profile {profile_name}: {e}"
                )

            date_str_formatted = (
                date_obj.strftime("%Y-%m-%d") if date_obj else None
            )

            # Sort points by point number
            profile_points = profile_points.sort_values("POINT #")

            # Extract coordinates
            x_coords = np.array(
                profile_points["EASTING (X)"].values, dtype=float
            )
            y_coords = np.array(
                profile_points["NORTHING (Y)"].values, dtype=float
            )
            z_coords = np.array(
                profile_points["ELEVATION (Z)"].values, dtype=float
            )

            if len(x_coords) == 0:
                self.logger.warning(
                    f"No coordinate data found for profile {profile_name}"
                )
                return None

            # Validate coordinate arrays
            x_validation = validate_array_properties(
                x_coords, "x_coordinates", allow_nan=False
            )
            z_validation = validate_array_properties(
                z_coords, "z_coordinates", allow_nan=False
            )

            if x_validation or z_validation:
                all_errors = x_validation + z_validation
                self.logger.warning(
                    f"Coordinate validation errors for profile {profile_name}: {all_errors}"
                )
                # Continue processing but log the issues

            # Create metadata
            metadata: dict[str, Any] = {
                "source_format": "9-column",
                "survey_date": date_str_formatted,
                "point_count": len(profile_points),
                "y_coordinates": np.array(y_coords, dtype=float),
            }

            # Add point types and descriptions if available
            if "TYPE" in profile_points.columns:
                types = profile_points["TYPE"].fillna("").astype(str).tolist()
                metadata["point_types"] = types

            if "DESCRIPTION" in profile_points.columns:
                descriptions = (
                    profile_points["DESCRIPTION"]
                    .fillna("")
                    .astype(str)
                    .tolist()
                )
                metadata["point_descriptions"] = descriptions

            # Create description
            description = "9-column survey data"
            if date_str_formatted:
                description += f" - {date_str_formatted}"

            profile = Profile(
                name=profile_name,
                date=date_str_formatted,
                description=description,
                x=x_coords,
                z=z_coords,
                metadata=metadata,
            )

            return profile

        except (
            ValueError,
            TypeError,
            KeyError,
            IndexError,
            AttributeError,
        ) as e:
            self.logger.error(
                f"Failed to convert 9-column data to Profile object: {e}"
            )
            return None


def read_9col_profiles(
    file_path: str | Path, config: dict[str, Any] | None = None
) -> List[Profile]:
    """Read beach profile data from a 9-column ASCII file.

    Args:
        file_path: Path to the 9-column file
        config: Optional configuration for parsing

    Returns:
        List of Profile objects

    Raises:
        BeachProfileError: If reading fails
    """
    parser = NineColumnParser(config)
    return parser.parse_file(file_path)


def write_9col_profiles(
    profiles: List[Profile], file_path: str | Path
) -> None:
    """Write beach profile data to a 9-column ASCII file.

    Args:
        profiles: List of Profile objects to write
        file_path: Path where to write the 9-column file

    Raises:
        BeachProfileError: If writing fails
    """
    try:
        with open(file_path, "w") as f:
            # Write header
            f.write(
                "PROFILE ID\tDATE\tPOINT #\tEASTING (X)\tNORTHING (Y)\tELEVATION (Z)\tTYPE\tDESCRIPTION\n"
            )

            point_counter = 1

            for profile in profiles:
                # Get Y coordinates from metadata if available, otherwise use zeros
                y_coords = None
                if profile.metadata and "y_coordinates" in profile.metadata:
                    y_coords = profile.metadata["y_coordinates"]
                else:
                    y_coords = np.zeros_like(profile.x)

                # Ensure we have the right number of Y coordinates
                if len(y_coords) != len(profile.x):
                    y_coords = np.zeros_like(profile.x)

                # Get point types and descriptions from metadata if available
                point_types = [""] * len(profile.x)
                descriptions = [""] * len(profile.x)

                if profile.metadata:
                    if (
                        "point_types" in profile.metadata
                        and profile.metadata["point_types"]
                    ):
                        point_types = profile.metadata["point_types"][
                            : len(profile.x)
                        ]
                        point_types.extend(
                            [""] * (len(profile.x) - len(point_types))
                        )

                    if (
                        "point_descriptions" in profile.metadata
                        and profile.metadata["point_descriptions"]
                    ):
                        descriptions = profile.metadata["point_descriptions"][
                            : len(profile.x)
                        ]
                        descriptions.extend(
                            [""] * (len(profile.x) - len(descriptions))
                        )

                # Format date
                date_str = (
                    profile.date or "19000101"
                )  # Default date if none provided

                # Write each point
                for i, (x, y, z) in enumerate(
                    zip(profile.x, y_coords, profile.z)
                ):
                    point_type = point_types[i] if i < len(point_types) else ""
                    desc = descriptions[i] if i < len(descriptions) else ""

                    f.write(
                        f"{profile.name}\t{date_str}\t{point_counter}\t{x:.3f}\t{y:.3f}\t{z:.3f}\t{point_type}\t{desc}\n"
                    )
                    point_counter += 1

    except (OSError, ValueError, TypeError) as e:
        raise BeachProfileError(
            f"Failed to write 9-column file {file_path}: {e}",
            category=ErrorCategory.FILE_IO,
        ) from e

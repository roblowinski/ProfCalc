"""
CSV I/O Module for Beach Profile Data

This module provides functionality to read beach profile data from CSV
format files. CSV files are commonly used for storing tabular beach profile
survey data with columns representing different attributes like coordinates,
elevations, and metadata.

Supported CSV structures:
- Standard beach profile data with X, Y, Z coordinates
- Flexible column mapping for different CSV layouts
- Metadata columns for survey information
- Support for various delimiters and quote characters
"""

import uuid
from datetime import datetime
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
from .file_parser import ParsedFile
from .file_parser import parse_file as parse_file_centralized

# Type alias: mapping values may be a column name (str) or a list of extra column names
ColumnMapping = dict[str, str | list[str]]


class CSVImportError(Exception):
    """Exception raised when CSV import operations fail.

    This exception is raised when there are issues reading, parsing, or
    validating CSV files containing beach profile data. It provides
    detailed error information to help diagnose import problems.
    """

    pass


class CSVParser:
    """Parser for CSV beach profile data files.

    Handles the parsing and validation of CSV files containing beach profile
    survey data. Supports flexible column mapping for various CSV formats
    commonly used for beach profile data, including automatic detection of
    coordinate columns and metadata fields.

    The parser can handle CSV files with different column naming conventions
    and automatically maps them to standard internal representations. It
    supports both single-profile and multi-profile CSV files.

    Attributes:
        config: Optional configuration dictionary for parsing options.
        required_columns: List of column names that must be present in the CSV.
        optional_columns: List of optional column names for metadata.
        logger: Logger instance for recording parsing operations and errors.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the CSV parser.

        Args:
            config: Optional configuration dictionary for parsing options.
                Currently unused but reserved for future customization.
        """
        self.config = config or {}
        self.required_columns = ["x", "y"]  # At minimum need coordinates
        self.optional_columns = [
            "z",
            "profile_id",
            "survey_date",
            "surveyor",
            "project",
            "point_number",
            "description",
        ]
        self.logger = get_logger(LogComponent.FILE_IO)

    def parse_file(self, file_path: str | Path) -> List[Profile]:
        """Parse a CSV file and extract beach profile data.

        Reads a CSV file, automatically detects column mappings, validates
        required columns, and converts the data into Profile objects. Supports
        both single-profile files (all data treated as one profile) and
        multi-profile files (grouped by profile_id column).

        Args:
            file_path: Path to the CSV file to parse. Can be a string or Path object.

        Returns:
            List of Profile objects extracted from the CSV file. Each profile
            contains coordinate data and associated metadata.

        Raises:
            BeachProfileError: If the file cannot be read, parsed, or contains
                invalid data structure (missing required columns, empty file, etc.).
        """
        try:
            # Read CSV file with pandas
            df = pd.read_csv(file_path)

            if df.empty:
                raise BeachProfileError(
                    "CSV file is empty", category=ErrorCategory.FILE_IO
                )

            # Detect column mapping
            column_mapping = self._detect_column_mapping(df.columns.tolist())

            # Validate required columns
            missing_cols = []
            for req_col in self.required_columns:
                if req_col not in column_mapping:
                    missing_cols.append(req_col)

            if missing_cols:
                raise BeachProfileError(
                    f"Missing required columns: {', '.join(missing_cols)}. "
                    f"Available columns: {', '.join(df.columns)}",
                    category=ErrorCategory.FILE_IO,
                )

            # Parse profiles from CSV data
            profiles = self._parse_csv_data(df, column_mapping)

            return profiles

        except pd.errors.EmptyDataError as e:
            raise BeachProfileError(
                "CSV file is empty or contains no valid data",
                category=ErrorCategory.FILE_IO,
            ) from e
        except pd.errors.ParserError as e:
            raise BeachProfileError(
                f"Failed to parse CSV file: {e}",
                category=ErrorCategory.FILE_IO,
            ) from e
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            IndexError,
            AttributeError,
        ) as e:
            raise BeachProfileError(
                f"Unexpected error parsing CSV file: {e}",
                category=ErrorCategory.FILE_IO,
            ) from e

    def _detect_column_mapping(self, columns: list[str]) -> ColumnMapping:
        """Detect column mapping from CSV headers.

        Args:
            columns: List of column names from CSV

        Returns:
            Dictionary mapping standard names to actual column names
            (values are str for standard mapped columns, and list[str] for "_extra_columns")
        """
        mapping: ColumnMapping = {}
        columns_lower = [col.lower().strip() for col in columns]

        # Common column name variations
        # Note: More specific patterns first to avoid false matches
        column_patterns = {
            "profile_id": [
                "profile_id",
                "profile",
                "prof_id",
                "id",
                "profile_name",
            ],
            "survey_date": [
                "survey_date",
                "date",
                "surveydate",
                "collection_date",
            ],
            "surveyor": ["surveyor", "survey_by", "operator"],
            "project": ["project", "project_name", "proj_name"],
            "point_number": ["point_number", "point", "pt_num", "pt"],
            "description": ["description", "desc", "notes"],
            "x": [
                "x",
                "longitude",
                "lon",
                "easting",
                "east",
                "coord_x",
                "cross_shore",
                "utm_x",
                "utmx",
                "utm_easting",
                "state_plane_x",
                "spx",
                "sp_x",
                "x_coord",
                "x_coordinate",
                "xcoord",
            ],
            "y": [
                "y",
                "latitude",
                "lat",
                "northing",
                "north",
                "coord_y",
                "along_shore",
                "utm_y",
                "utmy",
                "utm_northing",
                "state_plane_y",
                "spy",
                "sp_y",
                "y_coordinate",
                "ycoord",
            ],
            "z": [
                "z",
                "elevation",
                "elev",
                "height",
                "depth",
                "coord_z",
                "z_coord",
                "z_coordinate",
                "zcoord",
                "altitude",
                "alt",
            ],
        }

        for standard_name, patterns in column_patterns.items():
            matched_columns = []  # Track all matching columns for this coordinate

            for i, col_lower in enumerate(columns_lower):
                # Use exact match for single-letter coordinates to avoid false positives
                if standard_name in ["x", "y", "z"]:
                    if col_lower == standard_name or any(
                        pattern == col_lower for pattern in patterns
                    ):
                        matched_columns.append((columns[i], i))
                else:
                    if any(pattern in col_lower for pattern in patterns):
                        matched_columns.append((columns[i], i))

            # If multiple columns match, warn about ambiguity
            if len(matched_columns) > 1:
                col_names = [col for col, _ in matched_columns]
                print(
                    f"⚠️  WARNING: Multiple columns match '{standard_name}' coordinate:"
                )
                print(f"   Matched columns: {', '.join(col_names)}")
                print(f"   Using first match: '{matched_columns[0][0]}'")
                print(
                    "   To avoid ambiguity, consider renaming columns or removing duplicates.\n"
                )

            # Use first match (or none if no matches)
            if matched_columns:
                mapping[standard_name] = matched_columns[0][0]

        # Detect extra columns (not in standard patterns)
        standard_cols = set(mapping.values())
        extra_cols = [col for col in columns if col not in standard_cols]
        if extra_cols:
            mapping["_extra_columns"] = (
                extra_cols  # Store list[str] under special key
            )

        return mapping

    def _parse_csv_data(
        self, df: pd.DataFrame, column_mapping: ColumnMapping
    ) -> List[Profile]:
        """Parse CSV data into Profile objects.

        Args:
            df: Pandas DataFrame with CSV data
            column_mapping: Mapping of standard names to column names

        Returns:
            List of Profile objects
        """
        profiles = []

        # Group by profile_id if available
        profile_groups: Any
        if "profile_id" in column_mapping and isinstance(
            column_mapping["profile_id"], str
        ):
            profile_groups = df.groupby(column_mapping["profile_id"])
        else:
            # If no profile_id, treat entire file as one profile
            profile_groups = [("default_profile", df)]

        for profile_id, profile_df in profile_groups:
            profile = self._parse_single_profile(
                profile_df, column_mapping, str(profile_id)
            )
            if profile:
                profiles.append(profile)

        return profiles

    def _parse_single_profile(
        self, df: pd.DataFrame, column_mapping: ColumnMapping, profile_id: str
    ) -> Optional[Profile]:
        """Parse a single profile from CSV data.

        Args:
            df: DataFrame for this profile
            column_mapping: Column mapping dictionary
            profile_id: Profile identifier

        Returns:
            Profile object or None if invalid
        """
        try:
            # Extract metadata
            metadata: dict[str, Any] = {}
            if "survey_date" in column_mapping and isinstance(
                column_mapping["survey_date"], str
            ):
                survey_date_str: Any = df[column_mapping["survey_date"]].iloc[
                    0
                ]  # type: ignore
                if pd.notna(survey_date_str):  # type: ignore
                    metadata["survey_date"] = self._parse_date(
                        str(survey_date_str)
                    )

            for col in ["surveyor", "project"]:
                if col in column_mapping and isinstance(
                    column_mapping[col], str
                ):
                    val: Any = df[column_mapping[col]].iloc[0]  # type: ignore
                    if pd.notna(val):  # type: ignore
                        metadata[col] = str(val)

            # Set default profile_id if not provided
            if profile_id == "default_profile":
                profile_id = f"csv_profile_{uuid.uuid4().hex[:8]}"

            # Check for extra columns
            extra_val = column_mapping.get("_extra_columns")
            if isinstance(extra_val, list):
                extra_column_names: list[str] = extra_val
            else:
                extra_column_names = []

            # Collect coordinate arrays and extra data
            x_coords = []
            y_coords = []
            z_coords = []
            extra_data: list[list] = []

            for row_num, (idx, row) in enumerate(df.iterrows()):
                try:
                    point = self._parse_point(row, column_mapping, row_num + 1)
                    if point:
                        x_coords.append(point["x"])
                        y_coords.append(point["y"])
                        z_coords.append(point["z"])

                        # Collect extra columns
                        if extra_column_names:
                            extra_values: list = []
                            for col_name in extra_column_names:
                                # row.get works with Pandas Series
                                # Removed unused variable `extra_value`
                                # Ensure val is a scalar if it's a Series
                                if isinstance(val, pd.Series):
                                    val = val.iloc[0] if len(val) > 0 else None
                                if pd.notna(val):  # type: ignore
                                    # Try to convert to float, otherwise keep as string
                                    try:
                                        extra_values.append(float(val))
                                    except (ValueError, TypeError):
                                        extra_values.append(str(val))
                                else:
                                    extra_values.append(None)
                            extra_data.append(extra_values)

                except (ValueError, TypeError) as e:
                    self.logger.warning(
                        f"Skipping invalid point at row {idx}: {e}"
                    )
                    continue

            if not x_coords:
                self.logger.warning(
                    f"No valid points found for profile {profile_id}"
                )
                return None

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
                    f"Coordinate validation errors for profile {profile_id}: {all_errors}"
                )
                # Continue processing but log the issues

            # Create Profile object
            # Use profile_id as name
            date_str = survey_date_str if survey_date_str else None
            description = None
            if "surveyor" in metadata or "project" in metadata:
                desc_parts = []
                if "surveyor" in metadata:
                    desc_parts.append(f"Surveyor: {metadata['surveyor']}")
                if "project" in metadata:
                    desc_parts.append(f"Project: {metadata['project']}")
                description = "; ".join(desc_parts)

            # Add y_coords to metadata
            metadata["y_coordinates"] = np.array(y_coords, dtype=float)

            # Add extra columns to metadata if present
            if extra_column_names and extra_data:
                metadata["extra_columns"] = {
                    "names": extra_column_names,
                    "data": extra_data,
                }

            profile = Profile(
                name=profile_id,
                date=date_str,
                description=description,
                x=x_array,
                z=z_array,
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
            self.logger.error(f"Failed to parse profile {profile_id}: {e}")
            return None

    def _parse_point(
        self, row: pd.Series, column_mapping: ColumnMapping, row_idx: int
    ) -> dict[str, Any] | None:
        """Parse a single point from a CSV row.

        Args:
            row: Pandas Series representing the row
            column_mapping: Column mapping dictionary
            row_idx: Row index for error reporting

        Returns:
            Point data dictionary or None if invalid
        """
        try:
            # Extract coordinates
            if not isinstance(column_mapping.get("x"), str) or not isinstance(
                column_mapping.get("y"), str
            ):
                raise ValueError(
                    "Column mapping must contain 'x' and 'y' string mappings"
                )

            assert isinstance(column_mapping["x"], str)
            assert isinstance(column_mapping["y"], str)
            x_val: Any = row[column_mapping["x"]]
            x = float(x_val) if pd.notna(x_val) else 0.0  # type: ignore

            y_val: Any = row[column_mapping["y"]]
            y = float(y_val) if pd.notna(y_val) else 0.0  # type: ignore

            z = 0.0
            if "z" in column_mapping and isinstance(column_mapping["z"], str):
                z_val: Any = row[column_mapping["z"]]
                if pd.notna(z_val):  # type: ignore
                    z = float(z_val)  # type: ignore

            return {"x": x, "y": y, "z": z}

        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(
                f"Invalid coordinate data in row {row_idx}: {e}. "
                f"Row data: {row.to_dict() if hasattr(row, 'to_dict') else dict(row)}"
            ) from e

    def _parse_date(self, date_str: str) -> str:
        """Parse date string into standardized string format.

        Args:
            date_str: Date string in various formats

        Returns:
            Parsed date string in YYYY-MM-DD format

        Raises:
            BeachProfileError: If date format is invalid
        """
        if pd.isna(date_str):
            return datetime.now().strftime("%Y-%m-%d")

        if isinstance(date_str, datetime):
            return date_str.strftime("%Y-%m-%d")

        if not date_str or date_str.strip() == "":
            return datetime.now().strftime("%Y-%m-%d")

        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        raise BeachProfileError(
            f"Invalid date format: '{date_str}'. "
            f"Supported formats: {', '.join(formats)}",
            category=ErrorCategory.VALIDATION,
        )


def _convert_parsed_file_to_profiles(parsed_file: ParsedFile) -> List[Profile]:
    """Convert a ParsedFile object to the legacy Profile format.

    Converts data from the centralized parsing system (ParsedFile) to the
    legacy Profile format expected by existing analysis tools. This function
    bridges the gap between the new unified parsing system and legacy code.

    Args:
        parsed_file: ParsedFile object from the centralized parser containing
            standardized profile data.

    Returns:
        List of Profile objects in the legacy format with coordinate arrays
        and metadata. Only profiles with valid coordinate data are included.
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
        desc = " ".join(desc_parts) if desc_parts else None

        # Extract coordinates
        coordinates = profile_dict.get("coordinates", [])
        if coordinates:
            # Convert coordinate dicts to separate x, z arrays
            x_vals = []
            z_vals = []

            for coord in coordinates:
                if "x" in coord and "z" in coord:
                    x_vals.append(coord["x"])
                    z_vals.append(coord["z"])
                elif "x" in coord and "y" in coord:
                    # For CSV, Y might be elevation
                    x_vals.append(coord["x"])
                    z_vals.append(coord.get("z", coord.get("y", 0)))

            if x_vals and z_vals:
                # Validate arrays
                x_validation = validate_array_properties(
                    np.array(x_vals), "x_coordinates", allow_nan=False
                )
                z_validation = validate_array_properties(
                    np.array(z_vals), "z_coordinates", allow_nan=False
                )

                if (
                    not x_validation and not z_validation
                ):  # No validation errors
                    profiles.append(
                        Profile(
                            name=name,
                            date=date,
                            description=desc,
                            x=np.array(x_vals, dtype=float),
                            z=np.array(z_vals, dtype=float),
                        )
                    )

    return profiles


def read_csv_profiles(
    file_path: str | Path, config: dict[str, Any] | None = None
) -> List[Profile]:
    """Read beach profile data from a CSV file using centralized parsing.

    High-level function that reads beach profile data from CSV files using
    the centralized format detection and parsing system. Automatically
    detects file format and column structure, then converts to Profile objects.

    Args:
        file_path: Path to the CSV file to read. Can be a string or Path object.
        config: Optional configuration dictionary for parsing options.
            Currently unused but reserved for future customization.

    Returns:
        List of Profile objects containing the parsed beach profile data.

    Note:
        This function uses the centralized format detection and parsing system
        for robust handling of various CSV formats and automatic column detection.
    """
    # Use the centralized parser
    parsed_file = parse_file_centralized(
        Path(file_path), skip_confirmation=True
    )

    # Convert to legacy Profile format
    return _convert_parsed_file_to_profiles(parsed_file)


def write_csv_profiles(
    profiles: List[Profile],
    file_path: str | Path,
    config: dict[str, Any] | None = None,
) -> None:
    """Write beach profile data to a CSV file.

    Exports Profile objects to a CSV file with standardized column formatting.
    Includes coordinate data and metadata fields in a structured format.

    Args:
        profiles: List of Profile objects to export to CSV format.
        file_path: Path where the CSV file will be created. Can be a string
            or Path object.
        config: Optional configuration dictionary for output formatting options
            such as column ordering, precision, or additional metadata fields.

    Returns:
        None

    Raises:
        BeachProfileError: If the file cannot be written due to I/O errors,
            invalid profile data, or DataFrame conversion failures.
    """
    try:
        # Convert profiles to DataFrame
        df = _profiles_to_dataframe(profiles)

        # Apply any formatting from config
        if config:
            df = _format_csv_output(df, config)

        # Write to CSV
        df.to_csv(file_path, index=False, encoding="utf-8")

    except (OSError, ValueError, TypeError) as e:
        raise BeachProfileError(
            f"Failed to write CSV file: {e}", category=ErrorCategory.FILE_IO
        ) from e


def _profiles_to_dataframe(profiles: List[Profile]) -> pd.DataFrame:
    """Convert Profile objects to a pandas DataFrame.

    Args:
        profiles: List of Profile objects

    Returns:
        DataFrame with profile data
    """
    rows = []

    for profile in profiles:
        # Get metadata
        metadata = profile.metadata or {}
        # Check both 'y_coordinates' and 'y' for Y values
        y_coords = None
        if "y_coordinates" in metadata:
            y_coords = metadata["y_coordinates"]
        elif "y" in metadata:
            y_coords = metadata["y"]

        if y_coords is None:
            y_coords = [None] * len(profile.x)

        # Check for extra columns
        extra_columns_info = metadata.get("extra_columns")
        extra_col_names = []
        extra_col_data = []
        if extra_columns_info:
            extra_col_names = extra_columns_info.get("names", [])
            extra_col_data = extra_columns_info.get("data", [])

        # Create rows for each point
        for i in range(len(profile.x)):
            row = {
                "profile_id": profile.name,
                "survey_date": profile.date,
                "surveyor": metadata.get("surveyor", ""),
                "project": metadata.get("project", ""),
                "x": profile.x[i],
                "y": y_coords[i] if i < len(y_coords) else None,
                "z": profile.z[i],
                "point_number": i + 1,
            }

            # Add extra columns
            if extra_col_names and i < len(extra_col_data):
                for col_idx, col_name in enumerate(extra_col_names):
                    if col_idx < len(extra_col_data[i]):
                        row[col_name] = extra_col_data[i][col_idx]
                    else:
                        row[col_name] = None

            rows.append(row)

    return pd.DataFrame(rows)


def _format_csv_output(
    df: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Format the CSV output DataFrame based on configuration.

    Args:
        df: Raw DataFrame
        config: Formatting configuration

    Returns:
        Formatted DataFrame
    """
    # Handle missing values
    df = df.fillna("")

    # Format dates if present
    if "survey_date" in df.columns:
        df["survey_date"] = pd.to_datetime(
            df["survey_date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    # Format numeric columns
    numeric_columns = ["x", "y", "z"]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(3)

    # Column ordering
    preferred_order = [
        "profile_id",
        "survey_date",
        "surveyor",
        "project",
        "point_number",
        "x",
        "y",
        "z",
    ]
    existing_columns = [col for col in preferred_order if col in df.columns]
    other_columns = [col for col in df.columns if col not in existing_columns]
    df = df[existing_columns + other_columns]

    return df


def read_xyz_profiles(
    file_path: str | Path,
    origin_azimuth_file: str
    | Path = "src/profcalc/data/required_inputs/ProfileOriginAzimuths.csv",
    tolerance_ft: float = 25.0,
) -> List[Profile]:
    """Read XYZ coordinate data and assign points to profiles based on perpendicular distance.

    Reads XYZ files containing survey point coordinates (X, Y, Z) and automatically
    assigns each point to the nearest beach profile based on perpendicular distance
    to profile origin azimuth lines.

    Args:
        file_path: Path to the XYZ file (whitespace-separated, no header, 3 columns: X Y Z)
        origin_azimuth_file: Path to CSV file containing profile origin azimuth data
        tolerance_ft: Maximum perpendicular distance in feet for profile assignment

    Returns:
        List of Profile objects with assigned points

    Raises:
        BeachProfileError: If reading or assignment fails
    """
    try:
        # Read XYZ file (whitespace separated, no header)
        df = pd.read_csv(
            file_path,
            sep=r"\s+",
            header=None,
            names=["x", "y", "z"],
            engine="python",
        )

        # Validate basic structure
        if len(df.columns) != 3 or not all(
            col in df.columns for col in ["x", "y", "z"]
        ):
            raise BeachProfileError(
                f"XYZ file must have exactly 3 columns (X, Y, Z), found: {list(df.columns)}",
                category=ErrorCategory.VALIDATION,
            )

        # Check for missing values
        if df.isnull().any().any():
            null_counts = df.isnull().sum()
            null_rows = df[df.isnull().any(axis=1)]
            raise BeachProfileError(
                f"XYZ file contains missing values - all points must have valid X, Y, Z coordinates. "
                f"Null counts by column: {null_counts.to_dict()}. "
                f"First few rows with nulls: {null_rows.head(3).to_string() if len(null_rows) > 0 else 'None'}",
                category=ErrorCategory.VALIDATION,
            )

        # Load profile baselines
        origin_azimuths_df = _load_profile_origin_azimuths(origin_azimuth_file)

        # Assign points to profiles
        assigned_df = _assign_points_to_profiles_by_distance(
            df, origin_azimuths_df, tolerance_ft
        )

        # Group by profile and create Profile objects
        profiles = []
        for profile_id, group in assigned_df.groupby("profile_id"):
            # Sort by X coordinate for consistent ordering
            group = group.sort_values("x")

            # Create Profile object
            profile = Profile(
                name=str(profile_id),
                date=datetime.now().strftime("%Y-%m-%d"),
                description=f"Profile assigned from XYZ data within {tolerance_ft} ft tolerance",
                x=np.array(group["x"].values, dtype=float),
                z=np.array(group["z"].values, dtype=float),
                metadata={
                    "y_coordinates": np.array(group["y"].values, dtype=float),
                    "source_file": str(file_path),
                    "assignment_method": "perpendicular_distance",
                    "tolerance_ft": tolerance_ft,
                    "origin_azimuth_file": str(origin_azimuth_file),
                    "point_count": len(group),
                },
            )
            profiles.append(profile)

        # Log summary
        logger = get_logger(LogComponent.FILE_IO)
        assigned_count = len(assigned_df)
        unassigned_count = len(df) - assigned_count

        logger.info(
            f"XYZ profile assignment complete: {len(profiles)} profiles created, "
            f"{assigned_count} points assigned, {unassigned_count} points unassigned",
            extra={
                "profiles_created": len(profiles),
                "points_assigned": assigned_count,
                "points_unassigned": unassigned_count,
                "tolerance_ft": tolerance_ft,
            },
        )

        if unassigned_count > 0:
            logger.warning(
                f"{unassigned_count} points could not be assigned to any profile within {tolerance_ft} ft tolerance",
                extra={
                    "unassigned_count": unassigned_count,
                    "tolerance_ft": tolerance_ft,
                },
            )

        return profiles

    except FileNotFoundError as e:
        raise BeachProfileError(
            f"XYZ file not found: {file_path}", category=ErrorCategory.FILE_IO
        ) from e
    except pd.errors.EmptyDataError:
        raise BeachProfileError(
            f"XYZ file is empty: {file_path}", category=ErrorCategory.FILE_IO
        )
    except (OSError, ValueError, TypeError, KeyError, IndexError) as e:
        raise BeachProfileError(
            f"Failed to read XYZ file: {e}", category=ErrorCategory.FILE_IO
        ) from e


def _load_profile_origin_azimuths(
    origin_azimuth_file: str | Path,
) -> pd.DataFrame:
    """Load profile origin azimuth data from a CSV file.

    Args:
        origin_azimuth_file: Path to the origin azimuth CSV file

    Returns:
        DataFrame with origin azimuth profile data

    Raises:
        BeachProfileError: If loading fails
    """
    try:
        # Read origin azimuth data
        df = pd.read_csv(origin_azimuth_file)

        # Handle different possible column name formats
        column_mapping = {}

        # Map expected column names to actual column names
        possible_names = {
            "profile_id": ["profile_id", "profile_name", "Profile", "profile"],
            "azimuth": ["azimuth", "Azimuth", "az", "AZIMUTH"],
            "origin_x": ["origin_x", "Origin_X", "x0", "X0", "originx"],
            "origin_y": ["origin_y", "Origin_Y", "y0", "Y0", "originy"],
        }

        # Try to find columns using a permissive set of header variants.
        for expected_col, possible_cols in possible_names.items():
            found = None
            for actual_col in possible_cols:
                if actual_col in df.columns:
                    found = actual_col
                    break
                # also try case-insensitive match
                for c in df.columns:
                    if c.strip().lower() == actual_col.strip().lower():
                        found = c
                        break
                if found:
                    break

            if found:
                column_mapping[expected_col] = found

        # At minimum we must have a profile id column
        if "profile_id" not in column_mapping:
            # try to infer a profile id-like column
            for c in df.columns:
                if c.strip().lower() in (
                    "profile",
                    "profile_name",
                    "id",
                    "profileid",
                ):
                    column_mapping["profile_id"] = c
                    break

        if "profile_id" not in column_mapping:
            raise BeachProfileError(
                "Could not find a profile identifier column in origin azimuth file",
                category=ErrorCategory.VALIDATION,
            )

        # Rename columns to expected keys where present
        rename_map = {v: k for k, v in column_mapping.items()}
        df = df.rename(columns=rename_map)

        # Normalize numeric columns: strip commas/whitespace and coerce to numeric
        for numcol in ("origin_x", "origin_y", "azimuth"):
            if numcol in df.columns:
                # convert to string, strip thousands separators and whitespace
                df[numcol] = (
                    df[numcol]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .str.strip()
                    .replace({"nan": None})
                )
                df[numcol] = pd.to_numeric(df[numcol], errors="coerce")

        # If azimuth is provided in degrees-minutes as text or with weird chars,
        # pd.to_numeric will coerce to NaN; we leave NaN and let callers decide.

        return df

    except FileNotFoundError as e:
        raise BeachProfileError(
            f"Origin azimuth file not found: {origin_azimuth_file}",
            category=ErrorCategory.FILE_IO,
        ) from e
    except pd.errors.EmptyDataError:
        raise BeachProfileError(
            f"Origin azimuth file is empty: {origin_azimuth_file}",
            category=ErrorCategory.FILE_IO,
        )
    except (OSError, ValueError, TypeError, KeyError, IndexError) as e:
        raise BeachProfileError(
            f"Failed to load origin azimuth file: {e}",
            category=ErrorCategory.FILE_IO,
        ) from e


def _assign_points_to_profiles_by_distance(
    points_df: pd.DataFrame,
    origin_azimuths_df: pd.DataFrame,
    tolerance_ft: float,
) -> pd.DataFrame:
    """Assign survey points to profiles based on perpendicular distance to origin azimuths.

    Args:
        points_df: DataFrame with points (x, y, z)
        origin_azimuths_df: DataFrame with profile origin azimuths (profile_id, azimuth, origin_x, origin_y)
        tolerance_ft: Maximum distance in feet for assigning points to profiles

    Returns:
        DataFrame with points and assigned profile_id

    Raises:
        BeachProfileError: If assignment fails
    """
    from .coordinate_transforms import calculate_point_profile_offset

    tolerance_m = tolerance_ft * 0.3048  # Convert feet to meters
    assigned_profile_ids = []

    for _, point in points_df.iterrows():
        min_distance = float("inf")
        best_profile = None

        # Find the profile with minimum perpendicular distance
        for _, origin_azimuth in origin_azimuths_df.iterrows():
            distance = calculate_point_profile_offset(
                origin_azimuth["origin_x"],
                origin_azimuth["origin_y"],
                origin_azimuth["azimuth"],
                point["x"],
                point["y"],
            )
            if distance < min_distance:
                min_distance = distance
                best_profile = origin_azimuth["profile_id"]

        # Assign if within tolerance
        if min_distance <= tolerance_m:
            assigned_profile_ids.append(best_profile)
        else:
            assigned_profile_ids.append(None)  # Unassigned

    points_df = points_df.copy()
    points_df["profile_id"] = assigned_profile_ids

    # Remove unassigned points
    assigned_df = points_df.dropna(subset=["profile_id"])

    # Log unassigned points
    unassigned_count = len(points_df) - len(assigned_df)
    if unassigned_count > 0:
        logger = get_logger(LogComponent.FILE_IO)
        logger.warning(
            f"{unassigned_count} points could not be assigned to any profile within {tolerance_ft} ft tolerance",
            extra={
                "unassigned_count": unassigned_count,
                "tolerance_ft": tolerance_ft,
            },
        )

    return assigned_df

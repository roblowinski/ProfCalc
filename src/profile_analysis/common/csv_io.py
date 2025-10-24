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
from .error_handler import (
    BeachProfileError,
    ErrorCategory,
    LogComponent,
    get_logger,
    validate_array_properties,
)


class CSVImportError(Exception):
    """Raised when CSV import fails."""
    pass


class CSVParser:
    """Parser for CSV beach profile data files.

    Handles the parsing and validation of CSV files containing beach
    profile survey data. Supports flexible column mapping and various
    CSV formats commonly used for beach profile data.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the CSV parser.

        Args:
            config: Optional configuration dictionary for parsing options
        """
        self.config = config or {}
        self.required_columns = ['x', 'y']  # At minimum need coordinates
        self.optional_columns = ['z', 'profile_id', 'survey_date', 'surveyor', 'project']
        self.logger = get_logger(LogComponent.FILE_IO)

    def parse_file(self, file_path: str | Path) -> List[Profile]:
        """Parse a CSV file and extract beach profile data.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of Profile objects

        Raises:
            BeachProfileError: If parsing fails
        """
        try:
            # Read CSV file with pandas
            df = pd.read_csv(file_path)

            if df.empty:
                raise BeachProfileError("CSV file is empty", category=ErrorCategory.FILE_IO)

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
                    category=ErrorCategory.FILE_IO
                )

            # Parse profiles from CSV data
            profiles = self._parse_csv_data(df, column_mapping)

            return profiles

        except pd.errors.EmptyDataError as e:
            raise BeachProfileError("CSV file is empty or contains no valid data", category=ErrorCategory.FILE_IO) from e
        except pd.errors.ParserError as e:
            raise BeachProfileError(f"Failed to parse CSV file: {e}", category=ErrorCategory.FILE_IO) from e
        except Exception as e:
            raise BeachProfileError(f"Unexpected error parsing CSV file: {e}", category=ErrorCategory.FILE_IO) from e

    def _detect_column_mapping(self, columns: list[str]) -> dict[str, str]:
        """Detect column mapping from CSV headers.

        Args:
            columns: List of column names from CSV

        Returns:
            Dictionary mapping standard names to actual column names
        """
        mapping = {}
        columns_lower = [col.lower().strip() for col in columns]

        # Common column name variations
        column_patterns = {
            'x': ['x', 'longitude', 'lon', 'easting', 'east', 'coord_x', 'cross_shore'],
            'y': ['y', 'latitude', 'lat', 'northing', 'north', 'coord_y', 'along_shore'],
            'z': ['z', 'elevation', 'elev', 'height', 'depth', 'coord_z'],
            'profile_id': ['profile_id', 'profile', 'prof_id', 'id', 'profile_name'],
            'survey_date': ['survey_date', 'date', 'surveydate', 'collection_date'],
            'surveyor': ['surveyor', 'survey_by', 'operator'],
            'project': ['project', 'project_name', 'proj_name']
        }

        for standard_name, patterns in column_patterns.items():
            for i, col_lower in enumerate(columns_lower):
                if any(pattern in col_lower for pattern in patterns):
                    mapping[standard_name] = columns[i]
                    break

        return mapping

    def _parse_csv_data(self, df: pd.DataFrame, column_mapping: dict[str, str]) -> List[Profile]:
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
        if 'profile_id' in column_mapping:
            profile_groups = df.groupby(column_mapping['profile_id'])
        else:
            # If no profile_id, treat entire file as one profile
            profile_groups = [('default_profile', df)]

        for profile_id, profile_df in profile_groups:
            profile = self._parse_single_profile(profile_df, column_mapping, str(profile_id))
            if profile:
                profiles.append(profile)

        return profiles

    def _parse_single_profile(self, df: pd.DataFrame, column_mapping: dict[str, str], profile_id: str) -> Optional[Profile]:
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
            metadata = {}
            survey_date_str = None
            if 'survey_date' in column_mapping:
                survey_date_str = df[column_mapping['survey_date']].iloc[0]
                metadata['survey_date'] = self._parse_date(survey_date_str)

            for col in ['surveyor', 'project']:
                if col in column_mapping:
                    val = df[column_mapping[col]].iloc[0]
                    if pd.notna(val):
                        metadata[col] = str(val)

            # Set default profile_id if not provided
            if profile_id == 'default_profile':
                profile_id = f"csv_profile_{uuid.uuid4().hex[:8]}"

            # Collect coordinate arrays
            x_coords = []
            y_coords = []
            z_coords = []

            for row_num, (idx, row) in enumerate(df.iterrows()):
                try:
                    point = self._parse_point(row, column_mapping, row_num + 1)
                    if point:
                        x_coords.append(point['x'])
                        y_coords.append(point['y'])
                        z_coords.append(point['z'])
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Skipping invalid point at row {idx}: {e}")
                    continue

            if not x_coords:
                self.logger.warning(f"No valid points found for profile {profile_id}")
                return None

            # Validate coordinate arrays
            x_array = np.array(x_coords, dtype=float)
            z_array = np.array(z_coords, dtype=float)

            x_validation = validate_array_properties(x_array, "x_coordinates", allow_nan=False)
            z_validation = validate_array_properties(z_array, "z_coordinates", allow_nan=False)

            if x_validation or z_validation:
                all_errors = x_validation + z_validation
                self.logger.warning(f"Coordinate validation errors for profile {profile_id}: {all_errors}")
                # Continue processing but log the issues

            # Create Profile object
            # Use profile_id as name
            date_str = survey_date_str if survey_date_str else None
            description = None
            if 'surveyor' in metadata or 'project' in metadata:
                desc_parts = []
                if 'surveyor' in metadata:
                    desc_parts.append(f"Surveyor: {metadata['surveyor']}")
                if 'project' in metadata:
                    desc_parts.append(f"Project: {metadata['project']}")
                description = "; ".join(desc_parts)

            # Add y_coords to metadata
            metadata['y_coordinates'] = np.array(y_coords, dtype=float)  # type: ignore[assignment]

            profile = Profile(
                name=profile_id,
                date=date_str,
                description=description,
                x=x_array,
                z=z_array,
                metadata=metadata
            )

            return profile

        except Exception as e:
            self.logger.error(f"Failed to parse profile {profile_id}: {e}")
            return None

    def _parse_point(self, row: pd.Series, column_mapping: dict[str, str], row_idx: int) -> dict[str, Any] | None:
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
            x_val = row[column_mapping['x']]
            x = float(x_val) if pd.notna(x_val) else 0.0

            y_val = row[column_mapping['y']]
            y = float(y_val) if pd.notna(y_val) else 0.0

            z = 0.0
            if 'z' in column_mapping:
                z_val = row[column_mapping['z']]
                if pd.notna(z_val):
                    z = float(z_val)

            return {
                'x': x,
                'y': y,
                'z': z
            }

        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f"Invalid coordinate data: {e}") from e

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
            return datetime.now().strftime('%Y-%m-%d')

        if isinstance(date_str, datetime):
            return date_str.strftime('%Y-%m-%d')

        if not date_str or date_str.strip() == '':
            return datetime.now().strftime('%Y-%m-%d')

        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d'
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        raise BeachProfileError(f"Invalid date format: {date_str}", category=ErrorCategory.VALIDATION)


def read_csv_profiles(file_path: str | Path, config: dict[str, Any] | None = None) -> List[Profile]:
    """Read beach profile data from a CSV file.

    Args:
        file_path: Path to the CSV file
        config: Optional configuration for parsing

    Returns:
        List of Profile objects

    Raises:
        BeachProfileError: If reading fails
    """
    parser = CSVParser(config)
    return parser.parse_file(file_path)


def write_csv_profiles(profiles: List[Profile], file_path: str | Path, config: dict[str, Any] | None = None) -> None:
    """Write beach profile data to a CSV file.

    Args:
        profiles: List of Profile objects to write
        file_path: Path where the CSV file will be created
        config: Optional configuration for output formatting

    Raises:
        BeachProfileError: If writing fails
    """
    try:
        # Convert profiles to DataFrame
        df = _profiles_to_dataframe(profiles)

        # Apply any formatting from config
        if config:
            df = _format_csv_output(df, config)

        # Write to CSV
        df.to_csv(file_path, index=False, encoding='utf-8')

    except Exception as e:
        raise BeachProfileError(f"Failed to write CSV file: {e}", category=ErrorCategory.FILE_IO) from e


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
        y_coords = metadata.get('y_coordinates', [None] * len(profile.x))

        # Create rows for each point
        for i in range(len(profile.x)):
            row = {
                'profile_id': profile.name,
                'survey_date': profile.date,
                'surveyor': metadata.get('surveyor', ''),
                'project': metadata.get('project', ''),
                'x': profile.x[i],
                'y': y_coords[i] if i < len(y_coords) else None,
                'z': profile.z[i],
                'point_number': i + 1
            }
            rows.append(row)

    return pd.DataFrame(rows)


def _format_csv_output(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Format the CSV output DataFrame based on configuration.

    Args:
        df: Raw DataFrame
        config: Formatting configuration

    Returns:
        Formatted DataFrame
    """
    # Handle missing values
    df = df.fillna('')

    # Format dates if present
    if 'survey_date' in df.columns:
        df['survey_date'] = pd.to_datetime(df['survey_date'], errors='coerce').dt.strftime('%Y-%m-%d')

    # Format numeric columns
    numeric_columns = ['x', 'y', 'z']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').round(3)

    # Column ordering
    preferred_order = ['profile_id', 'survey_date', 'surveyor', 'project', 'point_number', 'x', 'y', 'z']
    existing_columns = [col for col in preferred_order if col in df.columns]
    other_columns = [col for col in df.columns if col not in existing_columns]
    df = df[existing_columns + other_columns]

    return df

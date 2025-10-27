"""
Generic Data Validation Utilities

This module provides reusable data validation functions that can be used across
different projects and data formats. Functions are designed to be generic and
configurable to work with various data types and validation requirements.

Key Features:
- Array and coordinate validation
- Data type checking
- Range and bounds validation
- Missing data detection
- Custom validation rules
"""

from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from .error_handler import (
    BeachProfileError,
    ErrorCategory,
    StructuredLogger,
)


def validate_array_properties(
    array: np.ndarray,
    name: str = "array",
    allow_nan: bool = True,
    allow_inf: bool = True,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    dtype: Optional[np.dtype] = None
) -> List[str]:
    """Validate basic properties of a numpy array.

    Args:
        array: Array to validate
        name: Name of the array for error messages
        allow_nan: Whether NaN values are allowed
        allow_inf: Whether infinite values are allowed
        min_length: Minimum required length
        max_length: Maximum allowed length
        dtype: Required data type

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check if it's actually a numpy array
    if not isinstance(array, np.ndarray):
        errors.append(f"{name} must be a numpy array, got {type(array)}")
        return errors

    # Check length constraints
    if min_length is not None and len(array) < min_length:
        errors.append(f"{name} length {len(array)} is below minimum {min_length}")

    if max_length is not None and len(array) > max_length:
        errors.append(f"{name} length {len(array)} exceeds maximum {max_length}")

    # Check data type
    if dtype is not None and array.dtype != dtype:
        try:
            # Try to cast to required dtype
            array.astype(dtype, copy=False)
        except (ValueError, TypeError):
            errors.append(f"{name} cannot be converted to required dtype {dtype}")

    # Check for NaN values
    if not allow_nan and np.any(np.isnan(array)):
        nan_count = np.sum(np.isnan(array))
        errors.append(f"{name} contains {nan_count} NaN values (not allowed)")

    # Check for infinite values
    if not allow_inf and np.any(np.isinf(array)):
        inf_count = np.sum(np.isinf(array))
        errors.append(f"{name} contains {inf_count} infinite values (not allowed)")

    return errors


def validate_coordinate_arrays(
    x_coords: np.ndarray,
    y_coords: Optional[np.ndarray] = None,
    z_coords: Optional[np.ndarray] = None,
    coord_system: str = "cartesian",
    bounds: Optional[Dict[str, Union[float, int]]] = None
) -> List[str]:
    """Validate coordinate arrays for common issues.

    Args:
        x_coords: X coordinate array
        y_coords: Y coordinate array (optional)
        z_coords: Z coordinate array (optional)
        coord_system: Coordinate system type ("cartesian", "geographic", "projected")
        bounds: Optional bounds checking {"x_min": val, "x_max": val, etc.}

    Returns:
        List of validation error messages
    """
    errors = []

    # Validate X coordinates
    x_errors = validate_array_properties(
        x_coords, "x_coords", allow_nan=False, allow_inf=False
    )
    errors.extend(x_errors)

    # Check coordinate system specific constraints
    if coord_system == "geographic":
        # Longitude bounds
        if np.any((x_coords < -180) | (x_coords > 180)):
            errors.append("X coordinates (longitude) must be between -180 and 180 degrees")
        # Y coordinates should be latitude
        if y_coords is not None and np.any((y_coords < -90) | (y_coords > 90)):
            errors.append("Y coordinates (latitude) must be between -90 and 90 degrees")

    # Validate Y coordinates if provided
    if y_coords is not None:
        y_errors = validate_array_properties(
            y_coords, "y_coords", allow_nan=False, allow_inf=False
        )
        errors.extend(y_errors)

        # Check array lengths match
        if len(y_coords) != len(x_coords):
            errors.append(f"Y coordinates length ({len(y_coords)}) doesn't match X coordinates ({len(x_coords)})")

    # Validate Z coordinates if provided
    if z_coords is not None:
        z_errors = validate_array_properties(
            z_coords, "z_coords", allow_nan=True, allow_inf=False  # Allow NaN for missing elevations
        )
        errors.extend(z_errors)

        # Check array lengths match
        if len(z_coords) != len(x_coords):
            errors.append(f"Z coordinates length ({len(z_coords)}) doesn't match X coordinates ({len(x_coords)})")

    # Check bounds if provided
    if bounds:
        for coord_name, coord_array in [("x", x_coords), ("y", y_coords), ("z", z_coords)]:
            if coord_array is not None:
                coord_min = bounds.get(f"{coord_name}_min")
                coord_max = bounds.get(f"{coord_name}_max")

                if coord_min is not None and np.any(coord_array < coord_min):
                    errors.append(f"{coord_name.upper()} coordinates below minimum {coord_min}")

                if coord_max is not None and np.any(coord_array > coord_max):
                    errors.append(f"{coord_name.upper()} coordinates above maximum {coord_max}")

    return errors


def validate_dataframe_structure(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None,
    column_types: Optional[Dict[str, str]] = None,
    allow_empty: bool = False
) -> List[str]:
    """Validate pandas DataFrame structure and content.

    Args:
        df: DataFrame to validate
        required_columns: List of columns that must be present
        column_types: Dict mapping column names to expected data types
        allow_empty: Whether empty DataFrames are allowed

    Returns:
        List of validation error messages
    """
    errors = []

    # Check if it's actually a DataFrame
    if not isinstance(df, pd.DataFrame):
        errors.append(f"Expected pandas DataFrame, got {type(df)}")
        return errors

    # Check for empty DataFrame
    if not allow_empty and len(df) == 0:
        errors.append("DataFrame is empty")

    # Check required columns
    if required_columns:
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            errors.append(f"Missing required columns: {list(missing_columns)}")

    # Check column data types
    if column_types:
        for col_name, expected_type in column_types.items():
            if col_name in df.columns:
                actual_type = str(df[col_name].dtype)
                if expected_type not in actual_type.lower():
                    errors.append(f"Column '{col_name}' has type {actual_type}, expected {expected_type}")

    return errors


def validate_numeric_range(
    values: Union[np.ndarray, List[float], pd.Series],
    name: str = "values",
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    allow_zero: bool = True
) -> List[str]:
    """Validate that numeric values are within acceptable ranges.

    Args:
        values: Numeric values to validate
        name: Name for error messages
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        allow_zero: Whether zero values are allowed

    Returns:
        List of validation error messages
    """
    errors = []

    # Convert to numpy array for consistent handling
    if isinstance(values, (list, pd.Series)):
        values = np.array(values)
    elif not isinstance(values, np.ndarray):
        errors.append(f"{name} must be numeric array-like, got {type(values)}")
        return errors

    # Check for non-numeric values
    if not np.issubdtype(values.dtype, np.number):
        errors.append(f"{name} contains non-numeric values")

    # Check zero values
    if not allow_zero and np.any(values == 0):
        zero_count = np.sum(values == 0)
        errors.append(f"{name} contains {zero_count} zero values (not allowed)")

    # Check minimum value
    if min_val is not None:
        below_min = np.sum(values < min_val)
        if below_min > 0:
            errors.append(f"{name} has {below_min} values below minimum {min_val}")

    # Check maximum value
    if max_val is not None:
        above_max = np.sum(values > max_val)
        if above_max > 0:
            errors.append(f"{name} has {above_max} values above maximum {max_val}")

    return errors


def validate_file_path(
    file_path: Union[str, Path],
    must_exist: bool = True,
    allowed_extensions: Optional[List[str]] = None,
    check_readable: bool = True
) -> List[str]:
    """Validate file path properties.

    Args:
        file_path: Path to validate
        must_exist: Whether file must exist
        allowed_extensions: List of allowed file extensions (e.g., ['.csv', '.txt'])
        check_readable: Whether to check if file is readable

    Returns:
        List of validation error messages
    """
    errors = []

    try:
        path = Path(file_path)

        # Check if file exists
        if must_exist and not path.exists():
            errors.append(f"File does not exist: {file_path}")
            return errors

        # Check if it's actually a file (not directory)
        if path.exists() and not path.is_file():
            errors.append(f"Path is not a file: {file_path}")

        # Check file extension
        if allowed_extensions:
            if path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                errors.append(f"File extension '{path.suffix}' not in allowed extensions: {allowed_extensions}")

        # Check if readable
        if check_readable and path.exists():
            try:
                with open(path, 'r') as f:
                    f.read(1)  # Try to read one character
            except (PermissionError, OSError) as e:
                errors.append(f"File is not readable: {e}")

    except Exception as e:
        errors.append(f"Invalid file path: {e}")

    return errors


def run_validation_checks(
    checks: List[Callable[[], List[str]]],
    logger: Optional[StructuredLogger] = None
) -> List[str]:
    """Run multiple validation checks and collect all errors.

    Args:
        checks: List of validation functions that return error lists
        logger: Optional logger for warning messages

    Returns:
        Combined list of all validation errors
    """
    all_errors = []

    for check_func in checks:
        try:
            errors = check_func()
            if errors:
                all_errors.extend(errors)
                if logger:
                    for error in errors:
                        logger.warning(f"Validation error: {error}")
        except Exception as e:
            error_msg = f"Validation check failed: {e}"
            all_errors.append(error_msg)
            if logger:
                logger.error(error_msg)

    return all_errors


def validate_and_raise(
    validation_errors: List[str],
    error_class: type = BeachProfileError,
    context: str = ""
) -> None:
    """Validate results and raise exception if errors found.

    Args:
        validation_errors: List of validation error messages
        error_class: Exception class to raise
        context: Additional context for error messages

    Raises:
        error_class: If validation errors are found
    """
    if validation_errors:
        error_msg = "Validation failed"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {len(validation_errors)} error(s) found"

        # Add details of first few errors
        for i, error in enumerate(validation_errors[:5]):
            error_msg += f"\n  {i+1}. {error}"

        if len(validation_errors) > 5:
            error_msg += f"\n  ... and {len(validation_errors) - 5} more errors"

        raise error_class(error_msg, category=ErrorCategory.VALIDATION)


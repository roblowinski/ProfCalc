"""
Generic Error Handling and Exception Utilities

This module provides reusable error handling patterns, custom exceptions, and
utility functions for robust error checking across different projects and
applications.

Key Features:
- Custom exception classes for different error types
- Array and data structure validation helpers
- File and path error checking
- Error message formatting utilities
- Exception chaining and context preservation
"""

from pathlib import Path
from typing import Any, Callable, List, Optional, Union

import numpy as np


class DataProcessingError(Exception):
    """Base exception for data processing operations."""
    pass


class FileOperationError(DataProcessingError):
    """Raised when file operations fail."""
    pass


class ValidationError(DataProcessingError):
    """Raised when data validation fails."""
    pass


class CoordinateError(DataProcessingError):
    """Raised when coordinate operations fail."""
    pass


class FormatError(DataProcessingError):
    """Raised when data format parsing fails."""
    pass


def check_array_lengths(*arrays: np.ndarray, names: Optional[List[str]] = None) -> None:
    """Check that all arrays have the same length.

    Args:
        *arrays: Variable number of numpy arrays to check
        names: Optional names for arrays in error messages

    Raises:
        ValidationError: If arrays have different lengths
    """
    if len(arrays) < 2:
        return  # Nothing to check

    first_length = len(arrays[0])
    first_name = names[0] if names and len(names) > 0 else "array_0"

    for i, array in enumerate(arrays[1:], 1):
        if len(array) != first_length:
            array_name = names[i] if names and len(names) > i else f"array_{i}"
            raise ValidationError(
                f"Array length mismatch: {first_name} has {first_length} elements, "
                f"{array_name} has {len(array)} elements"
            )


def check_array_types(*arrays: np.ndarray, expected_dtype: Optional[np.dtype] = None, names: Optional[List[str]] = None) -> None:
    """Check that arrays have compatible data types.

    Args:
        *arrays: Variable number of numpy arrays to check
        expected_dtype: Expected data type for all arrays
        names: Optional names for arrays in error messages

    Raises:
        ValidationError: If arrays have incompatible types
    """
    for i, array in enumerate(arrays):
        array_name = names[i] if names and len(names) > i else f"array_{i}"

        if not isinstance(array, np.ndarray):
            raise ValidationError(f"{array_name} must be a numpy array, got {type(array)}")

        if expected_dtype is not None:
            try:
                # Try to cast to expected dtype
                array.astype(expected_dtype, copy=False)
            except (ValueError, TypeError) as e:
                raise ValidationError(
                    f"{array_name} cannot be converted to {expected_dtype}: {e}"
                ) from e


def check_file_exists(file_path: Union[str, Path], operation: str = "operation") -> None:
    """Check if a file exists and is accessible.

    Args:
        file_path: Path to the file to check
        operation: Description of the operation requiring the file

    Raises:
        FileNotFoundError: If file doesn't exist
        FileOperationError: If file exists but is not accessible
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File required for {operation} does not exist: {file_path}")

    if not path.is_file():
        raise FileOperationError(f"Path is not a file: {file_path}")

    # Check if file is readable
    try:
        with open(path, 'r') as f:
            f.read(1)  # Try to read one character
    except (PermissionError, OSError) as e:
        raise FileOperationError(f"File is not readable: {file_path} - {e}")


def check_directory_exists(dir_path: Union[str, Path], operation: str = "operation", create_if_missing: bool = False) -> None:
    """Check if a directory exists and is accessible.

    Args:
        dir_path: Path to the directory to check
        operation: Description of the operation requiring the directory
        create_if_missing: Whether to create the directory if it doesn't exist

    Raises:
        FileNotFoundError: If directory doesn't exist and create_if_missing is False
        FileOperationError: If path exists but is not a directory
    """
    path = Path(dir_path)

    if not path.exists():
        if create_if_missing:
            try:
                path.mkdir(parents=True, exist_ok=True)
                return
            except OSError as e:
                raise FileOperationError(f"Could not create directory {dir_path}: {e}")
        else:
            raise FileNotFoundError(f"Directory required for {operation} does not exist: {dir_path}")

    if not path.is_dir():
        raise FileOperationError(f"Path is not a directory: {dir_path}")


def check_numeric_value(
    value: Union[int, float],
    name: str = "value",
    min_val: Optional[Union[int, float]] = None,
    max_val: Optional[Union[int, float]] = None,
    allow_zero: bool = True,
    allow_negative: bool = True
) -> None:
    """Check that a numeric value meets specified constraints.

    Args:
        value: Value to check
        name: Name of the value for error messages
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        allow_zero: Whether zero is allowed
        allow_negative: Whether negative values are allowed

    Raises:
        ValidationError: If value doesn't meet constraints
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be numeric, got {type(value)}")

    if not allow_zero and value == 0:
        raise ValidationError(f"{name} cannot be zero")

    if not allow_negative and value < 0:
        raise ValidationError(f"{name} cannot be negative: {value}")

    if min_val is not None and value < min_val:
        raise ValidationError(f"{name} {value} is below minimum {min_val}")

    if max_val is not None and value > max_val:
        raise ValidationError(f"{name} {value} is above maximum {max_val}")


def check_coordinate_bounds(
    coords: np.ndarray,
    coord_type: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None
) -> None:
    """Check that coordinates are within reasonable bounds.

    Args:
        coords: Coordinate array to check
        coord_type: Type of coordinates ("longitude", "latitude", "elevation", etc.)
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Raises:
        CoordinateError: If coordinates are out of bounds
    """
    if not isinstance(coords, np.ndarray):
        raise ValidationError(f"Coordinates must be numpy array, got {type(coords)}")

    # Set default bounds based on coordinate type
    if coord_type.lower() == "longitude":
        min_val = min_val if min_val is not None else -180.0
        max_val = max_val if max_val is not None else 180.0
    elif coord_type.lower() == "latitude":
        min_val = min_val if min_val is not None else -90.0
        max_val = max_val if max_val is not None else 90.0
    elif coord_type.lower() == "elevation" and min_val is None:
        # Allow negative elevations (below sea level) but set a reasonable upper bound
        min_val = -1000.0  # Deepest point on Earth
        max_val = max_val if max_val is not None else 10000.0  # Highest mountain + buffer

    if min_val is not None:
        out_of_bounds = np.sum(coords < min_val)
        if out_of_bounds > 0:
            raise CoordinateError(
                f"{coord_type} coordinates: {out_of_bounds} values below minimum {min_val}"
            )

    if max_val is not None:
        out_of_bounds = np.sum(coords > max_val)
        if out_of_bounds > 0:
            raise CoordinateError(
                f"{coord_type} coordinates: {out_of_bounds} values above maximum {max_val}"
            )


def safe_file_operation(operation_func: Callable, file_path: Union[str, Path], *args, **kwargs) -> Any:
    """Execute a file operation with comprehensive error handling.

    Args:
        operation_func: Function to execute (should take file_path as first argument)
        file_path: Path to the file being operated on
        *args: Additional positional arguments for operation_func
        **kwargs: Additional keyword arguments for operation_func

    Returns:
        Result of the operation function

    Raises:
        FileOperationError: If the file operation fails
    """
    try:
        return operation_func(file_path, *args, **kwargs)
    except FileNotFoundError as e:
        raise FileOperationError(f"File not found: {file_path}") from e
    except PermissionError as e:
        raise FileOperationError(f"Permission denied accessing file: {file_path}") from e
    except OSError as e:
        raise FileOperationError(f"OS error accessing file {file_path}: {e}") from e
    except Exception as e:
        raise FileOperationError(f"Unexpected error accessing file {file_path}: {e}") from e


def format_error_message(error: Exception, context: Optional[str] = None, include_traceback: bool = False) -> str:
    """Format an exception into a user-friendly error message.

    Args:
        error: The exception to format
        context: Additional context about where the error occurred
        include_traceback: Whether to include full traceback

    Returns:
        Formatted error message string
    """
    error_type = type(error).__name__

    if context:
        message = f"{error_type} in {context}: {str(error)}"
    else:
        message = f"{error_type}: {str(error)}"

    if include_traceback and hasattr(error, '__traceback__'):
        import traceback
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        message += "\n\nTraceback:\n" + "".join(tb_lines)

    return message


def validate_and_convert_type(value: Any, target_type: type, name: str = "value") -> Any:
    """Safely convert a value to a target type with error handling.

    Args:
        value: Value to convert
        target_type: Type to convert to
        name: Name of the value for error messages

    Returns:
        Converted value

    Raises:
        ValidationError: If conversion fails
    """
    try:
        if target_type is bool:
            # Special handling for boolean conversion
            if isinstance(value, str):
                lower_val = value.lower()
                if lower_val in ('true', '1', 'yes', 'on'):
                    return True
                elif lower_val in ('false', '0', 'no', 'off'):
                    return False
                else:
                    raise ValueError(f"Cannot convert '{value}' to boolean")
            else:
                return bool(value)
        else:
            return target_type(value)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Cannot convert {name} '{value}' to {target_type.__name__}: {e}") from e


def check_memory_usage_threshold(current_mb: float, threshold_mb: float, operation: str = "operation") -> None:
    """Check if memory usage exceeds a threshold.

    Args:
        current_mb: Current memory usage in MB
        threshold_mb: Maximum allowed memory usage in MB
        operation: Description of the operation

    Raises:
        DataProcessingError: If memory threshold is exceeded
    """
    if current_mb > threshold_mb:
        raise DataProcessingError(
            f"Memory usage ({current_mb:.1f} MB) exceeds threshold ({threshold_mb:.1f} MB) "
            f"during {operation}. Consider processing data in smaller chunks."
        )

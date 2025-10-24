# =============================================================================  # noqa: D100
# Beach Profile Database - Enhanced Data Validation Utilities
# =============================================================================
#
# ENHANCED VERSION: Incorporates valuable patterns from Profile_Analysis project
#
# PURPOSE:
# This module provides comprehensive data validation utilities that ensure data
# integrity, consistency, and correctness across all components of the Beach
# Profile Database application.
#
# KEY FEATURES:
# - Generic array validation with flexible configuration
# - Coordinate validation for spatial data
# - DataFrame validation for tabular data
# - Validation runner pattern for comprehensive checks
# - Safe file operation wrappers
# - Context manager for operation logging
# - ENHANCED: Domain-specific beach profile validations
# - ENHANCED: Flexible coordinate system validation
# - ENHANCED: Comprehensive data quality checks
#
# VALIDATION SYSTEM:
# - Array property validation (length, NaN, infinity, dtype)
# - Coordinate validation (bounds, format, consistency)
# - DataFrame validation (schema, data types, constraints)
# - Beach profile specific validations (elevation, distance, morphology)
# - Validation runner for batch processing
# - Error collection and reporting
#
# DESIGN PRINCIPLES:
# The validation system is designed to be flexible and extensible, allowing
# for both generic validations that can be reused across different data types
# and domain-specific validations tailored to beach profile data characteristics.
#
# IMPORTANCE:
# This module is critical for maintaining data quality and preventing downstream
# errors in processing, analysis, and visualization components.
#
# =============================================================================

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


# Define basic classes for standalone operation
class BeachProfileError(Exception):
    """Custom exception class for beach profile database errors."""
    def __init__(self, message: str, category: str = "VALIDATION", **kwargs):
        super().__init__(message)
        self.category = category

class ErrorCategory:
    """Error categories for classification."""
    VALIDATION = "VALIDATION"
    DATABASE = "DATABASE"
    FILE_IO = "FILE_IO"

def validate_array_properties(
    array,
    name: str = "array",
    allow_nan: bool = True,
    allow_inf: bool = True,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    dtype: Optional[Any] = None
) -> List[str]:
    """Basic array validation function."""
    errors = []

    # Check if it's actually a numpy array
    if not hasattr(array, 'shape'):  # Simple check for array-like
        errors.append(f"{name} must be a numpy array, got {type(array)}")
        return errors

    # Check length constraints
    if min_length is not None and len(array) < min_length:
        errors.append(f"{name} length {len(array)} is below minimum {min_length}")

    if max_length is not None and len(array) > max_length:
        errors.append(f"{name} length {len(array)} exceeds maximum {max_length}")

    # Check for NaN values
    if not allow_nan and hasattr(array, 'isnan') and array.isnan().any():
        nan_count = array.isnan().sum() if hasattr(array, 'sum') else 0
        errors.append(f"{name} contains {nan_count} NaN values (not allowed)")

    # Check for infinite values
    if not allow_inf and hasattr(array, 'isinf') and array.isinf().any():
        inf_count = array.isinf().sum() if hasattr(array, 'sum') else 0
        errors.append(f"{name} contains {inf_count} infinite values (not allowed)")

    return errors

def run_validation_checks(
    checks: List[Callable[[], List[str]]],
    logger=None
) -> List[str]:
    """Run multiple validation checks and collect all errors."""
    all_errors = []

    for check_func in checks:
        try:
            errors = check_func()
            if errors:
                all_errors.extend(errors)
        except Exception as e:
            error_msg = f"Validation check failed: {e}"
            all_errors.append(error_msg)

    return all_errors

def safe_file_operation(operation_func: Callable, file_path, *args, **kwargs):
    """Execute a file operation with comprehensive error handling."""
    try:
        return operation_func(file_path, *args, **kwargs)
    except FileNotFoundError as e:
        raise BeachProfileError(f"File not found: {file_path}", category=ErrorCategory.FILE_IO) from e
    except PermissionError as e:
        raise BeachProfileError(f"Permission denied accessing file: {file_path}", category=ErrorCategory.FILE_IO) from e
    except OSError as e:
        raise BeachProfileError(f"OS error accessing file {file_path}: {e}", category=ErrorCategory.FILE_IO) from e
    except Exception as e:
        raise BeachProfileError(f"Unexpected error accessing file {file_path}: {e}", category=ErrorCategory.FILE_IO) from e


# =============================================================================
# GENERIC ARRAY VALIDATION UTILITIES (Enhanced from Profile_Analysis)
# =============================================================================

def validate_array_properties_enhanced(
    array,
    name: str = "array",
    allow_nan: bool = True,
    allow_inf: bool = True,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    dtype: Optional[Any] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    check_monotonic: Optional[str] = None
) -> List[str]:
    """Enhanced array validation with additional constraints.

    Extends the basic array validation with value range checks and monotonicity validation.
    This provides more comprehensive array validation for scientific data.

    Args:
        array: Array to validate
        name: Name of the array for error messages
        allow_nan: Whether NaN values are allowed
        allow_inf: Whether infinite values are allowed
        min_length: Minimum required length
        max_length: Maximum allowed length
        dtype: Required data type
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        check_monotonic: 'increasing', 'decreasing', or None

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = validate_array_properties(
        array, name, allow_nan, allow_inf, min_length, max_length, dtype
    )

    # Additional value range checks
    if min_value is not None and hasattr(array, '__iter__'):
        try:
            if np.any(np.array(array) < min_value):
                count = np.sum(np.array(array) < min_value)
                errors.append(f"{name} contains {count} values below minimum {min_value}")
        except (TypeError, ValueError):
            pass  # Skip if array operations fail

    if max_value is not None and hasattr(array, '__iter__'):
        try:
            if np.any(np.array(array) > max_value):
                count = np.sum(np.array(array) > max_value)
                errors.append(f"{name} contains {count} values above maximum {max_value}")
        except (TypeError, ValueError):
            pass  # Skip if array operations fail

    # Monotonicity checks
    if check_monotonic and hasattr(array, '__len__') and len(array) > 1:
        try:
            arr = np.array(array)
            if check_monotonic == 'increasing' and not np.all(arr[1:] >= arr[:-1]):
                errors.append(f"{name} is not monotonically increasing")
            elif check_monotonic == 'decreasing' and not np.all(arr[1:] <= arr[:-1]):
                errors.append(f"{name} is not monotonically decreasing")
        except (TypeError, ValueError):
            pass  # Skip if array operations fail

    return errors


def validate_coordinate_arrays(
    x_array,
    y_array,
    coordinate_system: str = "cartesian",
    bounds: Optional[Dict[str, Tuple[float, float]]] = None
) -> List[str]:
    """Validate coordinate arrays for consistency and validity.

    Performs comprehensive validation of coordinate data including length matching,
    value ranges, and coordinate system specific checks.

    Args:
        x_array: X/coordinate array
        y_array: Y/coordinate array
        coordinate_system: Type of coordinate system ('cartesian', 'geographic', 'beach_profile')
        bounds: Optional bounds checking as {'x': (min, max), 'y': (min, max)}

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Basic array validation
    errors.extend(validate_array_properties(x_array, "x_coordinates", allow_nan=False))
    errors.extend(validate_array_properties(y_array, "y_coordinates", allow_nan=False))

    # Length matching
    if len(x_array) != len(y_array):
        errors.append(f"Coordinate array length mismatch: x has {len(x_array)}, y has {len(y_array)}")

    if len(errors) > 0:
        return errors  # Don't continue if basic validation fails

    # Coordinate system specific validation
    if coordinate_system.lower() == "geographic":
        # Latitude bounds: -90 to 90
        if bounds is None:
            bounds = {'x': (-180, 180), 'y': (-90, 90)}

        lat_min, lat_max = bounds.get('y', (-90, 90))
        lon_min, lon_max = bounds.get('x', (-180, 180))

        if np.any((y_array < lat_min) | (y_array > lat_max)):
            errors.append(f"Latitude values out of range [{lat_min}, {lat_max}]")

        if np.any((x_array < lon_min) | (x_array > lon_max)):
            errors.append(f"Longitude values out of range [{lon_min}, {lon_max}]")

    elif coordinate_system.lower() == "beach_profile":
        # Beach profile coordinates: x typically distance alongshore, y elevation
        # Allow flexible bounds but check for reasonable ranges
        if bounds:
            x_min, x_max = bounds.get('x', (-np.inf, np.inf))
            y_min, y_max = bounds.get('y', (-np.inf, np.inf))

            if np.any((x_array < x_min) | (x_array > x_max)):
                errors.append(f"X coordinates out of range [{x_min}, {x_max}]")

            if np.any((y_array < y_min) | (y_array > y_max)):
                errors.append(f"Y coordinates out of range [{y_min}, {y_max}]")

    # Check for duplicate coordinates (potential data quality issue)
    try:
        coords = np.column_stack((x_array, y_array))
        unique_coords = np.unique(coords, axis=0)
        if len(unique_coords) < len(coords):
            duplicates = len(coords) - len(unique_coords)
            errors.append(f"Found {duplicates} duplicate coordinate pairs")
    except (ValueError, TypeError):
        pass  # Skip duplicate check if arrays can't be combined

    return errors


# =============================================================================
# DATAFRAME VALIDATION UTILITIES
# =============================================================================

def validate_dataframe_schema(
    df: pd.DataFrame,
    required_columns: List[str],
    column_types: Optional[Dict[str, str]] = None,
    allow_extra_columns: bool = True
) -> List[str]:
    """Validate DataFrame schema including required columns and types.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        column_types: Optional mapping of column names to expected types
        allow_extra_columns: Whether extra columns are allowed

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check required columns
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        errors.append(f"Missing required columns: {list(missing_columns)}")

    # Check for extra columns if not allowed
    if not allow_extra_columns:
        extra_columns = set(df.columns) - set(required_columns)
        if extra_columns:
            errors.append(f"Unexpected columns found: {list(extra_columns)}")

    # Check column types
    if column_types:
        for col, expected_type in column_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if expected_type not in actual_type.lower():
                    errors.append(f"Column '{col}' has type {actual_type}, expected {expected_type}")

    return errors


def validate_dataframe_data(
    df: pd.DataFrame,
    column_constraints: Optional[Dict[str, Dict[str, Any]]] = None,
    check_duplicates: bool = True,
    subset: Optional[List[str]] = None
) -> List[str]:
    """Validate DataFrame data content and constraints.

    Args:
        df: DataFrame to validate
        column_constraints: Constraints per column (min, max, allow_nan, etc.)
        check_duplicates: Whether to check for duplicate rows
        subset: Columns to consider for duplicate checking

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check for empty DataFrame
    if df.empty:
        errors.append("DataFrame is empty")
        return errors

    # Column-specific constraints
    if column_constraints:
        for col, constraints in column_constraints.items():
            if col not in df.columns:
                continue

            series = df[col]

            # Check for NaN values
            if not constraints.get('allow_nan', True) and series.isna().any():
                nan_count = series.isna().sum()
                errors.append(f"Column '{col}' contains {nan_count} NaN values")

            # Check numeric constraints
            if pd.api.types.is_numeric_dtype(series):
                if 'min' in constraints and (series < constraints['min']).any():
                    count = (series < constraints['min']).sum()
                    errors.append(f"Column '{col}' has {count} values below minimum {constraints['min']}")

                if 'max' in constraints and (series > constraints['max']).any():
                    count = (series > constraints['max']).sum()
                    errors.append(f"Column '{col}' has {count} values above maximum {constraints['max']}")

    # Check for duplicate rows
    if check_duplicates:
        duplicate_subset = subset or df.columns.tolist()
        duplicates = df.duplicated(subset=duplicate_subset).sum()
        if duplicates > 0:
            errors.append(f"Found {duplicates} duplicate rows")

    return errors


# =============================================================================
# BEACH PROFILE SPECIFIC VALIDATIONS
# =============================================================================

def validate_beach_profile_data(
    distance: np.ndarray,
    elevation: np.ndarray,
    profile_id: Optional[str] = None
) -> List[str]:
    """Validate beach profile data for physical reasonableness.

    Performs domain-specific validation for beach profile datasets including
    elevation ranges, distance monotonicity, and profile characteristics.

    Args:
        distance: Distance along profile (should be monotonic)
        elevation: Elevation values
        profile_id: Optional profile identifier for error messages

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    prefix = f"Profile {profile_id}: " if profile_id else ""

    # Basic coordinate validation
    coord_errors = validate_coordinate_arrays(
        distance, elevation,
        coordinate_system="beach_profile",
        bounds={'x': (0.0, float('inf')), 'y': (-20.0, 20.0)}  # Reasonable beach profile bounds
    )
    errors.extend([f"{prefix}{err}" for err in coord_errors])

    if len(errors) > 0:
        return errors  # Don't continue if basic validation fails

    # Distance should be monotonically increasing (moving along profile)
    if not np.all(distance[1:] >= distance[:-1]):
        errors.append(f"{prefix}Distance values are not monotonically increasing")

    # Check for reasonable elevation changes (no unrealistic jumps)
    elevation_diff = np.abs(np.diff(elevation))
    max_reasonable_diff = 5.0  # 5 meters max change between points
    if np.any(elevation_diff > max_reasonable_diff):
        count = np.sum(elevation_diff > max_reasonable_diff)
        errors.append(f"{prefix}{count} elevation changes exceed {max_reasonable_diff}m (possible data errors)")

    # Check for minimum profile length
    profile_length = distance[-1] - distance[0] if len(distance) > 1 else 0
    if profile_length < 1.0:  # Minimum 1 meter profile
        errors.append(f"{prefix}Profile length {profile_length:.1f}m is too short")

    # Check for sufficient data points
    if len(distance) < 5:
        errors.append(f"{prefix}Profile has only {len(distance)} points (minimum 5 recommended)")

    return errors


def validate_beach_profile_dataset(
    df: pd.DataFrame,
    distance_col: str = "distance",
    elevation_col: str = "elevation",
    profile_id_col: Optional[str] = "profile_id"
) -> List[str]:
    """Validate a complete beach profile dataset.

    Args:
        df: DataFrame containing beach profile data
        distance_col: Name of distance column
        elevation_col: Name of elevation column
        profile_id_col: Name of profile ID column (optional)

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Schema validation
    required_cols = [distance_col, elevation_col]
    if profile_id_col:
        required_cols.append(profile_id_col)

    schema_errors = validate_dataframe_schema(df, required_cols)
    errors.extend(schema_errors)

    if schema_errors:
        return errors  # Can't continue without required columns

    # Data validation
    data_errors = validate_dataframe_data(df, {
        distance_col: {'allow_nan': False, 'min': 0},
        elevation_col: {'allow_nan': False, 'min': -50, 'max': 50}
    })
    errors.extend(data_errors)

    # Profile-specific validation
    if profile_id_col and profile_id_col in df.columns:
        # Validate each profile separately
        for profile_id, group in df.groupby(profile_id_col):
            distance = np.asarray(group[distance_col].values, dtype=float)
            elevation = np.asarray(group[elevation_col].values, dtype=float)
            profile_errors = validate_beach_profile_data(distance, elevation, str(profile_id))
            errors.extend(profile_errors)
    else:
        # Validate as single profile
        distance = np.asarray(df[distance_col].values, dtype=float)
        elevation = np.asarray(df[elevation_col].values, dtype=float)
        profile_errors = validate_beach_profile_data(distance, elevation)
        errors.extend(profile_errors)

    return errors


# =============================================================================
# VALIDATION RUNNER AND UTILITIES
# =============================================================================

def run_comprehensive_validation(
    data: Any,
    validation_type: str,
    logger: Optional[Any] = None,
    **kwargs
) -> Tuple[bool, List[str]]:
    """Run comprehensive validation based on data type.

    Args:
        data: Data to validate
        validation_type: Type of validation ('array', 'coordinates', 'dataframe', 'beach_profile')
        logger: Optional logger for warnings
        **kwargs: Additional validation parameters

    Returns:
        Tuple of (is_valid, error_list)
    """
    validation_functions = {
        'array': lambda: validate_array_properties_enhanced(data, **kwargs),
        'coordinates': lambda: validate_coordinate_arrays(data[0], data[1], **kwargs),
        'dataframe': lambda: validate_dataframe_schema(data, **kwargs) + validate_dataframe_data(data, **kwargs),
        'beach_profile': lambda: validate_beach_profile_dataset(data, **kwargs)
    }

    if validation_type not in validation_functions:
        return False, [f"Unknown validation type: {validation_type}"]

    try:
        errors = validation_functions[validation_type]()
        is_valid = len(errors) == 0

        if not is_valid and logger:
            for error in errors:
                logger.warning(f"Validation error: {error}")

        return is_valid, errors

    except Exception as e:
        error_msg = f"Validation failed with exception: {e}"
        if logger:
            logger.error(error_msg)
        return False, [error_msg]


def validate_file_with_checks(
    file_path: Union[str, Path],
    validation_checks: List[Callable[[], List[str]]],
    logger: Optional[Any] = None
) -> Tuple[bool, List[str]]:
    """Validate a file using multiple validation checks with safe file operations.

    Args:
        file_path: Path to file to validate
        validation_checks: List of validation functions
        logger: Optional logger

    Returns:
        Tuple of (is_valid, error_list)
    """
    def perform_validation():
        return run_validation_checks(validation_checks, logger)

    try:
        errors = safe_file_operation(perform_validation, file_path)
        return len(errors) == 0, errors
    except BeachProfileError as e:
        return False, [str(e)]


# =============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS
# =============================================================================

def check_array_lengths(*arrays, names=None) -> None:
    """Backward compatibility function for array length checking from Profile_Analysis."""
    if len(arrays) < 2:
        return

    first_length = len(arrays[0])
    first_name = names[0] if names and len(names) > 0 else "array_0"

    for i, array in enumerate(arrays[1:], 1):
        if len(array) != first_length:
            array_name = names[i] if names and len(names) > i else f"array_{i}"
            raise BeachProfileError(
                f"Array length mismatch: {first_name} has {first_length} elements, "
                f"{array_name} has {len(array)} elements",
                category=ErrorCategory.VALIDATION
            )


def validate_numeric_array(
    array,
    name: str = "array",
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    allow_nan: bool = True
) -> List[str]:
    """Backward compatibility function for numeric array validation."""
    return validate_array_properties_enhanced(
        array, name=name, min_value=min_val, max_value=max_val, allow_nan=allow_nan
    )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_validation_report(
    validation_results: Dict[str, Tuple[bool, List[str]]],
    title: str = "Validation Report"
) -> str:
    """Create a formatted validation report from results.

    Args:
        validation_results: Dictionary mapping check names to (is_valid, errors) tuples
        title: Report title

    Returns:
        Formatted report string
    """
    report_lines = [title, "=" * len(title), ""]

    total_checks = len(validation_results)
    passed_checks = sum(1 for valid, _ in validation_results.values() if valid)
    failed_checks = total_checks - passed_checks

    report_lines.append(f"Summary: {passed_checks}/{total_checks} checks passed")
    report_lines.append("")

    for check_name, (is_valid, errors) in validation_results.items():
        status = "✓ PASS" if is_valid else "✗ FAIL"
        report_lines.append(f"{status}: {check_name}")

        if not is_valid and errors:
            for error in errors:
                report_lines.append(f"  - {error}")
        report_lines.append("")

    return "\n".join(report_lines)


def log_validation_results(
    validation_results: Dict[str, Tuple[bool, List[str]]],
    logger: Any,
    operation: str = "validation"
) -> None:
    """Log validation results using structured logging.

    Args:
        validation_results: Dictionary mapping check names to (is_valid, errors) tuples
        logger: Logger instance
        operation: Operation name for context
    """
    total_checks = len(validation_results)
    passed_checks = sum(1 for valid, _ in validation_results.values() if valid)

    logger.info(f"{operation} completed: {passed_checks}/{total_checks} checks passed")

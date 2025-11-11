# =============================================================================
# ProfCalc Common Utilities Package
# =============================================================================
#
# FILE: src/profcalc/common/__init__.py
#
# PURPOSE:
# This is the central hub for all shared utilities and common functionality
# used across the ProfCalc framework. It provides a unified interface to
# essential tools for data I/O, validation, coordinate transformations,
# error handling, and other cross-cutting concerns that are needed by
# multiple analysis modules.
#
# WHAT IT'S FOR:
# - Provides unified access to all common utility functions
# - Centralizes imports for frequently used functionality
# - Ensures consistent interfaces across different analysis tools
# - Supports data I/O operations for multiple file formats (BMAP, CSV, 9-column, etc.)
# - Offers coordinate transformation and baseline management utilities
# - Provides data validation and error handling frameworks
# - Enables consistent logging and reporting across the application
#
# WORKFLOW POSITION:
# This package sits at the foundation of the ProfCalc architecture, providing
# essential building blocks that are used by all higher-level analysis tools.
# It's imported by both CLI tools and core analysis modules, ensuring that
# common functionality is implemented once and reused consistently.
#
# LIMITATIONS:
# - Large package with many dependencies - imports may be slow if not selective
# - Some legacy modules (io_freeformat) are deprecated but still included
# - Requires careful management of __all__ exports to avoid namespace pollution
# - Some utilities assume specific data formats and coordinate systems
#
# ASSUMPTIONS:
# - All submodules are properly implemented and compatible with each other
# - Coordinate systems and data formats are consistent across tools
# - Error handling patterns are followed by all calling code
# - Logging configuration is established before using logging utilities
# - File I/O operations have appropriate permissions and valid file paths
#
# =============================================================================

"""
Common utilities and shared logic for all analysis tools.

Includes:
- config_utils: handles global and tool-specific settings
- io_freeformat: legacy BMAP file I/O (deprecated, use bmap_io instead)
- bmap_io: BMAP free format file I/O with Profile dataclass
- csv_io: CSV file I/O for reading and writing beach profile data
- ninecol_io: 9-column ASCII file I/O
- coordinate_transforms: 2D ↔ 3D coordinate transformations and baseline management
- data_validation: generic data validation utilities
- error_handling: error checking and custom exceptions
- logging_utils: logging setup and operation tracking
- io_reports: report formatting and export utilities
- resampling_core: interpolation, spacing, and math routines
"""

from .bmap_io import (
    read_bmap_freeformat,
    read_bmap_profiles,
    write_bmap_profiles,
)
from .config_utils import get_dx
from .coordinate_transforms import (
    batch_transform_profiles_to_2d,
    batch_transform_profiles_to_3d,
    convert_2d_to_3d_profile,
    convert_3d_to_2d_profile,
    estimate_profile_baseline,
    load_profile_baselines,
    transform_profile_to_2d,
    transform_profile_to_3d,
    transform_profiles_with_baselines,
)
from .csv_io import read_csv_profiles, read_xyz_profiles, write_csv_profiles
from .data_validation import (
    validate_and_raise,
    validate_array_properties,
    validate_coordinate_arrays,
    validate_dataframe_structure,
    validate_file_path,
    validate_numeric_range,
)
from .error_handler import (
    BeachProfileError,
    LogComponent,
    get_logger,
)
from .error_handling import check_array_lengths
from .io_reports import (
    write_bar_properties_report,
    write_cutfill_detailed_report,
    write_volume_report,
)
from .logging_utils import setup_module_logger
from .ninecol_io import read_9col_profiles, write_9col_profiles
from .resampling_core import interpolate_to_common_grid

__all__ = [
    "get_dx",
    "read_bmap_freeformat",
    "write_volume_report",
    "write_cutfill_detailed_report",
    "write_bar_properties_report",
    "interpolate_to_common_grid",
    "read_csv_profiles",
    "read_xyz_profiles",
    "read_bmap_profiles",
    "read_9col_profiles",
    "write_csv_profiles",
    "convert_3d_to_2d_profile",
    "convert_2d_to_3d_profile",
    "transform_profile_to_2d",
    "transform_profile_to_3d",
    "batch_transform_profiles_to_2d",
    "batch_transform_profiles_to_3d",
    "estimate_profile_baseline",
    "load_profile_baselines",
    "transform_profiles_with_baselines",
    "write_bmap_profiles",
    "write_9col_profiles",
    # Data validation functions
    "validate_array_properties",
    "validate_coordinate_arrays",
    "validate_dataframe_structure",
    "validate_file_path",
    "validate_numeric_range",
    "validate_and_raise",
    # Error handling functions
    "check_array_lengths",
    "setup_module_logger",
    "BeachProfileError",
    "get_logger",
    "LogComponent",
]

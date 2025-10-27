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
    check_array_lengths,
    get_logger,
    setup_module_logger,
)
from .io_reports import (
    write_bar_properties_report,
    write_cutfill_detailed_report,
    write_volume_report,
)
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


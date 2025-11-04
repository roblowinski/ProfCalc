"""
Core analysis modules for coastal profile analysis.

This package contains the core computational logic extracted from various
analysis tools, making them reusable across CLI tools and menu systems.
"""

from .beach_classification import classify_beach_type
from .bmap_area_calcs import area_above_contour_bmap, cross_section_change
from .profile_stats import (
    calculate_beach_face_slope,
    calculate_berm_width,
    calculate_common_ranges,
)
from .quality_checks import detect_gaps_and_outliers
from .shoreline_analysis import (
    calculate_real_world_coordinates,
    extract_seaward_most_position,
)

__all__ = [
    "calculate_berm_width",
    "calculate_beach_face_slope",
    "calculate_common_ranges",
    "detect_gaps_and_outliers",
    "classify_beach_type",
    "cross_section_change",
    "area_above_contour_bmap",
    "extract_seaward_most_position",
    "calculate_real_world_coordinates",
]

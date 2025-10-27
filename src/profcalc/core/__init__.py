"""
Core analysis modules for coastal profile analysis.

This package contains the core computational logic extracted from various
analysis tools, making them reusable across CLI tools and menu systems.
"""

from .beach_classification import classify_beach_type
from .profile_stats import (
    calculate_beach_face_slope,
    calculate_berm_width,
    calculate_common_ranges,
)
from .quality_checks import detect_gaps_and_outliers

__all__ = [
    "calculate_berm_width",
    "calculate_beach_face_slope",
    "calculate_common_ranges",
    "detect_gaps_and_outliers",
    "classify_beach_type",
]


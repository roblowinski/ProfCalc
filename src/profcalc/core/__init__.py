# =============================================================================
# ProfCalc Core Analysis Engine
# =============================================================================
#
# FILE: src/profcalc/core/__init__.py
#
# PURPOSE:
# This package contains the core computational algorithms and analysis logic
# that power ProfCalc's beach profile analysis capabilities. It provides the
# fundamental mathematical and statistical methods that are used across all
# analysis tools, extracted into reusable modules for consistency and
# maintainability.
#
# WHAT IT'S FOR:
# - Implements core beach profile analysis algorithms and calculations
# - Provides reusable computational logic for cross-sectional analysis
# - Supports shoreline position calculations and coordinate transformations
# - Enables beach classification and morphological analysis
# - Offers quality control and data validation algorithms
# - Provides statistical analysis of profile characteristics
#
# WORKFLOW POSITION:
# This package forms the computational foundation of ProfCalc, sitting below
# the tools layer and above the common utilities. It's used by all analysis
# tools that need to perform calculations on beach profile data, ensuring
# consistent algorithms and methodologies across different applications.
#
# LIMITATIONS:
# - Algorithms assume specific data formats and coordinate systems
# - Some calculations may have numerical precision limitations
# - Quality checks depend on statistical assumptions about data distributions
# - Coordinate transformations require proper baseline definitions
#
# ASSUMPTIONS:
# - Input data is properly validated before reaching core algorithms
# - Coordinate systems are consistent and properly defined
# - Mathematical models are appropriate for the beach morphology being analyzed
# - Statistical methods are suitable for the data characteristics
# - Users understand the engineering context of the calculations
#
# =============================================================================

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

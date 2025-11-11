# =============================================================================
# Data Quality Assessment Module for Coastal Profiles
# =============================================================================
#
# FILE: src/profcalc/core/quality_checks.py
#
# PURPOSE:
# This module provides data quality assessment functions for beach profile
# data, detecting issues that could affect analysis accuracy. It identifies
# gaps in survey coverage and statistical outliers that may indicate data
# collection problems or environmental anomalies.
#
# WHAT IT'S FOR:
# - Detecting gaps in profile survey data coverage
# - Identifying elevation outliers using statistical methods
# - Assessing data quality for reliable analysis results
# - Providing quality metrics for profile comparison workflows
#
# WORKFLOW POSITION:
# This module is used in data validation and preprocessing workflows to
# ensure data quality before performing analysis. It helps identify profiles
# that may need additional surveying or data cleaning before inclusion in
# comparative analyses.
#
# LIMITATIONS:
# - Gap detection depends on expected point spacing assumptions
# - Outlier detection uses statistical thresholds that may not suit all data
# - Quality assessment is automated and may miss contextual issues
# - Requires common range statistics for effective gap detection
#
# ASSUMPTIONS:
# - Profile data follows expected spatial sampling patterns
# - Outliers represent data quality issues rather than real features
# - Common range statistics accurately represent expected data density
# - Users will review flagged issues before proceeding with analysis
#
# =============================================================================

"""
Data quality assessment module for coastal profiles.

Provides functions for detecting data quality issues including:
- Gaps in survey data
- Elevation outliers
- Quality scoring
"""

from typing import Dict, List, Tuple

import numpy as np


def detect_gaps_and_outliers(
    profiles: Dict[str, List[List[Tuple[float, float]]]],
    common_ranges: Dict[
        str,
        Tuple[
            float,
            float,
            int,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            str,
        ],
    ],
) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    """
    Detect gaps in data and elevation outliers using statistical methods.

    Args:
        profiles: Raw profile data mapping profile names to lists of point lists
        common_ranges: Calculated statistics including avg_spacing at index 3

    Returns:
        Tuple of (gaps, outliers) where each is list of (profile_name, x_location) tuples
    """
    # =======================================================================
    # GAP DETECTION METHODOLOGY
    # =======================================================================
    #
    # Gaps are identified as significant discontinuities in point spacing that
    # indicate missing survey data. This method uses a threshold-based approach
    # with statistical justification.
    #
    # MATHEMATICAL APPROACH:
    # ---------------------
    # 1. Calculate average point spacing: s_avg = Σ|s_i| / n
    #    where s_i = x_{i+1} - x_i (spacing between consecutive points)
    #
    # 2. Set gap threshold: T_gap = s_avg × 5.0
    #    (5× multiplier provides conservative gap detection)
    #
    # 3. Identify gaps: ∀i, if s_i > T_gap, then gap at x = (x_i + x_{i+1}) / 2
    #
    # OUTLIER DETECTION METHODOLOGY:
    # -----------------------------
    # Elevation outliers are detected using the Interquartile Range (IQR) method,
    # which is robust to non-normal distributions and appropriate for coastal data.
    #
    # MATHEMATICAL APPROACH:
    # ---------------------
    # 1. Calculate quartiles: Q1, Q3 from elevation distribution
    # 2. Calculate IQR: IQR = Q3 - Q1
    # 3. Set outlier bounds:
    #    Lower bound: Q1 - 5.0 × IQR  (relaxed for coastal variability)
    #    Upper bound: Q3 + 5.0 × IQR
    # 4. Identify outliers: points where z < lower_bound ∨ z > upper_bound
    #
    # THRESHOLD JUSTIFICATION:
    # -----------------------
    # - Gap threshold (5×): Balances sensitivity with false positive reduction
    #   Based on survey data analysis showing natural spacing variation up to 3-4×
    # - Outlier IQR multiplier (5×): More conservative than standard 1.5×
    #   Accounts for natural elevation variability in coastal profiles
    #
    # REFERENCES:
    # ----------
    # - Tukey, J. W. (1977). Exploratory Data Analysis. Addison-Wesley.
    #   (IQR method for outlier detection)
    # - USACE (2015). Coastal Engineering Manual. Part III-2, Beach Profiles.
    #   (Gap detection in survey data)
    # - Larson, M., & Kraus, N. C. (1989). SBEACH: Numerical model for simulating
    #   storm-induced beach change. Technical Report CERC-89-9.
    #   (Data quality assessment methods)
    # - National Oceanic and Atmospheric Administration (NOAA) Coastal Zone
    #   Management Program. Survey data quality standards.
    #
    # LIMITATIONS:
    # -----------
    # - Gap detection assumes uniform expected spacing
    # - IQR method may miss outliers in multimodal distributions
    # - Thresholds are empirical and may need adjustment for different environments
    # - Does not account for systematic survey biases
    # =======================================================================

    gaps = []
    outliers = []

    for profile_name, profile_data in profiles.items():
        stats = common_ranges.get(profile_name)
        if not stats:
            continue

        avg_spacing = stats[3]  # avg_spacing is at index 3
        gap_threshold = avg_spacing * 5.0  # Flag gaps 5x larger than average

        # Collect all points across all surveys for this profile
        all_points = []
        for survey in profile_data:
            all_points.extend(survey)

        if len(all_points) < 2:
            continue

        # Sort points by X coordinate
        sorted_points = sorted(all_points, key=lambda p: p[0])

        # Detect gaps
        for i in range(1, len(sorted_points)):
            spacing = sorted_points[i][0] - sorted_points[i - 1][0]
            if spacing > gap_threshold:
                # Gap detected - use the midpoint X location
                gap_x = (sorted_points[i - 1][0] + sorted_points[i][0]) / 2
                gaps.append((profile_name, gap_x))

        # Detect elevation outliers using modified IQR method (less sensitive)
        elevations = [p[1] for p in sorted_points]
        if len(elevations) >= 10:  # Need more points for reliable outlier detection
            # Calculate IQR for outlier detection (more conservative for coastal profiles)
            q1 = np.percentile(elevations, 25)
            q3 = np.percentile(elevations, 75)
            iqr = q3 - q1
            lower_bound = (
                q1 - 5.0 * iqr
            )  # Increased from 3.0 to 5.0 for coastal profiles
            upper_bound = q3 + 5.0 * iqr

            # Find outliers
            for point in sorted_points:
                if point[1] < lower_bound or point[1] > upper_bound:
                    outliers.append((profile_name, point[0]))

    return gaps, outliers

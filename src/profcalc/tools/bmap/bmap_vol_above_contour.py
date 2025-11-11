# =============================================================================
# BMAP Volume Above Contour Calculation Tool
# =============================================================================
#
# FILE: src/profcalc/tools/bmap/bmap_vol_above_contour.py
#
# PURPOSE:
# This module computes the volume of material above a specified elevation
# contour within a beach profile. It provides quantitative estimates of
# sediment volumes above reference elevations, which is essential for
# understanding beach morphology, sediment budgets, and coastal management
# applications.
#
# WHAT IT'S FOR:
# - Calculating sediment volumes above specified elevation contours
# - Determining contour crossing locations for profile analysis
# - Supporting volumetric analysis for beach management decisions
# - Providing quantitative data for sediment budget calculations
# - Enabling contour-based morphological assessments
#
# WORKFLOW POSITION:
# This tool is used in volumetric analysis workflows to quantify sediment
# volumes relative to reference elevations. It's particularly important for
# assessing beach nourishment volumes, erosion monitoring, and sediment
# management planning.
#
# LIMITATIONS:
# - Provides single-profile volume calculations only
# - Assumes trapezoidal integration is adequate for volume estimation
# - Contour crossing detection depends on data resolution
# - Does not account for three-dimensional volume considerations
#
# ASSUMPTIONS:
# - Profile data is sorted and represents continuous morphology
# - Linear interpolation between points is appropriate
# - Contour elevations are meaningful reference levels
# - Integration spacing provides adequate accuracy
#
# =============================================================================

"""Minimal volume_above_contour module.

Provides a small, valid implementation of compute_volume_above_contour used
for tests and as a CLI helper in examples. Kept intentionally small so it can
be imported during repository migrations without pulling heavy dependencies.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np


def compute_volume_above_contour(
    profile: Any, contour: float, dx: float = 10.0
) -> Dict[str, float | None]:
    """Compute approximate volume above a contour for a single profile.

    Args:
        profile: object with numeric .x and .z sequences
        contour: elevation contour
        dx: grid spacing for interpolation/integration

    Returns:
        dict with x_on, x_off, volume_cuyd_per_ft, contour_x
    """
    x = np.asarray(profile.x, dtype=float)
    z = np.asarray(profile.z, dtype=float)
    order = np.argsort(x)
    x, z = x[order], z[order]

    xg = np.arange(float(np.min(x)), float(np.max(x)) + dx, dx)
    zg = np.interp(xg, x, z)

    h = np.maximum(0.0, zg - contour)
    area_ft3_per_ft = float(np.trapz(h, xg))
    area_cuyd_per_ft = area_ft3_per_ft / 27.0

    crossings = []
    for i in range(1, len(x)):
        a, b = z[i - 1] - contour, z[i] - contour
        if a * b < 0:
            frac = (contour - z[i - 1]) / (z[i] - z[i - 1])
            crossings.append(float(x[i - 1] + frac * (x[i] - x[i - 1])))
        elif a == 0:
            crossings.append(float(x[i - 1]))
        elif b == 0:
            crossings.append(float(x[i]))

    x_cross = max(crossings) if crossings else float("nan")

    return {
        "x_on": float(xg[0]),
        "x_off": float(x[-1]),
        "volume_cuyd_per_ft": float(area_cuyd_per_ft),
        "contour_x": float(x_cross) if np.isfinite(x_cross) else None,
    }

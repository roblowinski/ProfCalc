# =============================================================================
# BMAP Area and Volume Calculation Module
# =============================================================================
#
# FILE: src/profcalc/core/bmap_area_calcs.py
#
# PURPOSE:
# This module provides core computational functions for area and volume
# calculations in beach profile analysis. It implements the fundamental
# algorithms for computing cross-sectional changes and contour-based areas
# that form the basis of BMAP (Beach Morphology Analysis Package) analysis.
#
# WHAT IT'S FOR:
# - Calculating cross-sectional area changes between profile surveys
# - Computing areas above specified contour elevations
# - Handling XOn/XOff boundary restrictions for analysis regions
# - Supporting trapezoidal integration for accurate area calculations
# - Managing contour line intersections and interpolation
#
# WORKFLOW POSITION:
# This module provides the mathematical foundation for volumetric analysis
# in beach profile monitoring. It's used by higher-level analysis functions
# to compute erosion/accretion volumes and contour-based metrics that
# inform coastal management decisions.
#
# LIMITATIONS:
# - Assumes profiles are sorted by cross-shore distance
# - Trapezoidal integration may not be suitable for highly irregular data
# - Contour calculations require sufficient data density
# - XOn/XOff boundaries must be within profile extent
#
# ASSUMPTIONS:
# - Input coordinates are in consistent units
# - Profiles represent the same physical cross-section
# - Data is free of significant outliers or gaps
# - Contour elevations are meaningful for the analysis
#
# =============================================================================

from typing import List, Optional, Union

import numpy as np


# 1. Cross-Sectional Change Between Two Profiles
def cross_section_change(
    x: Union[List[float], np.ndarray],
    z1: Union[List[float], np.ndarray],
    z2: Union[List[float], np.ndarray],
) -> float:
    x, z1, z2 = map(np.array, (x, z1, z2))
    dz = z2 - z1
    delta_area = np.trapz(dz, x)
    return float(delta_area)


# 2. Volume Above a Contour
def area_above_contour_bmap(
    x: Union[List[float], np.ndarray],
    z: Union[List[float], np.ndarray],
    contour_elev: float,
    xon: Optional[float] = None,
    xoff: Optional[float] = None,
) -> float:
    x = np.asarray(x)
    z = np.asarray(z)
    idx = np.argsort(x)
    x, z = x[idx], z[idx]
    # Restrict to XOn/XOff if specified
    if xon is not None:
        xon = float(xon)
        mask = x >= xon
        x = x[mask]
        z = z[mask]
    if xoff is not None:
        xoff = float(xoff)
        mask = x <= xoff
        x = x[mask]
        z = z[mask]
    if len(x) < 2:
        return 0.0
    # Remove exact consecutive duplicate x
    xz = [(x[0], z[0])]
    for i in range(1, len(x)):
        if x[i] == x[i - 1]:
            continue
        xz.append((x[i], z[i]))
    x, z = np.array([p[0] for p in xz]), np.array([p[1] for p in xz])

    # Find crossings and insert contour points
    def insert_crossings(x: np.ndarray, z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        out_x, out_z = [x[0]], [z[0]]
        for i in range(1, len(x)):
            out_x.append(x[i])
            out_z.append(z[i])
            if (z[i - 1] - contour_elev) * (z[i] - contour_elev) < 0:
                frac = (contour_elev - z[i - 1]) / (z[i] - z[i - 1])
                x_cross = x[i - 1] + frac * (x[i] - x[i - 1])
                out_x.append(x_cross)
                out_z.append(contour_elev)
        return np.array(out_x), np.array(out_z)

    x, z = insert_crossings(x, z)
    z = np.maximum(z, contour_elev)
    return float(np.trapz(np.asarray(z) - contour_elev, x))

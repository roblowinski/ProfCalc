# =============================================================================
# Coordinate Reference System (CRS) Detection and Management
# =============================================================================
#
# FILE: src/profcalc/common/crs_utils.py
#
# PURPOSE:
# This module provides utilities for detecting and managing coordinate reference
# systems (CRS) in beach profile analysis. It specializes in automatically
# inferring state plane coordinate systems from sample data points, which is
# crucial for accurate geographic transformations in coastal engineering.
#
# WHAT IT'S FOR:
# - Automatically detects NAD83 state plane CRS from sample coordinates
# - Tests candidate CRS against geographic bounding boxes for accuracy
# - Provides conservative CRS inference to avoid incorrect assumptions
# - Supports New Jersey and Delaware state plane systems (common in coastal studies)
# - Handles optional pyproj dependency gracefully
# - Returns CRS objects and human-readable labels for identified systems
#
# WORKFLOW POSITION:
# This module is used during data import and processing phases when coordinate
# systems are not explicitly specified. It helps ensure that geographic
# transformations are performed with the correct CRS, preventing coordinate
# errors that could lead to incorrect profile analysis results.
#
# LIMITATIONS:
# - Currently limited to NJ and DE NAD83 state plane systems
# - Requires pyproj library for CRS operations (graceful degradation if unavailable)
# - Conservative detection may miss valid CRS in edge cases
# - Requires sufficient sample points for reliable detection
# - Geographic bounding box approach may not work for complex state boundaries
#
# ASSUMPTIONS:
# - Sample points are in a consistent projected coordinate system
# - State plane systems are NAD83-based with US survey feet
# - Geographic bounding boxes accurately represent state boundaries
# - Users have pyproj installed for full functionality
# - Coordinate data is numeric and properly formatted
#
# =============================================================================

"""
CRS utility helpers.

Provides helpers to infer likely state-plane CRS from projected XY samples.

The primary function `infer_state_plane_crs_from_samples` tries a small set
of candidate EPSG codes (New Jersey and Delaware NAD83 state-plane in US
survey feet) and transforms sample points to geographic coordinates to test
which CRS produces lat/lon inside the expected state bounding box.

This is intentionally conservative and returns None when detection is
ambiguous or pyproj is not available.
"""

from typing import Any, Iterable, Optional, Tuple

try:
    from pyproj import CRS, Transformer
except ImportError:  # pragma: no cover - optional dependency
    CRS = None  # type: ignore
    Transformer = None  # type: ignore


def infer_state_plane_crs_from_samples(
    samples: Iterable[Tuple[float, float]],
) -> Tuple[Optional[Any], Optional[str]]:
    """Try to infer whether samples are in NJ or DE NAD83 state-plane (ftUS).

    Args:
        samples: Iterable of (easting, northing) sample tuples.

    Returns:
        Tuple of (pyproj.CRS object or None, label string like 'NJ'/'DE' or None).
    """
    if CRS is None or Transformer is None:
        return None, None

    # Small set of candidate EPSG codes for NAD83 (US survey foot) state planes
    candidates = [
        (
            3424,
            "NJ",
            (-75.6, 38.87, -73.88, 41.36),
        ),  # EPSG:3424 NAD83 / New Jersey (ftUS)
        (
            2235,
            "DE",
            (-79.49, 37.97, -74.97, 39.85),
        ),  # EPSG:2235 NAD83 / Delaware (ftUS)
    ]

    pts = []
    for x, y in samples:
        try:
            xf = float(x)
            yf = float(y)
            pts.append((xf, yf))
        except (ValueError, TypeError):
            continue
        if len(pts) >= 10:
            break

    if not pts:
        return None, None

    best_score = 0.0
    best: Tuple[Optional[Any], Optional[str]] = (None, None)

    for epsg, label, bbox in candidates:
        try:
            crs = CRS.from_epsg(epsg)
            transformer = Transformer.from_crs(crs, CRS.from_epsg(4326), always_xy=True)
            lons, lats = transformer.transform([p[0] for p in pts], [p[1] for p in pts])
            inside = 0
            for lon, lat in zip(lons, lats):
                if bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]:
                    inside += 1
            score = inside / len(pts)
            if score > best_score:
                best_score = score
                best = (crs, label)
        except (ImportError, RuntimeError, ValueError, TypeError):
            continue

    # require a majority of samples to fall inside the bbox to accept
    if best_score >= 0.6:
        return best
    return None, None

"""Annual Erosion Rate (AER) utilities.

This module computes volume change between two
cross-shore profiles to derive an Annual Erosion Rate (AER).

The implementation focuses on the numeric steps:
- interpolate two profiles to a common cross-shore grid
- compute cut (material removed) and fill (material added) separately by
  integrating positive/negative differences
- return per-foot (alongshore) volume changes in cubic yards and a
  computed AER (cuyd/ft/yr) when a time delta is provided

Notes on sign convention:
- We compute diff = z_before - z_after. Positive diff means the earlier
  profile was higher (material removed -> cut). We return separate
  `cut_cuyd_per_ft` and `fill_cuyd_per_ft` (both positive numbers).
- `all_cuyd_per_ft` is defined as (fill - cut) = net accretion (cuyd/ft).

This module is intentionally small and well-typed so it can be reused by
CLI/menu code and unit tests.
"""
from __future__ import annotations

import datetime as _dt
import math
from typing import Any, Dict, Iterable, Optional, Tuple

import numpy as np

FT3_TO_CUYD = 1.0 / 27.0


def _to_numpy(x: Iterable[float]) -> np.ndarray:
    return np.asarray(list(x), dtype=float)


def interpolate_to_common_grid(
    x1: Iterable[float],
    z1: Iterable[float],
    x2: Iterable[float],
    z2: Iterable[float],
    dx: float = 0.1,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Interpolate two profiles onto a common uniformly spaced x-grid.

    Args:
        x1, z1: coordinates for profile 1 (before)
        x2, z2: coordinates for profile 2 (after)
        dx: target grid spacing in same units as x (default 0.1)

    Returns:
        x_common, z1i, z2i: numpy arrays of the common x-grid and the
        interpolated z-values for each profile.
    """
    xa = _to_numpy(x1)
    za = _to_numpy(z1)
    xb = _to_numpy(x2)
    zb = _to_numpy(z2)

    # Validate dx early to provide a clear error for invalid spacing
    try:
        if not math.isfinite(dx) or dx <= 0:
            raise ValueError("dx must be a positive finite number")
    except TypeError:
        raise ValueError("dx must be a positive finite number")

    if xa.size < 2 or xb.size < 2:
        raise ValueError("Each profile must contain at least two points")

    x_min = float(min(xa.min(), xb.min()))
    x_max = float(max(xa.max(), xb.max()))
    if not math.isfinite(x_min) or not math.isfinite(x_max):
        raise ValueError("Non-finite coordinates in profiles")

    num = max(2, int(math.floor((x_max - x_min) / float(dx))) + 1)
    x_common = np.linspace(x_min, x_max, num=num, dtype=float)

    z1i = np.interp(x_common, xa, za)
    z2i = np.interp(x_common, xb, zb)

    return x_common, z1i, z2i


def cut_fill_per_ft(
    x: Iterable[float],
    z_before: Iterable[float],
    z_after: Iterable[float],
    *,
    use_bmap_core: bool = False,
) -> Dict[str, float]:
    """Compute cut and fill volumes per foot alongshore between two
    interpolated profiles.

    The profiles must be defined on the same x-grid and have the same
    length.

    Returns a dict with keys:
      - cut_cuyd_per_ft: cubic yards per foot removed (positive)
      - fill_cuyd_per_ft: cubic yards per foot added (positive)
      - all_cuyd_per_ft: net accretion (fill - cut) in cuyd/ft (signed)

    Algorithm: trapezoidal integration of diff = z_before - z_after; areas
    where diff>0 contribute to `cut`, where diff<0 contribute to `fill`.
    """
    x_arr = _to_numpy(x)
    za = _to_numpy(z_before)
    zb = _to_numpy(z_after)
    if x_arr.size != za.size or x_arr.size != zb.size:
        raise ValueError("x, z_before and z_after must have the same length")

    # differences in elevation (ft)
    diff = za - zb

    # integrate by trapezoid rule across adjacent segments
    cut_ft3 = 0.0
    fill_ft3 = 0.0
    if use_bmap_core:
        # Use existing BMAP split_trap_area logic for datum-aware splitting.
        from profcalc.tools.bmap.bmap_cut_fill import split_trap_area

        for i in range(x_arr.size - 1):
            xa = float(x_arr[i])
            xb = float(x_arr[i + 1])
            dz_a = float(diff[i])
            dz_b = float(diff[i + 1])
            if xb <= xa:
                continue
            area_above, area_below = split_trap_area(xa, xb, dz_a, dz_b)
            # area_above corresponds to positive diff (cut), area_below to negative (fill)
            cut_ft3 += float(area_above)
            fill_ft3 += float(area_below)
    else:
        for i in range(x_arr.size - 1):
            dx = float(x_arr[i + 1] - x_arr[i])
            if dx <= 0:
                # skip degenerate or backwards segments
                continue
            # trapezoid area (ft^2)
            area = 0.5 * (diff[i] + diff[i + 1]) * dx
            if area > 0:
                # positive area -> earlier profile higher -> cut (erosion)
                cut_ft3 += area  # ft^2 * 1 ft alongshore -> ft^3
            else:
                fill_ft3 += -area

    cut_cuyd = cut_ft3 * FT3_TO_CUYD
    fill_cuyd = fill_ft3 * FT3_TO_CUYD
    all_cuyd = fill_cuyd - cut_cuyd

    return {
        "cut_cuyd_per_ft": float(cut_cuyd),
        "fill_cuyd_per_ft": float(fill_cuyd),
        "all_cuyd_per_ft": float(all_cuyd),
    }


def years_between(date1: _dt.date, date2: _dt.date) -> float:
    """Return fractional years between two dates using a 365.25-day year."""
    if not isinstance(date1, _dt.date) or not isinstance(date2, _dt.date):
        raise TypeError("date1 and date2 must be datetime.date instances")
    delta = abs((date2 - date1).days)
    return float(delta) / 365.25


def calculate_aer(
    x_before: Iterable[float],
    z_before: Iterable[float],
    x_after: Iterable[float],
    z_after: Iterable[float],
    date_before: Optional[_dt.date] = None,
    date_after: Optional[_dt.date] = None,
    dx: float = 0.1,
    *,
    use_bmap_core: bool = False,
) -> Dict[str, Any]:
    """Compute AER and intermediary values between two cross-shore profiles.

    Args:
        x_before, z_before: coordinates for the earlier profile
        x_after, z_after: coordinates for the later profile
        date_before, date_after: optional dates to compute years delta. If
            both are provided, `aer_cuyd_per_ft_per_yr` will be included in
            the result. If not provided, AER is set to NaN.
        dx: interpolation spacing for the common grid (default 0.1)

    Returns a dict with keys:
        x_common: numpy array of common x-grid (not JSON serializable)
        cut_cuyd_per_ft, fill_cuyd_per_ft, all_cuyd_per_ft
        years: computed years (or NaN)
        aer_cuyd_per_ft_per_yr: AER (signed) or NaN when dates are missing

    """
    x_common, z1i, z2i = interpolate_to_common_grid(x_before, z_before, x_after, z_after, dx=dx)

    vols = cut_fill_per_ft(x_common, z1i, z2i, use_bmap_core=use_bmap_core)

    if date_before is not None and date_after is not None:
        yrs = years_between(date_before, date_after)
        if yrs <= 0:
            aer = float("nan")
        else:
            # follow MATLAB sign: AER = - all_cuyd_per_ft / years
            aer = -vols["all_cuyd_per_ft"] / yrs
    else:
        yrs = float("nan")
        aer = float("nan")

    result: Dict[str, Any] = {
        "cut_cuyd_per_ft": vols["cut_cuyd_per_ft"],
        "fill_cuyd_per_ft": vols["fill_cuyd_per_ft"],
        "all_cuyd_per_ft": vols["all_cuyd_per_ft"],
        "years": float(yrs),
        "aer_cuyd_per_ft_per_yr": float(aer),
    }
    # include x_common for callers that want to inspect the grid
    # but keep it under a non-serializable key name to indicate it is
    # a numpy array
    result["_x_common"] = x_common  # type: ignore[index]
    return result

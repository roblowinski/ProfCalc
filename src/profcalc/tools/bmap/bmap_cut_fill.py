"""
cut_fill_detailed.py
--------------------
Replicates the BMAP "Cut and Fill" tool, including the detailed per-cell table.

Behavior:
- User selects two profiles (by name/date/desc)
- Datum fixed at 0.00 ft
- Xon = landward-most x common to both profiles
- Xoff = seaward-most x common to both profiles
- Profiles are interpolated to a uniform grid with spacing dX (default = 10 ft)
- Volumes integrated with trapezoidal rule
- Report format matches BMAP's Cut & Fill report

Example:
    python tool_cut_fill.py \
      --input1 ../../data/input_examples/OCNJ_FreeFormat_Test.txt \
      --sel1 "OC118 21SEP2021 (AME)" \
      --input2 ../../data/input_examples/OCNJ_FreeFormat_Test.txt \
      --sel2 "OC118 16SEP2022 (AME)" \
      --output ../../data/output_examples/OCNJ_CutFill_Detailed.txt \
      --title "Untitled"
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional, Tuple

import numpy as np
from scipy.interpolate import UnivariateSpline  # type: ignore

from profcalc.common.bmap_io import read_bmap_freeformat
from profcalc.common.config_utils import get_dx
from profcalc.common.error_handler import LogComponent, get_logger
from profcalc.common.io_reports import write_cutfill_detailed_report

# --- Ensure src/ is in sys.path for direct script execution ---
_project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
_src_path = os.path.join(_project_root, "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# Helper: Cubic spline smoothing


def smooth_profile(
    x: np.ndarray, z: np.ndarray, smoothing_factor: Optional[float] = None
) -> np.ndarray:
    """
    Smooth a profile using cubic spline smoothing (UnivariateSpline) or linear.
    Parameters:
        x (np.ndarray): X coordinates (must be sorted)
        z (np.ndarray): Z values
        smoothing_factor (float or None): Spline smoothing factor. If None, compute dynamically. If 0, use linear interpolation.
    Returns:
        np.ndarray: Smoothed Z values at original Xs
    """
    if smoothing_factor == 0:
        # Use linear interpolation (no spline)
        return z
    if smoothing_factor is None:
        # Dynamic smoothing: proportional to profile noise and length
        dz = np.diff(z)
        noise = np.std(dz)
        n = len(x)
        # Heuristic: s = k * noise^2 * n, k ~ 1.0 (tune as needed)
        k = 1.0
        s = k * (noise**2) * n
    else:
        s = smoothing_factor
    spline = UnivariateSpline(x, z, s=s)
    return np.asarray(spline(x))


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------


def _header_string(p) -> str:
    parts = [p.name]
    if p.date:
        parts.append(p.date)
    if p.description:
        parts.append(p.description)
    return " ".join(parts).strip()


def _select_profile(profiles, selector: str):
    sel = selector.strip().lower()
    for p in profiles:
        if _header_string(p).lower() == sel:
            return p
    for p in profiles:
        if _header_string(p).lower().startswith(sel):
            return p
    raise ValueError(f"No profile matched selector: '{selector}'")


def _ensure_sorted(
    x: np.ndarray, z: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    idx = np.argsort(x)
    return x[idx], z[idx]


def _overlap_bounds(x1: np.ndarray, x2: np.ndarray) -> Tuple[float, float]:
    x1min, x1max = float(np.min(x1)), float(np.max(x1))
    x2min, x2max = float(np.min(x2)), float(np.max(x2))
    x_on = max(x1min, x2min)
    x_off = min(x1max, x2max)
    if x_on >= x_off:
        raise ValueError(
            "Profiles do not overlap in X; cannot compute Cut/Fill."
        )
    return x_on, x_off


def _shoreline_x(x: np.ndarray, z: np.ndarray) -> Optional[float]:
    """Seaward-most crossing with z=0. Returns None if no crossing."""
    # Ensure x and z are arrays with at least two points
    if (
        np.isscalar(x)
        or np.isscalar(z)
        or len(np.atleast_1d(x)) < 2
        or len(np.atleast_1d(z)) < 2
    ):
        return None
    x, z = _ensure_sorted(x, z)
    xr = None
    for i in range(1, len(x)):
        z1, z2 = z[i - 1], z[i]
        if z1 == 0.0:
            xr = x[i - 1]
        if (z1 * z2) < 0.0:
            frac = -z1 / (z2 - z1)
            xr = x[i - 1] + frac * (x[i] - x[i - 1])
        if z2 == 0.0:
            xr = x[i]
    return xr


# Module-level helper: split trapezoid area across datum (z=0)
def split_trap_area(
    xa: float, xb: float, za: float, zb: float
) -> tuple[float, float]:
    """Return (area_above, area_below) for trapezoid between xa..xb with end elevations za, zb.
    Splits at z=0 when crossing the datum.
    """
    if za >= 0 and zb >= 0:
        return 0.5 * (za + zb) * (xb - xa), 0.0
    elif za <= 0 and zb <= 0:
        return 0.0, 0.5 * (za + zb) * (xb - xa)
    else:
        # Crosses datum, split at zero
        frac = -za / (zb - za)
        x_cross = xa + frac * (xb - xa)
        area1 = 0.5 * (za + 0) * (x_cross - xa)
        area2 = 0.5 * (0 + zb) * (xb - x_cross)
        if za > 0:
            return area1, area2
        else:
            return area2, area1


# ---------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------


def compute_cut_fill_detailed(
    p1,
    p2,
    title: str,
    output_path: str,
    dx: float = 10.0,
    smoothing: Optional[float] = None,
    use_ported_logic: bool = False,
):
    # Sort and restrict to overlapping X range
    x1, z1 = _ensure_sorted(p1.x, p1.z)
    x2, z2 = _ensure_sorted(p2.x, p2.z)
    x_on, x_off = _overlap_bounds(x1, x2)

    # Apply cubic spline smoothing to both profiles
    z1_smoothed = smooth_profile(x1, z1, smoothing)
    z2_smoothed = smooth_profile(x2, z2, smoothing)

    # Helper for BMAP-style flat extension/interp (now uses smoothed profiles)
    def interp_or_flat(x, z, xq):
        if xq <= x[0]:
            return z[0]
        if xq >= x[-1]:
            return z[-1]
        return float(np.interp(xq, x, z))

    # Use smoothed profiles for all subsequent logic
    z1, z2 = z1_smoothed, z2_smoothed

    if use_ported_logic:
        # --- Ported logic from ProfileAnalysis_v129.py ---
        xs1, ys1 = x1, z1
        xs2, ys2 = x2, z2
        xs_all = np.array(sorted(set(xs1) | set(xs2)))
        y1_interp = np.array([interp_or_flat(xs1, ys1, x) for x in xs_all])
        y2_interp = np.array([interp_or_flat(xs2, ys2, x) for x in xs_all])
        # Cell boundaries: intersections and endpoints only
        dz_all = y2_interp - y1_interp
        intersection_xs = []
        for i in range(1, len(xs_all)):
            if dz_all[i - 1] * dz_all[i] < 0.0:
                frac = -dz_all[i - 1] / (dz_all[i] - dz_all[i - 1])
                x_cross = xs_all[i - 1] + frac * (xs_all[i] - xs_all[i - 1])
                intersection_xs.append(x_cross)
        cell_boundaries = (
            [x_on]
            + sorted([x for x in intersection_xs if x_on < x < x_off])
            + [x_off]
        )
        z1_cb = np.array(
            [interp_or_flat(xs1, ys1, x) for x in cell_boundaries]
        )
        z2_cb = np.array(
            [interp_or_flat(xs2, ys2, x) for x in cell_boundaries]
        )
        # The rest of the ported logic can now use cell_boundaries, z1_cb, z2_cb
        # (Replace all uses of cell_edges, y1_interp, y2_interp with these)
        # Δz and per-cell volume (variable-width cells)
        dz_cb = z2_cb - z1_cb
        nseg = len(cell_boundaries) - 1
        cell_vol_ft3_per_ft: np.ndarray = np.empty(nseg, dtype=float)
        cell_vol_cuyd_per_ft: np.ndarray = np.empty(nseg, dtype=float)
        cell_thickness: np.ndarray = np.empty(nseg, dtype=float)
        for i in range(nseg):
            width = cell_boundaries[i + 1] - cell_boundaries[i]
            dz_a = dz_cb[i]
            dz_b = dz_cb[i + 1]
            vol_ft3 = 0.5 * (dz_a + dz_b) * width
            cell_vol_ft3_per_ft[i] = vol_ft3
            cell_vol_cuyd_per_ft[i] = vol_ft3 / 27.0
            cell_thickness[i] = 0.5 * (dz_a + dz_b)

        # Running totals
        cum_vol: np.ndarray = np.cumsum(cell_vol_cuyd_per_ft)
        gross_vol: np.ndarray = np.cumsum(np.abs(cell_vol_cuyd_per_ft))

        # Above and below datum volumes (z=0) with datum-splitting for each cell
        def split_cell_at_datum(x0, x1, z1_0, z2_0, z1_1, z2_1):
            # Returns list of (x_start, x_end, z1_start, z2_start, z1_end, z2_end) for sub-cells split at z=0
            # Linear interpolation for z=0 crossing
            result = []
            # Check for crossings in either profile
            crossings = []
            for z_start, z_end in [(z1_0, z1_1), (z2_0, z2_1)]:
                if (z_start < 0 and z_end > 0) or (z_start > 0 and z_end < 0):
                    frac = -z_start / (z_end - z_start)
                    x_cross = x0 + frac * (x1 - x0)
                    crossings.append(x_cross)
            # Remove duplicates and sort
            crossings = sorted(set([x0, x1] + crossings))
            # Build sub-cells
            for i in range(len(crossings) - 1):
                xa, xb = crossings[i], crossings[i + 1]

                # Interpolate z1, z2 at xa, xb
                def interp_z(z0, z1, x0, x1, x):
                    if x1 == x0:
                        return z0
                    return z0 + (z1 - z0) * (x - x0) / (x1 - x0)

                za1 = interp_z(z1_0, z1_1, x0, x1, xa)
                za2 = interp_z(z2_0, z2_1, x0, x1, xa)
                zb1 = interp_z(z1_0, z1_1, x0, x1, xb)
                zb2 = interp_z(z2_0, z2_1, x0, x1, xb)
                result.append((xa, xb, za1, za2, zb1, zb2))
            return result

        # BMAP-style: For each segment (split at datum if needed),
        #   Above datum: (Template above datum) - (BD above datum)
        #   Below datum: (BD below datum) - (Template below datum)
        def area_above(z0, z1, x0, x1):
            if z0 > 0 and z1 > 0:
                return 0.5 * (z0 + z1) * (x1 - x0)
            elif z0 > 0 and z1 <= 0:
                frac = z0 / (z0 - z1)
                x_cross = x0 + frac * (x1 - x0)
                return 0.5 * (z0 + 0.0) * (x_cross - x0)
            elif z0 <= 0 and z1 > 0:
                frac = -z0 / (z1 - z0)
                x_cross = x0 + frac * (x1 - x0)
                return 0.5 * (0.0 + z1) * (x1 - x_cross)
            else:
                return 0.0

        def area_below(z0, z1, x0, x1):
            if z0 < 0 and z1 < 0:
                return 0.5 * (z0 + z1) * (x1 - x0)
            elif z0 < 0 and z1 >= 0:
                frac = -z0 / (z1 - z0)
                x_cross = x0 + frac * (x1 - x0)
                return 0.5 * (z0 + 0.0) * (x_cross - x0)
            elif z0 >= 0 and z1 < 0:
                frac = z0 / (z0 - z1)
                x_cross = x0 + frac * (x1 - x0)
                return 0.5 * (0.0 + z1) * (x1 - x_cross)
            else:
                return 0.0

        above_sum = 0.0
        below_sum = 0.0
        for i in range(len(cell_boundaries) - 1):
            x0, x1 = cell_boundaries[i], cell_boundaries[i + 1]
            # Template (profile 1)
            zt0, zt1 = z1_cb[i], z1_cb[i + 1]
            # BD (profile 2)
            zb0, zb1 = z2_cb[i], z2_cb[i + 1]
            # Above datum: (Template above datum) - (BD above datum)
            above_sum += area_above(zt0, zt1, x0, x1) - area_above(
                zb0, zb1, x0, x1
            )
            # Below datum: (BD below datum) - (Template below datum)
            below_sum += area_below(zb0, zb1, x0, x1) - area_below(
                zt0, zt1, x0, x1
            )
        above_cuyd_per_ft = above_sum / 27.0
        below_cuyd_per_ft = below_sum / 27.0

        total_cuyd_per_ft = float(np.sum(cell_vol_cuyd_per_ft))

        # Shoreline intersection (seaward-most crossing)
        xs1_sh: Optional[float] = _shoreline_x(xs1, ys1)
        xs2_sh: Optional[float] = _shoreline_x(xs2, ys2)
        if xs1_sh is not None and xs2_sh is not None:
            sh_change = float(xs2_sh - xs1_sh)
            xs1_out, xs2_out = float(xs1_sh), float(xs2_sh)
        else:
            sh_change = float("nan")
            xs1_out, xs2_out = float("nan"), float("nan")

        # Build cell table with above/below datum split for each sub-cell

        cells = []
        for i in range(nseg):
            x0, x1_ = cell_boundaries[i], cell_boundaries[i + 1]
            dz0, dz1_ = dz_cb[i], dz_cb[i + 1]
            z1a, z1b = z1_cb[i], z1_cb[i + 1]
            z2a, z2b = z2_cb[i], z2_cb[i + 1]
            width = x1_ - x0
            vol_cuyd = cell_vol_cuyd_per_ft[i]
            # For each profile
            abv1, blw1 = split_trap_area(x0, x1_, z1a, z1b)
            abv2, blw2 = split_trap_area(x0, x1_, z2a, z2b)
            # For difference (z2-z1), net area, above datum, below datum
            dz_a, dz_b = dz0, dz1_
            abv_d, blw_d = split_trap_area(x0, x1_, dz_a, dz_b)
            net_d = abv_d + blw_d
            cells.append(
                {
                    "end_x": float(x1_),
                    "end_z2": float(z2b),
                    "cell_vol_cuyd_per_ft": float(vol_cuyd),
                    "cell_thickness_ft": float(0.5 * (dz_a + dz_b)),
                    "cum_vol_cuyd_per_ft": float(cum_vol[i]),
                    "gross_vol_cuyd_per_ft": float(gross_vol[i]),
                    "z1_above": float(abv1),
                    "z1_below": float(blw1),
                    "z2_above": float(abv2),
                    "z2_below": float(blw2),
                    "dz_above": float(abv_d),
                    "dz_below": float(blw_d),
                    "dz_net": float(net_d),
                }
            )

        # Write report
        write_cutfill_detailed_report(
            output_path,
            title=title,
            profile1_label=_header_string(p1),
            profile2_label=_header_string(p2),
            x_on=float(x_on),
            x_off=float(x_off),
            above_datum_cuyd_per_ft=above_cuyd_per_ft,
            below_datum_cuyd_per_ft=below_cuyd_per_ft,
            total_volume_cuyd_per_ft=total_cuyd_per_ft,
            shoreline_from_x=xs1_out,
            shoreline_to_x=xs2_out,
            shoreline_change=sh_change,
            cells=cells,
        )
        return

    # --- Hybrid logic: BMAP-style cell boundaries, original above/below datum logic ---
    if getattr(sys.modules[__name__], "use_hybrid_logic", False):
        use_intersections_only = getattr(
            sys.modules[__name__], "hybrid_intersections_only", False
        )
        # Build cell boundaries at all unique x-values, intersection points, and datum crossings
        xs1, ys1 = x1, z1
        xs2, ys2 = x2, z2
        xs_all = np.array(sorted(set(xs1) | set(xs2)))
        y1_interp = np.array([interp_or_flat(xs1, ys1, x) for x in xs_all])
        y2_interp = np.array([interp_or_flat(xs2, ys2, x) for x in xs_all])
        dz_all = y2_interp - y1_interp
        intersection_xs = []
        for i in range(1, len(xs_all)):
            if dz_all[i - 1] * dz_all[i] < 0.0:
                frac = -dz_all[i - 1] / (dz_all[i] - dz_all[i - 1])
                x_cross = xs_all[i - 1] + frac * (xs_all[i] - xs_all[i - 1])
                intersection_xs.append(x_cross)
        use_datum_only = getattr(
            sys.modules[__name__], "hybrid_datum_only", False
        )
        if use_intersections_only:
            cell_boundaries = (
                [x_on]
                + sorted([x for x in set(intersection_xs) if x_on < x < x_off])
                + [x_off]
            )
        elif use_datum_only:
            datum_xs = []
            for arr in [y1_interp, y2_interp]:
                for i in range(1, len(xs_all)):
                    if arr[i - 1] * arr[i] < 0.0:
                        frac = -arr[i - 1] / (arr[i] - arr[i - 1])
                        x_cross = xs_all[i - 1] + frac * (
                            xs_all[i] - xs_all[i - 1]
                        )
                        datum_xs.append(x_cross)
            cell_boundaries = (
                [x_on]
                + sorted([x for x in set(datum_xs) if x_on < x < x_off])
                + [x_off]
            )
        else:
            # Datum crossings for each profile
            datum_xs = []
            for arr in [y1_interp, y2_interp]:
                for i in range(1, len(xs_all)):
                    if arr[i - 1] * arr[i] < 0.0:
                        frac = -arr[i - 1] / (arr[i] - arr[i - 1])
                        x_cross = xs_all[i - 1] + frac * (
                            xs_all[i] - xs_all[i - 1]
                        )
                        datum_xs.append(x_cross)
            cell_boundaries = (
                [x_on]
                + sorted(
                    [
                        x
                        for x in set(intersection_xs + datum_xs)
                        if x_on < x < x_off
                    ]
                )
                + [x_off]
            )
        z1_cb = np.array(
            [interp_or_flat(xs1, ys1, x) for x in cell_boundaries]
        )
        z2_cb = np.array(
            [interp_or_flat(xs2, ys2, x) for x in cell_boundaries]
        )
        dz_cb = z2_cb - z1_cb
        nseg = len(cell_boundaries) - 1
        cell_vol_ft3_per_ft = np.empty(nseg, dtype=float)
        cell_vol_cuyd_per_ft = np.empty(nseg, dtype=float)
        cell_thickness = np.empty(nseg, dtype=float)
        for i in range(nseg):
            width = cell_boundaries[i + 1] - cell_boundaries[i]
            dz_a = dz_cb[i]
            dz_b = dz_cb[i + 1]
            vol_ft3 = 0.5 * (dz_a + dz_b) * width
            cell_vol_ft3_per_ft[i] = vol_ft3
            cell_vol_cuyd_per_ft[i] = vol_ft3 / 27.0
            cell_thickness[i] = 0.5 * (dz_a + dz_b)
        cum_vol = np.cumsum(cell_vol_cuyd_per_ft)
        gross_vol = np.cumsum(np.abs(cell_vol_cuyd_per_ft))
        above_datum = 0.0
        below_datum = 0.0
        reverse_sign = getattr(
            sys.modules[__name__], "hybrid_reverse_sign", False
        )
        total_volume = 0.0
        cumulative_volume = 0.0
        gross_volume = 0.0
        cells = []
        for i in range(nseg):
            x0, x1_ = cell_boundaries[i], cell_boundaries[i + 1]
            bd_start = z1_cb[i]
            bd_end = z1_cb[i + 1]
            tmpl_start = z2_cb[i]
            tmpl_end = z2_cb[i + 1]
            avg_elev = (bd_start + bd_end + tmpl_start + tmpl_end) / 4
            cell_volume_cy = cell_vol_cuyd_per_ft[i]
            if reverse_sign:
                if avg_elev >= 0.0:
                    below_datum += cell_volume_cy
                else:
                    above_datum += cell_volume_cy
            else:
                if avg_elev >= 0.0:
                    above_datum += cell_volume_cy
                else:
                    below_datum += cell_volume_cy
            total_volume += cell_volume_cy
            cumulative_volume += cell_volume_cy
            gross_volume += abs(cell_volume_cy)
            cells.append(
                {
                    "end_x": float(x1_),
                    "end_z2": float(tmpl_end),
                    "cell_vol_cuyd_per_ft": float(cell_volume_cy),
                    "cell_thickness_ft": float(cell_thickness[i]),
                    "cum_vol_cuyd_per_ft": float(cum_vol[i]),
                    "gross_vol_cuyd_per_ft": float(gross_vol[i]),
                }
            )
        # Shoreline intersection (seaward-most crossing)
        xs1_sh = _shoreline_x(xs1, ys1)
        xs2_sh = _shoreline_x(xs2, ys2)
        if xs1_sh is not None and xs2_sh is not None:
            sh_change = float(xs2_sh - xs1_sh)
            xs1_out, xs2_out = float(xs1_sh), float(xs2_sh)
        else:
            sh_change = float("nan")
            xs1_out, xs2_out = float("nan"), float("nan")
        write_cutfill_detailed_report(
            output_path,
            title=title,
            profile1_label=_header_string(p1),
            profile2_label=_header_string(p2),
            x_on=float(x_on),
            x_off=float(x_off),
            above_datum_cuyd_per_ft=above_datum,
            below_datum_cuyd_per_ft=below_datum,
            total_volume_cuyd_per_ft=total_volume,
            shoreline_from_x=xs1_out,
            shoreline_to_x=xs2_out,
            shoreline_change=sh_change,
            cells=cells,
        )
        return

    # --- Original logic: uniform grid (dx) with datum splitting ---
    # All variables scoped inside this block to avoid redefinition errors
    x_grid = np.arange(x_on, x_off + dx, dx)
    if x_grid[-1] > x_off:
        x_grid[-1] = x_off
    # Add datum crossings to x_grid
    datum_xs = []
    for x_arr, z_arr in [(x1, z1_smoothed), (x2, z2_smoothed)]:
        for i in range(1, len(z_arr)):
            if z_arr[i - 1] * z_arr[i] < 0:
                frac = -z_arr[i - 1] / (z_arr[i] - z_arr[i - 1])
                x_cross = x_arr[i - 1] + frac * (x_arr[i] - x_arr[i - 1])
                if x_on < x_cross < x_off:
                    datum_xs.append(x_cross)
    x_grid = np.sort(np.concatenate([x_grid, datum_xs]))
    x_grid = np.unique(x_grid)
    nseg = len(x_grid) - 1
    z1_grid = np.array([interp_or_flat(x1, z1_smoothed, x) for x in x_grid])
    z2_grid = np.array([interp_or_flat(x2, z2_smoothed, x) for x in x_grid])
    dz_grid = z2_grid - z1_grid
    cell_vol_ft3_per_ft = np.empty(nseg, dtype=float)
    cell_vol_cuyd_per_ft = np.empty(nseg, dtype=float)
    cell_thickness = np.empty(nseg, dtype=float)
    for i in range(nseg):
        width = x_grid[i + 1] - x_grid[i]
        dz_a = dz_grid[i]
        dz_b = dz_grid[i + 1]
        vol_ft3 = 0.5 * (dz_a + dz_b) * width
        cell_vol_ft3_per_ft[i] = vol_ft3
        cell_vol_cuyd_per_ft[i] = vol_ft3 / 27.0
        cell_thickness[i] = 0.5 * (dz_a + dz_b)
    cum_vol = np.cumsum(cell_vol_cuyd_per_ft)
    gross_vol = np.cumsum(np.abs(cell_vol_cuyd_per_ft))
    above_datum = 0.0
    below_datum = 0.0
    total_volume = 0.0
    cumulative_volume = 0.0
    gross_volume = 0.0
    cells = []

    # Use module-level split_trap_area directly

    for i in range(nseg):
        x0, x1_ = x_grid[i], x_grid[i + 1]
        bd_start = z1_grid[i]
        bd_end = z1_grid[i + 1]
        tmpl_start = z2_grid[i]
        tmpl_end = z2_grid[i + 1]
        cell_volume_cy = cell_vol_cuyd_per_ft[i]
        # Split each profile at datum and compute net above/below areas
        abv1, blw1 = split_trap_area(x0, x1_, bd_start, bd_end)
        abv2, blw2 = split_trap_area(x0, x1_, tmpl_start, tmpl_end)
        above_datum += (abv2 - abv1) / 27.0
        below_datum += (blw2 - blw1) / 27.0
        total_volume += cell_volume_cy
        cumulative_volume += cell_volume_cy
        gross_volume += abs(cell_volume_cy)
        cells.append(
            {
                "end_x": float(x1_),
                "end_z2": float(tmpl_end),
                "cell_vol_cuyd_per_ft": float(cell_volume_cy),
                "cell_thickness_ft": float(cell_thickness[i]),
                "cum_vol_cuyd_per_ft": float(cum_vol[i]),
                "gross_vol_cuyd_per_ft": float(gross_vol[i]),
            }
        )
    # Shoreline intersection (seaward-most crossing)
    xs1_sh = _shoreline_x(x1, z1)
    xs2_sh = _shoreline_x(x2, z2)
    if xs1_sh is not None and xs2_sh is not None:
        sh_change = float(xs2_sh - xs1_sh)
        xs1_out, xs2_out = float(xs1_sh), float(xs2_sh)
    else:
        sh_change = float("nan")
        xs1_out, xs2_out = float("nan"), float("nan")
    write_cutfill_detailed_report(
        output_path,
        title=title,
        profile1_label=_header_string(p1),
        profile2_label=_header_string(p2),
        x_on=float(x_on),
        x_off=float(x_off),
        above_datum_cuyd_per_ft=above_datum,
        below_datum_cuyd_per_ft=below_datum,
        total_volume_cuyd_per_ft=total_volume,
        shoreline_from_x=xs1_out,
        shoreline_to_x=xs2_out,
        shoreline_change=sh_change,
        cells=cells,
    )


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(
        description="BMAP-style Cut & Fill (detailed) for two selected profiles."
    )
    ap.add_argument(
        "--input1",
        required=True,
        help="BMAP Free Format file containing Profile 1",
    )
    ap.add_argument(
        "--sel1",
        required=True,
        help='Selector for Profile 1 (e.g., "OC118 21SEP2021")',
    )
    ap.add_argument(
        "--input2",
        required=False,
        help="Optional second file containing Profile 2 (defaults to input1)",
    )
    ap.add_argument(
        "--sel2",
        required=True,
        help='Selector for Profile 2 (e.g., "OC118 16SEP2022")',
    )
    ap.add_argument("--output", required=True, help="Output ASCII report path")
    ap.add_argument("--title", default="Untitled", help="Report title")
    ap.add_argument(
        "--dx",
        type=float,
        default=None,
        help="Analysis step size in feet (default from config.json)",
    )
    ap.add_argument(
        "--smoothing",
        type=float,
        default=0.0,
        help="Spline smoothing parameter (default: 0, i.e., no smoothing; matches BMAP). Use >0 to enable smoothing.",
    )
    ap.add_argument(
        "--ported-logic",
        action="store_true",
        help="Use ported cell boundary and integration logic from ProfileAnalysis_v129.py.",
    )
    ap.add_argument(
        "--hybrid-logic",
        action="store_true",
        help="Use BMAP-style cell boundaries but original above/below datum logic.",
    )
    ap.add_argument(
        "--hybrid-intersections-only",
        action="store_true",
        help="Hybrid logic: use only intersection points as cell boundaries (no datum crossings).",
    )
    ap.add_argument(
        "--hybrid-datum-only",
        action="store_true",
        help="Hybrid logic: use only datum crossings as cell boundaries (no intersection points).",
    )
    ap.add_argument(
        "--hybrid-reverse-sign",
        action="store_true",
        help="Hybrid logic: reverse the sign convention for above/below datum assignment.",
    )
    args = ap.parse_args()

    dx = args.dx if args.dx is not None else get_dx()

    profs1 = read_bmap_freeformat(args.input1)
    p1 = _select_profile(profs1, args.sel1)

    profs2 = read_bmap_freeformat(args.input2) if args.input2 else profs1
    p2 = _select_profile(profs2, args.sel2)

    # Patch: set a module-level flag for hybrid logic
    setattr(sys.modules[__name__], "use_hybrid_logic", args.hybrid_logic)
    setattr(
        sys.modules[__name__],
        "hybrid_intersections_only",
        args.hybrid_intersections_only,
    )
    setattr(sys.modules[__name__], "hybrid_datum_only", args.hybrid_datum_only)
    setattr(
        sys.modules[__name__], "hybrid_reverse_sign", args.hybrid_reverse_sign
    )
    compute_cut_fill_detailed(
        p1,
        p2,
        args.title,
        args.output,
        dx,
        args.smoothing,
        use_ported_logic=args.ported_logic,
    )
    logger = get_logger(LogComponent.CLI)
    logger.info(f"Wrote Cut/Fill detailed report to: {args.output}")


if __name__ == "__main__":
    main()

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
from typing import Optional, Tuple

import numpy as np

from profcalc.common.bmap_io import read_bmap_freeformat
from profcalc.common.config_utils import get_dx
from profcalc.common.error_handler import LogComponent, get_logger
from profcalc.common.io_reports import write_cutfill_detailed_report

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


def _ensure_sorted(x: np.ndarray, z: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    idx = np.argsort(x)
    return x[idx], z[idx]


def _overlap_bounds(x1: np.ndarray, x2: np.ndarray) -> Tuple[float, float]:
    x1min, x1max = float(np.min(x1)), float(np.max(x1))
    x2min, x2max = float(np.min(x2)), float(np.max(x2))
    x_on = max(x1min, x2min)
    x_off = min(x1max, x2max)
    if x_on >= x_off:
        raise ValueError("Profiles do not overlap in X; cannot compute Cut/Fill.")
    return x_on, x_off


def _shoreline_x(x: np.ndarray, z: np.ndarray) -> Optional[float]:
    """Seaward-most crossing with z=0. Returns None if no crossing."""
    x, z = _ensure_sorted(x, z)
    xr = None
    for i in range(1, len(x)):
        z1, z2 = z[i-1], z[i]
        if z1 == 0.0:
            xr = x[i-1]
        if (z1 * z2) < 0.0:
            frac = -z1 / (z2 - z1)
            xr = x[i-1] + frac * (x[i] - x[i-1])
        if z2 == 0.0:
            xr = x[i]
    return xr


# ---------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------

def compute_cut_fill_detailed(p1, p2, title: str, output_path: str, dx: float = 10.0):
    # Sort and restrict to overlapping X range
    x1, z1 = _ensure_sorted(p1.x, p1.z)
    x2, z2 = _ensure_sorted(p2.x, p2.z)
    x_on, x_off = _overlap_bounds(x1, x2)

    # Uniform analysis grid (dX spacing)
    xg = np.arange(x_on, x_off + dx, dx)
    z1g = np.interp(xg, x1, z1)
    z2g = np.interp(xg, x2, z2)

    # Δz and per-cell volume
    dz = z2g - z1g
    cell_vol_ft3_per_ft = 0.5 * (dz[:-1] + dz[1:]) * (xg[1:] - xg[:-1])
    cell_vol_cuyd_per_ft = cell_vol_ft3_per_ft / 27.0
    cell_thickness = 0.5 * (dz[:-1] + dz[1:])

    # Running totals
    cum_vol = np.cumsum(cell_vol_cuyd_per_ft)
    gross_vol = np.cumsum(np.abs(cell_vol_cuyd_per_ft))

    # Above and below datum volumes (z=0)
    h1_above = np.maximum(0.0, z1g)
    h2_above = np.maximum(0.0, z2g)
    diff_above = 0.5 * ((h2_above[:-1] - h1_above[:-1]) +
                        (h2_above[1:] - h1_above[1:])) * (xg[1:] - xg[:-1])
    above_cuyd_per_ft = float(np.sum(diff_above) / 27.0)

    h1_below = np.minimum(0.0, z1g)
    h2_below = np.minimum(0.0, z2g)
    diff_below = 0.5 * ((h2_below[:-1] - h1_below[:-1]) +
                        (h2_below[1:] - h1_below[1:])) * (xg[1:] - xg[:-1])
    below_cuyd_per_ft = float(np.sum(diff_below) / 27.0)

    total_cuyd_per_ft = float(np.sum(cell_vol_cuyd_per_ft))

    # Shoreline intersection (seaward-most crossing)
    xs1 = _shoreline_x(x1, z1)
    xs2 = _shoreline_x(x2, z2)
    if xs1 is not None and xs2 is not None:
        sh_change = float(xs2 - xs1)
        xs1_out, xs2_out = float(xs1), float(xs2)
    else:
        sh_change = float("nan")
        xs1_out, xs2_out = float("nan"), float("nan")

    # Build cell table
    cells = []
    for i in range(len(xg) - 1):
        cells.append({
            "end_x": float(xg[i + 1]),
            "end_z2": float(z2g[i + 1]),
            "cell_vol_cuyd_per_ft": float(cell_vol_cuyd_per_ft[i]),
            "cell_thickness_ft": float(cell_thickness[i]),
            "cum_vol_cuyd_per_ft": float(cum_vol[i]),
            "gross_vol_cuyd_per_ft": float(gross_vol[i]),
        })

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


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="BMAP-style Cut & Fill (detailed) for two selected profiles."
    )
    ap.add_argument("--input1", required=True, help="BMAP Free Format file containing Profile 1")
    ap.add_argument("--sel1", required=True, help='Selector for Profile 1 (e.g., "OC118 21SEP2021")')
    ap.add_argument("--input2", required=False, help="Optional second file containing Profile 2 (defaults to input1)")
    ap.add_argument("--sel2", required=True, help='Selector for Profile 2 (e.g., "OC118 16SEP2022")')
    ap.add_argument("--output", required=True, help="Output ASCII report path")
    ap.add_argument("--title", default="Untitled", help="Report title")
    ap.add_argument("--dx", type=float, default=None,
                    help="Analysis step size in feet (default from config.json)")
    args = ap.parse_args()

    dx = args.dx if args.dx is not None else get_dx()

    profs1 = read_bmap_freeformat(args.input1)
    p1 = _select_profile(profs1, args.sel1)

    profs2 = read_bmap_freeformat(args.input2) if args.input2 else profs1
    p2 = _select_profile(profs2, args.sel2)

    compute_cut_fill_detailed(p1, p2, args.title, args.output, dx)
    logger = get_logger(LogComponent.CLI)
    logger.info(f"Wrote Cut/Fill detailed report to: {args.output}")


if __name__ == "__main__":
    main()


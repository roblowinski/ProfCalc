# =============================================================================
# BMAP Volume Between Xon/Xoff Boundaries Tool
# =============================================================================
#
# FILE: src/profcalc/tools/bmap/bmap_vol_xon_xoff.py
#
# PURPOSE:
# This module replicates BMAP's "Volume from Xon to Xoff" tool, computing
# sediment volumes within specified cross-shore boundaries relative to a
# reference elevation. It provides precise volumetric calculations for defined
# profile segments, supporting detailed analysis of beach morphology and
# sediment distribution.
#
# WHAT IT'S FOR:
# - Calculating sediment volumes within specified cross-shore ranges
# - Computing volumes above reference elevations between Xon/Xoff boundaries
# - Supporting detailed volumetric analysis for beach segments
# - Providing BMAP-compatible volume reports with statistical summaries
# - Enabling precise volume calculations for management applications
#
# WORKFLOW POSITION:
# This tool is used in detailed volumetric analysis workflows when specific
# cross-shore ranges need to be analyzed separately. It's essential for
# targeted assessments of beach segments, nourishment projects, and
# morphological monitoring programs.
#
# LIMITATIONS:
# - Requires accurate Xon/Xoff boundary specification
# - Volume calculations depend on reference elevation choice
# - Flat extension beyond profile limits may not be physically accurate
# - Integration accuracy depends on grid spacing selection
#
# ASSUMPTIONS:
# - Xon/Xoff boundaries define meaningful analysis regions
# - Reference elevation is appropriate for volume calculations
# - Profile data covers or can be extended to boundary regions
# - Flat extension is acceptable for regions beyond profile extent
#
# =============================================================================

"""
volume_xon_xoff.py
------------------
Replicates the BMAP "Volume from Xon to Xoff" tool.

Computes volume (cu. yd/ft) bounded by:
- User-specified landward limit (Xon)
- User-specified seaward limit (Xoff)
- User-specified reference contour elevation (Zref)

Behavior:
- Uniform analysis grid using dX (from config.json or CLI override)
- Flat extension at Xon/Xoff if outside the profile range
- Volume integrated above Zref, clipped below
- Outputs BMAP-style ASCII report

Example:
        python tool_volume_xon_xoff.py \
            --input src/profcalc/data/input_examples/OCNJ_FreeFormat_Test.txt \
            --xon -25 --xoff 3000 --zref 0.0 \
            --output src/profcalc/data/output_examples/OCNJ_VolumeXonXoff.txt \
            --title "Untitled"
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

import numpy as np

from profcalc.common.bmap_io import read_bmap_freeformat
from profcalc.common.config_utils import get_dx
from profcalc.common.error_handler import LogComponent, get_logger
from profcalc.common.io_reports import write_volume_report


def _extend_or_interp(x: np.ndarray, z: np.ndarray, xq: float) -> float:
    """Interpolate within bounds or flat-extend beyond."""
    x, z = np.array(x), np.array(z)
    idx = np.argsort(x)
    x, z = x[idx], z[idx]
    if xq <= x[0]:
        return z[0]
    if xq >= x[-1]:
        return z[-1]
    return float(np.interp(xq, x, z))


def compute_volume_xon_xoff(
    profile: Any,
    xon: float,
    xoff: float,
    zref: float,
    dx: float = 10.0,
    outofbounds_policy: str = "extend",
) -> Dict[str, float | None] | None:
    """Compute volume between user-specified Xon/Xoff and above Zref.
    outofbounds_policy: 'extend' (flat), 'clip' (adjust), 'skip' (remove)"""
    x, z = np.array(profile.x), np.array(profile.z)
    idx = np.argsort(x)
    x, z = x[idx], z[idx]

    # Policy 3: skip profile if Xon/Xoff are out of bounds
    if outofbounds_policy == "skip":
        if xon < x[0] or xoff > x[-1]:
            return None

    # Policy 2: clip Xon/Xoff to bounds
    if outofbounds_policy == "clip":
        xon = max(xon, x[0])
        xoff = min(xoff, x[-1])
        if xon >= xoff:
            return {
                "x_on": float(xon),
                "x_off": float(xoff),
                "volume_cuyd_per_ft": 0.0,
                "contour_x": None,
            }

    # Policy 1: extend (default, flat extension)
    def interp_or_flat(x: np.ndarray, z: np.ndarray, xq: float) -> float:
        if xq <= x[0]:
            return z[0]
        if xq >= x[-1]:
            return z[-1]
        return float(np.interp(xq, x, z))

    x_list, z_list = list(x), list(z)
    if outofbounds_policy == "extend":
        if xon < x[0]:
            x_list = [xon] + x_list
            z_list = [z[0]] + z_list
        elif xon > x[0]:
            x_list = [xon] + x_list
            z_list = [interp_or_flat(x, z, xon)] + z_list
        if xoff > x[-1]:
            x_list = x_list + [xoff]
            z_list = z_list + [z[-1]]
        elif xoff < x[-1]:
            x_list = x_list + [xoff]
            z_list = z_list + [interp_or_flat(x, z, xoff)]
        x = np.array(x_list)
        z = np.array(z_list)
    elif outofbounds_policy == "clip":
        # Just restrict to [xon, xoff] (already clipped above)
        x_list, z_list = [xon], [interp_or_flat(x, z, xon)]
        for xi, zi in zip(x, z):
            if xon < xi < xoff:
                x_list.append(xi)
                z_list.append(zi)
        x_list.append(xoff)
        z_list.append(interp_or_flat(x, z, xoff))
        x = np.array(x_list)
        z = np.array(z_list)
    # For 'skip', we already returned None above
    # Restrict to [XOn, XOff]
    mask = (x >= xon) & (x <= xoff)
    x = x[mask]
    z = z[mask]
    if len(x) < 2:
        return {
            "x_on": float(xon),
            "x_off": float(xoff),
            "volume_cuyd_per_ft": 0.0,
            "contour_x": None,
        }
    # Remove exact consecutive duplicate x
    xz = [(x[0], z[0])]
    for i in range(1, len(x)):
        if x[i] == x[i - 1]:
            continue
        xz.append((x[i], z[i]))
    x, z = np.array([p[0] for p in xz]), np.array([p[1] for p in xz])
    # Integrate area above Zref
    area = 0.0
    nseg = len(x) - 1
    # For 'extend' policy, if Xoff > last profile x, exclude the last segment (BMAP behavior)
    if outofbounds_policy == "extend" and len(x) >= 2:
        # Find the last profile x (before extension)
        last_profile_x = np.max(np.array(profile.x))
        # If the last x in the working array is Xoff and the previous is last_profile_x, exclude this segment
        if np.isclose(x[-1], xoff) and np.isclose(x[-2], last_profile_x):
            nseg -= 1
    for i in range(nseg):
        x0, x1 = x[i], x[i + 1]
        z0, z1 = z[i], z[i + 1]
        h0 = z0 - zref
        h1 = z1 - zref
        h0_clip = max(h0, 0)
        h1_clip = max(h1, 0)
        seg_area = 0.5 * (h0_clip + h1_clip) * (x1 - x0)
        area += float(seg_area)
    area_cuyd_per_ft = area / 27.0
    # Find first crossing of Zref (optional, for reporting)
    x_cross = None
    for i in range(1, len(x)):
        if (z[i - 1] - zref) * (z[i] - zref) < 0:
            frac = (zref - z[i - 1]) / (z[i] - z[i - 1])
            x_cross = x[i - 1] + frac * (x[i] - x[i - 1])
            break
    return {
        "x_on": float(xon),
        "x_off": float(xoff),
        "volume_cuyd_per_ft": float(area_cuyd_per_ft),
        "contour_x": float(x_cross) if x_cross is not None else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="BMAP-style Volume from Xon–Xoff")
    ap.add_argument("--input", required=True, help="BMAP Free Format file")
    ap.add_argument("--xon", type=float, required=True, help="Landward limit (ft)")
    ap.add_argument("--xoff", type=float, required=True, help="Seaward limit (ft)")
    ap.add_argument(
        "--zref",
        type=float,
        required=True,
        help="Reference contour elevation (ft)",
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
        "--outofbounds-policy",
        choices=["extend", "clip", "skip"],
        default="extend",
        help="How to handle Xon/Xoff outside profile bounds: 'extend' (flat extension), 'clip' (adjust to bounds), 'skip' (remove profile). Default: extend.",
    )
    args = ap.parse_args()

    if args.xon >= args.xoff:
        raise SystemExit("Error: Xon must be less than Xoff.")

    dx = args.dx if args.dx is not None else get_dx()

    profiles = read_bmap_freeformat(args.input)
    results = []

    for p in profiles:
        res = compute_volume_xon_xoff(
            p, args.xon, args.xoff, args.zref, dx, args.outofbounds_policy
        )
        if res is None:
            continue  # skip profile if policy is 'skip' and out of bounds
        results.append(
            {
                "label": f"{p.name} {p.date or ''} {p.description or ''}".strip(),
                "x_on": res["x_on"],
                "x_off": res["x_off"],
                "volume_cuyd_per_ft": res["volume_cuyd_per_ft"],
                "contour_x": res["contour_x"],
            }
        )

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    write_volume_report(args.output, results, args.zref, args.title)
    logger = get_logger(LogComponent.CLI)
    logger.info(f"Volume from Xon–Xoff report written to: {args.output}")


if __name__ == "__main__":
    main()

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
      --input ../../data/input_examples/OCNJ_FreeFormat_Test.txt \
      --xon -25 --xoff 3000 --zref 0.0 \
      --output ../../data/output_examples/OCNJ_VolumeXonXoff.txt \
      --title "Untitled"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from profile_analysis.common.config_utils import get_dx
from profile_analysis.common.io_freeformat import read_bmap_freeformat
from profile_analysis.common.io_reports import write_volume_report


def _extend_or_interp(x, z, xq):
    """Interpolate within bounds or flat-extend beyond."""
    x, z = np.array(x), np.array(z)
    idx = np.argsort(x)
    x, z = x[idx], z[idx]
    if xq <= x[0]:
        return z[0]
    if xq >= x[-1]:
        return z[-1]
    return float(np.interp(xq, x, z))


def compute_volume_xon_xoff(profile, xon, xoff, zref, dx: float = 10.0):
    """Compute volume between user-specified Xon/Xoff and above Zref."""
    x, z = np.array(profile.x), np.array(profile.z)
    idx = np.argsort(x)
    x, z = x[idx], z[idx]

    # Extend endpoints if necessary
    z_xon = _extend_or_interp(x, z, xon)
    z_xoff = _extend_or_interp(x, z, xoff)

    # Define uniform grid between bounds
    xg = np.arange(xon, xoff + dx, dx)
    zg = np.interp(xg, x, z)
    zg[0], zg[-1] = z_xon, z_xoff

    # Clip below contour elevation
    h = np.maximum(0.0, zg - zref)
    area_ft3_per_ft = np.trapz(h, xg)
    area_cuyd_per_ft = float(area_ft3_per_ft) / 27.0

    # Contour crossing location
    x_cross = np.nan
    for i in range(1, len(xg)):
        if (zg[i-1] - zref) * (zg[i] - zref) <= 0:
            frac = (zref - zg[i-1]) / (zg[i] - zg[i-1] + 1e-12)
            x_cross = xg[i-1] + frac * (xg[i] - xg[i-1])

    return {
        "x_on": float(xon),
        "x_off": float(xoff),
        "volume_cuyd_per_ft": float(area_cuyd_per_ft),
        "contour_x": float(x_cross) if x_cross == x_cross else None,
    }


def main():
    ap = argparse.ArgumentParser(description="BMAP-style Volume from Xon–Xoff")
    ap.add_argument("--input", required=True, help="BMAP Free Format file")
    ap.add_argument("--xon", type=float, required=True, help="Landward limit (ft)")
    ap.add_argument("--xoff", type=float, required=True, help="Seaward limit (ft)")
    ap.add_argument("--zref", type=float, required=True, help="Reference contour elevation (ft)")
    ap.add_argument("--output", required=True, help="Output ASCII report path")
    ap.add_argument("--title", default="Untitled", help="Report title")
    ap.add_argument("--dx", type=float, default=None,
                    help="Analysis step size in feet (default from config.json)")
    args = ap.parse_args()

    if args.xon >= args.xoff:
        raise SystemExit("Error: Xon must be less than Xoff.")

    dx = args.dx if args.dx is not None else get_dx()

    profiles = read_bmap_freeformat(args.input)
    results = []

    for p in profiles:
        res = compute_volume_xon_xoff(p, args.xon, args.xoff, args.zref, dx)
        results.append({
            "label": f"{p.name} {p.date or ''} {p.description or ''}".strip(),
            "x_on": res["x_on"],
            "x_off": res["x_off"],
            "volume_cuyd_per_ft": res["volume_cuyd_per_ft"],
            "contour_x": res["contour_x"],
        })

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    write_volume_report(args.output, results, args.zref, args.title)
    print(f"Volume from Xon–Xoff report written to: {args.output}")


if __name__ == "__main__":
    main()

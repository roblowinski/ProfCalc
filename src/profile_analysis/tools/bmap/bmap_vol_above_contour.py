"""
volume_above_contour.py
-----------------------
Replicates the BMAP "Volume Above Contour" tool.

Computes the area (volume per foot) between a user-specified contour elevation
and the upper portion of each profile.  Results are written to a BMAP-style
ASCII report.

Inputs:
- One BMAP Free Format file containing one or more profiles.
- A user-specified contour elevation (ft, NAVD88 or other datum).

Behavior:
- Uses global dX (from config.json) for uniform spacing.
- Integrates elevation above contour only (z > contour).
- Outputs cu. yd/ft.

Example:
    python tool_volume_above_contour.py \
      --input ../../data/input_examples/OCNJ_FreeFormat_Test.txt \
      --contour 0.0 \
      --output ../../data/output_examples/OCNJ_VolumeAboveContour.txt \
      --title "Untitled"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from profile_analysis.common.config_utils import get_dx
from profile_analysis.common.io_freeformat import read_bmap_freeformat
from profile_analysis.common.io_reports import write_volume_report


def compute_volume_above_contour(profile, contour: float, dx: float = 10.0):
    """Compute volume above a contour elevation for one profile."""
    x, z = np.array(profile.x), np.array(profile.z)
    idx = np.argsort(x)
    x, z = x[idx], z[idx]

    x_min, x_max = float(np.min(x)), float(np.max(x))
    xg = np.arange(x_min, x_max + dx, dx)
    zg = np.interp(xg, x, z)

    # Elevations above contour only
    h = np.maximum(0.0, zg - contour)
    area_ft3_per_ft = np.trapz(h, xg)
    area_cuyd_per_ft = float(area_ft3_per_ft) / 27.0

    # Find contour crossing (seaward-most)
    x_cross = np.nan
    for i in range(1, len(xg)):
        if (zg[i-1] - contour) * (zg[i] - contour) <= 0:
            frac = (contour - zg[i-1]) / (zg[i] - zg[i-1] + 1e-12)
            x_cross = xg[i-1] + frac * (xg[i] - xg[i-1])
    return {
        "x_on": float(xg[0]),
        "x_off": float(xg[-1]),
        "volume_cuyd_per_ft": float(area_cuyd_per_ft),
        "contour_x": float(x_cross) if x_cross == x_cross else None,
    }


def main():
    ap = argparse.ArgumentParser(description="BMAP-style Volume Above Contour")
    ap.add_argument("--input", required=True, help="BMAP Free Format file")
    ap.add_argument("--contour", type=float, required=True,
                    help="Contour elevation (ft)")
    ap.add_argument("--output", required=True, help="Output ASCII report path")
    ap.add_argument("--title", default="Untitled", help="Report title")
    ap.add_argument("--dx", type=float, default=None,
                    help="Analysis step size in feet (default from config.json)")
    args = ap.parse_args()

    dx = args.dx if args.dx is not None else get_dx()

    profiles = read_bmap_freeformat(args.input)
    results = []

    for p in profiles:
        res = compute_volume_above_contour(p, args.contour, dx)
        results.append({
            "label": f"{p.name} {p.date or ''} {p.description or ''}".strip(),
            "x_on": res["x_on"],
            "x_off": res["x_off"],
            "volume_cuyd_per_ft": res["volume_cuyd_per_ft"],
            "contour_x": res["contour_x"],
        })

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    write_volume_report(args.output, results, args.contour, args.title)
    print(f"Volume Above Contour report written to: {args.output}")


if __name__ == "__main__":
    main()

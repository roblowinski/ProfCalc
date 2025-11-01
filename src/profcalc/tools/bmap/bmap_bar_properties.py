"""
bar_properties.py
-----------------
BMAP-style "Bar Properties" tool with directional crossing pairs.

Behavior (matches BMAP):
- User selects a Reference profile and a Specific profile (must be different,
  unless Reference is 'None' to use manual XStart/XEnd).
- We resample both profiles to a uniform grid (dX).
- Find all landward->seaward zero-crossings of (Z_ref - Z_spec).
- Pair crossings as (1&2), (3&4), ... and let user pick a pair index.
- The selected pair defines Bar XStart and XEnd.
- Compute *on the Specific profile only* within [XStart, XEnd]:
    * Minimum Depth (report absolute magnitude) and its X location
    * Maximum Height (crest minus trough) and crest X location
    * Bar Volume (above horizontal trough baseline) in cu. yd/ft
    * Bar Length (XEnd - XStart)
    * Center of Mass X (centroid of bar volume above trough baseline)
- Preserve directional behavior: crossings come from sign changes of (Z_ref - Z_spec).

CLI examples:
(1) List crossing pairs only:
    python tool_bar_properties.py --input1 input.txt --sel1 "OC117 27SEP2021 (AME)" \
                             --input2 input.txt --sel2 "OC117 16SEP2022 (AME)" \
                             --list_pairs

(2) Generate report choosing pair #1:
    python tool_bar_properties.py --input1 input.txt --sel1 "OC117 27SEP2021 (AME)" \
                             --input2 input.txt --sel2 "OC117 16SEP2022 (AME)" \
                             --pair 1 --output bar_report.txt --title "Untitled"

(3) Manual window (Reference=None mode):
    python tool_bar_properties.py --input2 input.txt --sel2 "OC117 16SEP2022 (AME)" \
                             --xstart 1279.19 --xend 4287.67 \
                             --output bar_report.txt --title "Untitled"
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from profcalc.common.bmap_io import read_bmap_freeformat
from profcalc.common.config_utils import get_dx
from profcalc.common.error_handler import LogComponent, get_logger
from profcalc.common.io_reports import write_bar_properties_report

# ----------------------------
# Small helpers
# ----------------------------


def _label(p) -> str:
    parts = [p.name]
    if p.date:
        parts.append(p.date)
    if p.description:
        parts.append(p.description)
    return " ".join(parts).strip()


def _ensure_sorted(
    x: np.ndarray, z: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    idx = np.argsort(x)
    return x[idx], z[idx]


def _interp1d_flat_extend(
    x: np.ndarray, z: np.ndarray, xg: np.ndarray
) -> np.ndarray:
    """
    Linear interpolation with flat extension beyond native bounds.
    """
    x, z = _ensure_sorted(np.asarray(x), np.asarray(z))
    zg = np.interp(xg, x, z)
    if xg[0] < x[0]:
        zg[xg <= x[0]] = z[0]
    if xg[-1] > x[-1]:
        zg[xg >= x[-1]] = z[-1]
    return zg


def _build_common_grid(p1, p2, dx: float) -> np.ndarray:
    """
    Common uniform grid covering the combined span of both profiles.
    """
    xmin = min(np.min(p1.x), np.min(p2.x))
    xmax = max(np.max(p1.x), np.max(p2.x))
    # ensure at least two points
    if xmax <= xmin:
        xmax = xmin + dx
    return np.arange(xmin, xmax + dx, dx)


def _zero_crossings(
    xg: np.ndarray, yr: np.ndarray, ys: np.ndarray
) -> List[float]:
    """
    Find zero crossings of (yr - ys) along xg using linear interpolation.
    Returns a sorted list of crossing X locations (landward->seaward).
    """
    d = yr - ys
    xs: List[float] = []
    for i in range(len(xg) - 1):
        y1 = d[i]
        y2 = d[i + 1]
        if y1 == 0.0:
            # exact grid hit: record, but continue to next segment
            xs.append(float(xg[i]))
        # sign change across the segment
        if (y1 > 0 and y2 < 0) or (y1 < 0 and y2 > 0):
            # linear interpolation for zero
            t = y1 / (y1 - y2)  # fraction from x[i] to x[i+1]
            xz = xg[i] + t * (xg[i + 1] - xg[i])
            xs.append(float(xz))
        # handle exact zero at end point (avoid duplicates)
        if y2 == 0.0:
            xs.append(float(xg[i + 1]))
    # sort + dedupe near-equals
    xs = sorted(xs)
    dedup: list[float] = []
    eps = 1e-6
    for val in xs:
        if not dedup or abs(val - dedup[-1]) > eps:
            dedup.append(val)
    return dedup


def _pair_crossings(xs: List[float]) -> List[Tuple[float, float]]:
    """
    Pair consecutive crossings: (x1,x2), (x3,x4), ...
    Ignore a trailing unpaired crossing if count is odd.
    """
    pairs = []
    for i in range(0, len(xs) - 1, 2):
        pairs.append((xs[i], xs[i + 1]))
    return pairs


# ----------------------------
# Bar properties on Specific profile
# ----------------------------


@dataclass
class BarProps:
    xstart_ft: float
    xend_ft: float
    length_ft: float
    min_depth_ft: float  # positive magnitude (abs trough Z)
    min_depth_x_ft: float
    max_height_ft: float  # crestZ - troughZ
    max_height_x_ft: float  # crest X
    volume_cuyd_per_ft: float
    centroid_x_ft: float  # NaN if volume ~ 0


def _interp_clip(
    x: np.ndarray, z: np.ndarray, x1: float, x2: float, dx: float
):
    x, z = _ensure_sorted(x, z)
    if x2 <= x1:
        raise ValueError("xend must be greater than xstart")
    xg = np.arange(x1, x2 + dx, dx)
    zg = _interp1d_flat_extend(x, z, xg)
    return xg, zg


def compute_bar_properties_specific(
    profile, xstart: float, xend: float, dx: float
) -> BarProps:
    """
    Compute bar properties within [xstart, xend] using SPECIFIC profile elevations.
    Baseline is horizontal at the trough elevation in that window.
    """
    xg, zg = _interp_clip(
        np.asarray(profile.x), np.asarray(profile.z), xstart, xend, dx
    )

    # Trough (minimum Z) and Crest (maximum Z) in the window
    i_tr = int(np.argmin(zg))
    i_cr = int(np.argmax(zg))
    z_tr = float(zg[i_tr])
    x_tr = float(xg[i_tr])
    z_cr = float(zg[i_cr])
    x_cr = float(xg[i_cr])

    # Height field above trough baseline
    h = zg - z_tr
    h[h < 0.0] = 0.0

    # Volume (ft^3/ft), then convert to cu yd/ft
    area_ft3_per_ft = float(np.trapz(h, xg))
    vol_cuyd_per_ft = area_ft3_per_ft / 27.0

    # Center of mass X
    if area_ft3_per_ft > 0:
        moment = float(np.trapz(xg * h, xg))
        x_cm = moment / area_ft3_per_ft
    else:
        x_cm = float("nan")

    return BarProps(
        xstart_ft=float(xstart),
        xend_ft=float(xend),
        length_ft=float(xend - xstart),
        min_depth_ft=abs(z_tr),  # report positive magnitude like BMAP
        min_depth_x_ft=x_tr,
        max_height_ft=float(z_cr - z_tr),
        max_height_x_ft=x_cr,
        volume_cuyd_per_ft=vol_cuyd_per_ft,
        centroid_x_ft=x_cm,
    )


# ----------------------------
# CLI
# ----------------------------


def main():
    ap = argparse.ArgumentParser(
        description="BMAP-style Bar Properties (with crossing pairs)."
    )
    ap.add_argument(
        "--input1",
        help="File containing REFERENCE profile (BMAP Free Format). Use 'none' to skip.",
    )
    ap.add_argument(
        "--sel1",
        help='Selector for Reference profile (e.g., "OC117 27SEP2021 (AME)"). Use "none" to skip.',
    )
    ap.add_argument(
        "--input2",
        required=True,
        help="File containing SPECIFIC profile (BMAP Free Format)",
    )
    ap.add_argument(
        "--sel2",
        required=True,
        help='Selector for Specific profile (e.g., "OC117 16SEP2022 (AME)")',
    )
    ap.add_argument(
        "--pair",
        type=int,
        help="Select crossing pair index (1-based). Requires Reference mode.",
    )
    ap.add_argument(
        "--list_pairs",
        action="store_true",
        help="List crossing pairs and exit (Reference mode).",
    )
    ap.add_argument(
        "--xstart",
        type=float,
        help="Manual Bar XStart (ft) (Reference=None mode)",
    )
    ap.add_argument(
        "--xend", type=float, help="Manual Bar XEnd (ft) (Reference=None mode)"
    )
    ap.add_argument("--output", help="ASCII report path to write")
    ap.add_argument("--title", default="Untitled", help="Report title")
    ap.add_argument(
        "--dx",
        type=float,
        default=None,
        help="Analysis spacing in feet (default from config.json)",
    )
    args = ap.parse_args()

    dx = args.dx if args.dx is not None else get_dx()

    # Load Specific profile (always required)
    profs2 = read_bmap_freeformat(args.input2)
    p_spec = None
    key2 = (args.sel2 or "").strip().lower()
    for p in profs2:
        lab = _label(p).lower()
        if lab == key2 or lab.startswith(key2):
            p_spec = p
            break
    if p_spec is None:
        raise SystemExit(f"No Specific profile matched: {args.sel2}")

    # Reference mode?
    ref_mode = (
        args.sel1
        and args.sel1.strip().lower() != "none"
        and args.input1
        and args.input1.strip().lower() != "none"
    )

    if ref_mode:
        # Load Reference profile; must be different from Specific
        profs1 = read_bmap_freeformat(args.input1)
        p_ref = None
        key1 = args.sel1.strip().lower()
        for p in profs1:
            lab = _label(p).lower()
            if lab == key1 or lab.startswith(key1):
                p_ref = p
                break
        if p_ref is None:
            raise SystemExit(f"No Reference profile matched: {args.sel1}")

        if _label(p_ref) == _label(p_spec):
            raise SystemExit(
                "Reference and Specific profiles must be different (or set Reference to 'none')."
            )

        # Build common grid and compute directional crossings of (Z_ref - Z_spec)
        xg = _build_common_grid(p_ref, p_spec, dx)
        zr = _interp1d_flat_extend(p_ref.x, p_ref.z, xg)
        zs = _interp1d_flat_extend(p_spec.x, p_spec.z, xg)
        xs = _zero_crossings(xg, zr, zs)  # landward->seaward
        pairs = _pair_crossings(xs)

        if args.list_pairs or not args.pair:
            # Print list and exit (or prompt user to re-run with --pair)
            logger = get_logger(LogComponent.CLI)
            if not pairs:
                logger.info("No crossing pairs found.")
            else:
                logger.info("Crossing pairs (landward -> seaward):")
                for i, (a, b) in enumerate(pairs, start=1):
                    logger.info(f"  ({i}) {a:.2f} – {b:.2f} ft")
            if args.list_pairs or not args.output or not args.pair:
                # Listing mode or missing selection => stop here
                return

        # Pair selection (1-based)
        idx = args.pair
        if idx is None or idx < 1 or idx > len(pairs):
            raise SystemExit(
                f"--pair must be between 1 and {len(pairs)} (found {len(pairs)} pairs)."
            )
        xstart, xend = pairs[idx - 1]

    else:
        # Manual window mode (Reference=None)
        if args.xstart is None or args.xend is None:
            raise SystemExit(
                "Reference=None mode requires --xstart and --xend."
            )
        xstart, xend = float(args.xstart), float(args.xend)

    # Compute properties on Specific within [xstart, xend]
    props = compute_bar_properties_specific(p_spec, xstart, xend, dx)

    # Write report if requested
    if args.output:
        write_bar_properties_report(
            output_path=args.output,
            title=args.title,
            reference_label=(_label(p_ref) if ref_mode else "None"),
            specific_label=_label(p_spec),
            xstart=float(props.xstart_ft),
            xend=float(props.xend_ft),
            min_depth_ft=float(props.min_depth_ft),
            min_depth_x_ft=float(props.min_depth_x_ft),
            max_height_ft=float(props.max_height_ft),
            max_height_x_ft=float(props.max_height_x_ft),
            bar_volume_cuyd_per_ft=float(props.volume_cuyd_per_ft),
            bar_length_ft=float(props.length_ft),
            center_of_mass_x_ft=float(props.centroid_x_ft),
        )
        logger = get_logger(LogComponent.CLI)
        logger.info(f"Bar Properties report written to: {args.output}")
    else:
        # If no output, print a compact summary to stdout
        print("Bar Properties Report (summary)")
        print(f"Reference Profile:\t{_label(p_ref) if ref_mode else 'None'}")
        print(f"Specific Profile:\t{_label(p_spec)}")
        print(f"Bar XStart:\t{props.xstart_ft:.2f} ft")
        print(f"Bar XEnd:\t{props.xend_ft:.2f} ft")
        print(f"Minimum Depth:\t{props.min_depth_ft:.2f} ft")
        print(f"   Location:\t{props.min_depth_x_ft:.2f} ft")
        print(f"Maximum Height:\t{props.max_height_ft:.2f} ft")
        print(f"   Location:\t{props.max_height_x_ft:.2f} ft")
        print(f"Bar Volume:\t{props.volume_cuyd_per_ft:.3f} cu. yd/ft")
        print(f"Bar Length:\t{props.length_ft:.2f} ft")
        print(f"Center of Mass:\t{props.centroid_x_ft:.2f} ft")


if __name__ == "__main__":
    main()

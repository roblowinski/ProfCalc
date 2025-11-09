"""Bounds Finder

Find common X/Y coordinate ranges across profile surveys. Reads BMAP,
CSV or XYZ input, computes per-survey and per-profile bounds, and writes
CSV and pretty-text outputs. Optionally creates a shapefile of Xon/Xoff
positions when baseline (origin azimuth) data are available.

Usage examples:
    - CLI: run the conversion/CLI entry that calls :func:`execute_from_cli` or
        use the interactive menu entry::

            python -m profcalc.cli.tools.bounds "*.dat"

    - Menu: Quick Tools → Find Common Bounds (invokes :func:`execute_from_menu`).
"""

import glob
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.common.bmap_io import format_date_for_bmap, read_bmap_freeformat
from profcalc.common.csv_io import CSVParser, read_xyz_profiles
from profcalc.core.profile_stats import calculate_common_ranges

try:
    from tabulate import tabulate  # type: ignore

    _HAS_TABULATE = True
except ImportError:  # pragma: no cover - optional dependency
    tabulate = None  # type: ignore
    _HAS_TABULATE = False


def _profiles_to_dict_for_axis(
    profiles: Iterable[Any], coord_attr: str = "x"
) -> Dict[str, List[List[Tuple[float, float]]]]:
    """Convert profiles to a dict keyed by profile name using coord_attr.

    Each value is a list of surveys, each survey is a list of (coord, z)
    tuples where coord is either X or Y depending on coord_attr.
    """
    result = defaultdict(list)
    for profile in profiles:
        coords = getattr(profile, coord_attr, None)
        if coords is None:
            coords = profile.x
        points = [(float(c), float(z)) for c, z in zip(coords, profile.z)]
        result[profile.name].append(points)
    return dict(result)


def _format_survey_csv_combined(
    combined_rows: List[
        Tuple[str, str, float | None, float | None, float | None, float | None]
    ],
) -> str:
    lines: List[str] = [
        "profile,date,xon_ft,xoff_ft,xrange_ft,ymin_ft,ymax_ft,yrange_ft"
    ]
    for profile_name, date_str, xmin, xmax, ymin, ymax in combined_rows:
        xrange_ft = ""
        yrange_ft = ""
        xmin_s = ""
        xmax_s = ""
        ymin_s = ""
        ymax_s = ""
        if xmin is not None and xmax is not None:
            xmin_s = f"{xmin:.2f}"
            xmax_s = f"{xmax:.2f}"
            xrange_ft = f"{(xmax - xmin):.2f}"
        if ymin is not None and ymax is not None:
            ymin_s = f"{ymin:.2f}"
            ymax_s = f"{ymax:.2f}"
            yrange_ft = f"{(ymax - ymin):.2f}"

        lines.append(
            f"{profile_name},{date_str or ''},{xmin_s},{xmax_s},{xrange_ft},{ymin_s},{ymax_s},{yrange_ft}"
        )

    return "\n".join(lines)


def _format_summary_csv_combined(
    summary_rows: List[
        Tuple[
            str,
            float | None,
            float | None,
            int | None,
            float | None,
            float | None,
            int | None,
        ]
    ],
) -> str:
    lines: List[str] = [
        "profile,xon_ft,xoff_ft,x_surveys,xrange_ft,ymin_ft,ymax_ft,y_surveys,yrange_ft"
    ]
    for (
        profile_name,
        xmin,
        xmax,
        x_surveys,
        ymin,
        ymax,
        y_surveys,
    ) in summary_rows:
        xmin_s = f"{xmin:.2f}" if xmin is not None else ""
        xmax_s = f"{xmax:.2f}" if xmax is not None else ""
        x_range = (
            f"{(xmax - xmin):.2f}"
            if xmin is not None and xmax is not None
            else ""
        )
        ymin_s = f"{ymin:.2f}" if ymin is not None else ""
        ymax_s = f"{ymax:.2f}" if ymax is not None else ""
        y_range = (
            f"{(ymax - ymin):.2f}"
            if ymin is not None and ymax is not None
            else ""
        )
        x_surveys_s = f"{x_surveys}" if x_surveys is not None else ""
        y_surveys_s = f"{y_surveys}" if y_surveys is not None else ""
        lines.append(
            f"{profile_name},{xmin_s},{xmax_s},{x_surveys_s},{x_range},{ymin_s},{ymax_s},{y_surveys_s},{y_range}"
        )

    return "\n".join(lines)


def _format_survey_table_combined(
    combined_rows: List[
        Tuple[str, str, float | None, float | None, float | None, float | None]
    ],
) -> str:
    headers = [
        "Profile",
        "Date",
        "Xon (ft)",
        "Xoff (ft)",
        "X-Range (ft)",
        "Ymin (ft)",
        "Ymax (ft)",
        "Y-Range (ft)",
    ]

    rows: List[List[str]] = []
    for profile_name, date_str, xmin, xmax, ymin, ymax in combined_rows:
        xmin_s = f"{xmin:.2f}" if xmin is not None else ""
        xmax_s = f"{xmax:.2f}" if xmax is not None else ""
        x_range = (
            f"{(xmax - xmin):.2f}"
            if xmin is not None and xmax is not None
            else ""
        )
        ymin_s = f"{ymin:.2f}" if ymin is not None else ""
        ymax_s = f"{ymax:.2f}" if ymax is not None else ""
        y_range = (
            f"{(ymax - ymin):.2f}"
            if ymin is not None and ymax is not None
            else ""
        )
        rows.append(
            [
                profile_name,
                date_str or "",
                xmin_s,
                xmax_s,
                x_range,
                ymin_s,
                ymax_s,
                y_range,
            ]
        )

    if _HAS_TABULATE:
        return tabulate(rows, headers=headers, tablefmt="github")

    # Fallback ASCII
    lines: List[str] = ["=" * 100]
    lines.append("PER-SURVEY LIST (X and Y)")
    lines.append("=" * 100)
    lines.append("")
    lines.append(
        f"{'Profile':<20} | {'Date':<12} | {'Xon (ft)':>10} | {'Xoff (ft)':>10} | {'X-Range (ft)':>12} | {'Ymin (ft)':>10} | {'Ymax (ft)':>10} | {'Y-Range (ft)':>12}"
    )
    lines.append("-" * 100)

    for row in rows:
        lines.append(
            f"{row[0]:<20} | {row[1]:<12} | {row[2]:>10} | {row[3]:>10} | {row[4]:>12} | {row[5]:>10} | {row[6]:>10} | {row[7]:>12}"
        )

    lines.append("-" * 100)
    return "\n".join(lines)


def _format_summary_table_combined(
    summary_rows: List[
        Tuple[
            str,
            float | None,
            float | None,
            int | None,
            float | None,
            float | None,
            int | None,
        ]
    ],
) -> str:
    headers = [
        "Profile",
        "Xon (ft)",
        "Xoff (ft)",
        "X-Range (ft)",
        "X-Surveys",
        "Ymin (ft)",
        "Ymax (ft)",
        "Y-Range (ft)",
        "Y-Surveys",
    ]

    rows: List[List[str]] = []
    for pname, xmin, xmax, x_surveys, ymin, ymax, y_surveys in summary_rows:
        xmin_s = f"{xmin:.2f}" if xmin is not None else ""
        xmax_s = f"{xmax:.2f}" if xmax is not None else ""
        x_range = (
            f"{(xmax - xmin):.2f}"
            if xmin is not None and xmax is not None
            else ""
        )
        x_surveys_s = f"{x_surveys}" if x_surveys is not None else ""
        ymin_s = f"{ymin:.2f}" if ymin is not None else ""
        ymax_s = f"{ymax:.2f}" if ymax is not None else ""
        y_range = (
            f"{(ymax - ymin):.2f}"
            if ymin is not None and ymax is not None
            else ""
        )
        y_surveys_s = f"{y_surveys}" if y_surveys is not None else ""
        rows.append(
            [
                pname,
                xmin_s,
                xmax_s,
                x_range,
                x_surveys_s,
                ymin_s,
                ymax_s,
                y_range,
                y_surveys_s,
            ]
        )

    if _HAS_TABULATE:
        return tabulate(rows, headers=headers, tablefmt="github")

    lines: List[str] = ["=" * 120]
    lines.append("PER-PROFILE SUMMARY (X and Y)")
    lines.append("=" * 120)
    lines.append("")
    lines.append(
        f"{'Profile':<20} | {'Xon (ft)':>10} | {'Xoff (ft)':>10} | {'X-Range (ft)':>12} | {'X-Surveys':>9} | {'Ymin (ft)':>10} | {'Ymax (ft)':>10} | {'Y-Range (ft)':>12} | {'Y-Surveys':>9}"
    )
    lines.append("-" * 120)

    for r in rows:
        lines.append(
            f"{r[0]:<20} | {r[1]:>10} | {r[2]:>10} | {r[3]:>12} | {r[4]:>9} | {r[5]:>10} | {r[6]:>10} | {r[7]:>12} | {r[8]:>9}"
        )

    lines.append("-" * 120)
    return "\n".join(lines)


def execute_from_menu() -> None:
    """Interactive, menu-driven entry point for the quick bounds tool.

    Reads BMAP files matching a user-supplied pattern, calculates common X/Y
    bounds, writes CSV and pretty text outputs, and optionally creates a
    shapefile of Xon/Xoff points with X/Y attributes when an origin azimuth
    file is provided or supplied by the user.
    """
    print("\n" + "=" * 60)
    print("FIND COMMON BOUNDS")
    print("=" * 60)

    file_pattern = input("Enter BMAP file pattern (e.g., *.dat): ").strip()
    # always write both CSV and text

    mhw_input = input(
        "Enter MHW elevation (ft NAVD88) [optional, press Enter to skip]: "
    ).strip()
    mhw_elev = float(mhw_input) if mhw_input else None

    dir_input = (
        input("Direction to analyze (x/y/both) [x]: ").strip().lower() or "x"
    )
    if dir_input not in ("x", "y", "both"):
        print("Invalid direction selection. Defaulting to 'x'.")
        dir_input = "x"

    matched_files = glob.glob(file_pattern)
    if not matched_files:
        matched_files = [file_pattern]

    all_profiles_x: dict[str, list] = {}
    all_profiles_y: dict[str, list] = {}
    all_surveys_x: List[Tuple[str, str, datetime | None, float, float]] = []
    all_surveys_y: List[Tuple[str, str, datetime | None, float, float]] = []

    for fp in matched_files:
        try:
            # Auto-detect input type by inspecting the file if it exists.
            p = Path(fp)
            if p.exists():

                def _detect_input_type(path: Path) -> str:
                    # Prefer explicit CSV by extension
                    ext = path.suffix.lower()
                    if ext == ".csv":
                        return "csv"
                    if ext in (".xyz", ".dat"):
                        return "xyz"
                    # Peek at first non-empty line
                    try:
                        with path.open(
                            "r", encoding="utf-8", errors="ignore"
                        ) as fh:
                            for _ in range(10):
                                line = fh.readline()
                                if not line:
                                    break
                                s = line.strip()
                                if not s:
                                    continue
                                # CSV if it contains commas
                                if "," in s:
                                    return "csv"
                                # XYZ if it looks like three floats separated by whitespace
                                parts = s.split()
                                if len(parts) >= 3:
                                    try:
                                        [
                                            float(x.replace(",", ""))
                                            for x in parts[:3]
                                        ]
                                        return "xyz"
                                    except (ValueError, TypeError):
                                        pass
                                break
                    except (OSError, ValueError, TypeError):
                        pass
                    return "bmap"

                itype = _detect_input_type(p)
                if itype == "csv":
                    parser = CSVParser()
                    profiles = parser.parse_file(str(p))
                elif itype == "xyz":
                    profiles = read_xyz_profiles(str(p))
                else:
                    profiles = read_bmap_freeformat(fp)
            else:
                # File doesn't exist as a path; delegate to read_bmap_freeformat which
                # may handle glob patterns or other virtual paths the old tool supported.
                profiles = read_bmap_freeformat(fp)
            pd_x = _profiles_to_dict_for_axis(profiles, "x")
            pd_y = _profiles_to_dict_for_axis(profiles, "y")
            for pname, surveys in pd_x.items():
                all_profiles_x.setdefault(pname, []).extend(surveys)
            for pname, surveys in pd_y.items():
                all_profiles_y.setdefault(pname, []).extend(surveys)

            for profile in profiles:
                raw_date = profile.date or None
                date_norm = format_date_for_bmap(raw_date) if raw_date else ""
                date_key = None
                if raw_date:
                    try:
                        date_key = datetime.fromisoformat(str(raw_date))
                    except (ValueError, TypeError):
                        try:
                            date_key = datetime.strptime(
                                str(raw_date).upper(), "%d%b%Y"
                            )
                        except (ValueError, TypeError):
                            for fmt in (
                                "%m/%d/%Y",
                                "%d/%m/%Y",
                                "%m-%d-%Y",
                                "%d-%m-%Y",
                                "%Y/%m/%d",
                            ):
                                try:
                                    date_key = datetime.strptime(
                                        str(raw_date), fmt
                                    )
                                    break
                                except (ValueError, TypeError):
                                    continue

                # X axis
                coords_x = getattr(profile, "x", None)
                if coords_x is not None and len(coords_x) > 0:
                    xmin = float(min(coords_x))
                    xmax = float(max(coords_x))
                    all_surveys_x.append(
                        (profile.name, date_norm or "", date_key, xmin, xmax)
                    )

                # Y axis
                coords_y = getattr(profile, "y", None)
                if coords_y is not None and len(coords_y) > 0:
                    ymin = float(min(coords_y))
                    ymax = float(max(coords_y))
                    all_surveys_y.append(
                        (profile.name, date_norm or "", date_key, ymin, ymax)
                    )
        except (OSError, ValueError, TypeError) as e:
            print(f"⚠️  Warning: could not read '{fp}': {e}")

    if dir_input in ("x", "both") and not all_profiles_x:
        print("No valid X profiles found for the given pattern.")
    if dir_input in ("y", "both") and not all_profiles_y:
        print("No valid Y profiles found for the given pattern.")

    common_x = None
    common_y = None
    if dir_input in ("x", "both") and all_profiles_x:
        common_x = calculate_common_ranges(all_profiles_x, mhw_elev)
    if dir_input in ("y", "both") and all_profiles_y:
        common_y = calculate_common_ranges(all_profiles_y, mhw_elev)

    # Build combined per-survey rows keyed by (profile, date)
    combined_map: dict[tuple, dict] = {}
    for pname, date_norm, date_key, xmin, xmax in all_surveys_x:
        key = (pname, date_norm or "")
        ent = combined_map.setdefault(
            key,
            {
                "profile": pname,
                "date": date_norm or "",
                "date_key": date_key,
                "xmin": None,
                "xmax": None,
                "ymin": None,
                "ymax": None,
            },
        )
        ent["date_key"] = date_key
        ent["xmin"] = xmin
        ent["xmax"] = xmax

    for pname, date_norm, date_key, ymin, ymax in all_surveys_y:
        key = (pname, date_norm or "")
        ent = combined_map.setdefault(
            key,
            {
                "profile": pname,
                "date": date_norm or "",
                "date_key": date_key,
                "xmin": None,
                "xmax": None,
                "ymin": None,
                "ymax": None,
            },
        )
        ent["date_key"] = date_key
        ent["ymin"] = ymin
        ent["ymax"] = ymax

    combined_list: List[
        Tuple[
            str,
            str,
            datetime | None,
            float | None,
            float | None,
            float | None,
            float | None,
        ]
    ] = []
    for (pname, date_norm), ent in combined_map.items():
        combined_list.append(
            (
                ent["profile"],
                ent["date"],
                ent.get("date_key"),
                ent["xmin"],
                ent["xmax"],
                ent["ymin"],
                ent["ymax"],
            )
        )

    combined_list.sort(
        key=lambda e: (
            e[0],
            0 if e[2] is not None else 1,
            e[2] or datetime.max,
        )
    )

    display_rows: List[
        Tuple[str, str, float | None, float | None, float | None, float | None]
    ] = []
    for pname, date_norm, date_key, xmin, xmax, ymin, ymax in combined_list:
        display_rows.append((pname, date_norm or "", xmin, xmax, ymin, ymax))

    # Build per-profile summary
    summary_keys = set()
    if common_x is not None:
        summary_keys.update(common_x.keys())
    if common_y is not None:
        summary_keys.update(common_y.keys())

    summary_rows: List[
        Tuple[
            str,
            float | None,
            float | None,
            int | None,
            float | None,
            float | None,
            int | None,
        ]
    ] = []
    for pname in sorted(summary_keys):
        xmin = None
        xmax = None
        x_surveys = None
        ymin = None
        ymax = None
        y_surveys = None
        if common_x and pname in common_x:
            xs = common_x[pname]
            xmin = xs[0]
            xmax = xs[1]
            x_surveys = xs[2]
        if common_y and pname in common_y:
            ys = common_y[pname]
            ymin = ys[0]
            ymax = ys[1]
            y_surveys = ys[2]
        summary_rows.append(
            (pname, xmin, xmax, x_surveys, ymin, ymax, y_surveys)
        )

    if not display_rows and not summary_rows:
        print("No results to write.")
        input("\nPress Enter to continue...")
        return

    # Write outputs to auto-generated files
    base_dir = Path(matched_files[0]).parent if matched_files else Path.cwd()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    axis_label = dir_input
    base_name = f"output_bounds_{axis_label}_{ts}"
    written_files: List[Path] = []

    if display_rows:
        survey_csv = base_dir / f"{base_name}_surveys.csv"
        survey_txt = base_dir / f"{base_name}_surveys.txt"
        try:
            survey_csv.write_text(
                _format_survey_csv_combined(display_rows), encoding="utf-8"
            )
            survey_txt.write_text(
                _format_survey_table_combined(display_rows), encoding="utf-8"
            )
        except (OSError, IOError) as e:
            log_quick_tool_error(
                "bounds", f"Failed to write survey outputs: {e}", e
            )
            print(f"❌ Failed to write survey outputs: {e}")
        written_files.extend([survey_csv, survey_txt])

    if summary_rows:
        summary_csv = base_dir / f"{base_name}_summary.csv"
        summary_txt = base_dir / f"{base_name}_summary.txt"
        try:
            summary_csv.write_text(
                _format_summary_csv_combined(summary_rows), encoding="utf-8"
            )
            summary_txt.write_text(
                _format_summary_table_combined(summary_rows), encoding="utf-8"
            )
        except (OSError, IOError) as e:
            log_quick_tool_error(
                "bounds", f"Failed to write summary outputs: {e}", e
            )
            print(f"❌ Failed to write summary outputs: {e}")
        written_files.extend([summary_csv, summary_txt])

    # Optional shapefile: only for X analysis
    try:
        if dir_input in ("x", "both") and common_x:
            try:
                import fiona
            except ImportError:
                fiona = None

            if fiona:
                shp_path = base_dir / f"{base_name}_xon_xoff.shp"
                schema = {
                    "geometry": "Point",
                    "properties": {
                        "profile": "str:80",
                        "xon": "float",
                        "xoff": "float",
                        "dates": "str:254",
                        "kind": "str:8",
                        "X": "float",
                        "Y": "float",
                    },
                }

                # collect dates per profile
                dates_map: dict[str, List[str]] = {}
                for pname, date_norm, _k, _xmin, _xmax in all_surveys_x:
                    dates_map.setdefault(pname, []).append(
                        date_norm or "UNKNOWN"
                    )

                # find candidate baseline file or prompt
                baseline_file: Path | None = None
                # Only use a user-provided baseline file (src/profcalc/data/required_inputs/ProfileOriginAzimuths.csv)
                # or a file explicitly supplied by the user. Do NOT implicitly use
                # the packaged required_inputs file so we don't create shapefiles
                # unexpectedly when the user has not provided baseline data.
                candidates = [
                    Path(
                        "src/profcalc/data/required_inputs/ProfileOriginAzimuths.csv"
                    )
                ]
                for c in candidates:
                    if c.exists():
                        baseline_file = c
                        break

                if baseline_file is None:
                    user_bf = input(
                        "Enter origin azimuth file path to compute real-world X/Y for shapefile (press Enter to skip): "
                    ).strip()
                    if user_bf:
                        bf = Path(user_bf)
                        if bf.exists():
                            baseline_file = bf
                        else:
                            print(
                                f"⚠️  Baseline file not found: {bf}; shapefile will use Xon as X and Y=0.0"
                            )

                baselines = None
                convert_fn = None
                if baseline_file is not None:
                    try:
                        from profcalc.common.coordinate_transforms import (
                            convert_2d_to_3d_profile,
                            load_profile_baselines,
                        )

                        try:
                            baselines_raw = load_profile_baselines(
                                str(baseline_file)
                            )
                            baselines = {
                                str(k): v for k, v in baselines_raw.items()
                            }
                            convert_fn = convert_2d_to_3d_profile
                        except (OSError, ValueError, KeyError):
                            from profcalc.common.csv_io import (
                                _load_profile_origin_azimuths,
                            )

                            df = _load_profile_origin_azimuths(
                                str(baseline_file)
                            )
                            baselines = {}
                            for _idx, row in df.iterrows():
                                baselines[str(row["profile_id"])] = {
                                    "origin_x": float(
                                        str(row["origin_x"]).replace(",", "")
                                    )
                                    if row.get("origin_x") is not None
                                    else None,
                                    "origin_y": float(
                                        str(row["origin_y"]).replace(",", "")
                                    )
                                    if row.get("origin_y") is not None
                                    else None,
                                    "azimuth": float(row["azimuth"])
                                    if row.get("azimuth") is not None
                                    else None,
                                }
                            convert_fn = convert_2d_to_3d_profile
                    except (OSError, ValueError, KeyError) as _e:
                        print(
                            f"⚠️  Could not load baselines from {baseline_file}: {_e}; falling back to profile-local X coordinates"
                        )
                        baselines = None

                    # Baselines (if loaded) are available in `baselines` mapping.

                # If we could not load baselines, do not create a shapefile.
                if baselines is None:
                    print(
                        "⚠️  No origin azimuth baselines available; skipping shapefile creation."
                    )
                else:
                    # attempt to infer a CRS from available baselines (origins)
                    crs_wkt = None
                    try:
                        from profcalc.common.crs_utils import (
                            infer_state_plane_crs_from_samples,
                        )

                        samples = []
                        for bb in baselines.values():
                            ox = bb.get("x0") or bb.get("origin_x")
                            oy = bb.get("y0") or bb.get("origin_y")
                            if ox is not None and oy is not None:
                                try:
                                    samples.append((float(ox), float(oy)))
                                except (ValueError, TypeError):
                                    continue

                        if samples:
                            crs_obj, crs_label = (
                                infer_state_plane_crs_from_samples(samples)
                            )
                            if crs_obj is not None:
                                try:
                                    crs_wkt = crs_obj.to_wkt()
                                except (AttributeError, ValueError, TypeError):
                                    try:
                                        crs_wkt = crs_obj.to_string()
                                    except (
                                        AttributeError,
                                        ValueError,
                                        TypeError,
                                    ):
                                        crs_wkt = None
                    except (OSError, ValueError, AttributeError, TypeError):
                        crs_wkt = None

                    # write shapefile
                    crs_param = crs_wkt if crs_wkt else {}
                    with fiona.open(
                        str(shp_path),
                        mode="w",
                        driver="ESRI Shapefile",
                        schema=schema,
                        crs=crs_param,
                    ) as dst:
                        for pname in sorted(common_x.keys()):
                            xs = common_x[pname]
                            xon_v = xs[0]
                            xoff_v = xs[1]
                            if xon_v is None and xoff_v is None:
                                continue

                            dates_list = dates_map.get(pname, [])
                            if not dates_list:
                                dates_s = "UNKNOWN"
                            else:
                                seen = set()
                                deduped = []
                                for d in dates_list:
                                    if d not in seen:
                                        seen.add(d)
                                        deduped.append(d)
                                dates_s = ",".join(deduped)

                            e_on = n_on = e_off = n_off = None
                            if baselines is not None and pname in baselines:
                                b = baselines[pname]
                                origin_x = b.get("x0") or b.get("origin_x")
                                origin_y = b.get("y0") or b.get("origin_y")
                                azimuth = b.get("azimuth")
                                try:
                                    if xon_v is not None:
                                        xs_e, ys_n, _ = convert_fn(
                                            np.array([xon_v], dtype=float),
                                            np.array([0.0], dtype=float),
                                            float(origin_x),
                                            float(origin_y),
                                            float(azimuth),
                                        )
                                        e_on = float(xs_e[0])
                                        n_on = float(ys_n[0])
                                    if xoff_v is not None:
                                        xs_e, ys_n, _ = convert_fn(
                                            np.array([xoff_v], dtype=float),
                                            np.array([0.0], dtype=float),
                                            float(origin_x),
                                            float(origin_y),
                                            float(azimuth),
                                        )
                                        e_off = float(xs_e[0])
                                        n_off = float(ys_n[0])
                                except (ValueError, TypeError):
                                    e_on = n_on = e_off = n_off = None

                            if xon_v is not None:
                                geom_x = (
                                    e_on if e_on is not None else float(xon_v)
                                )
                                geom_y = n_on if n_on is not None else 0.0
                                rec_on = {
                                    "geometry": {
                                        "type": "Point",
                                        "coordinates": (geom_x, geom_y),
                                    },
                                    "properties": {
                                        "profile": str(pname),
                                        "xon": float(xon_v),
                                        "xoff": float(xoff_v)
                                        if xoff_v is not None
                                        else None,
                                        "dates": dates_s,
                                        "kind": "xon",
                                        "X": geom_x,
                                        "Y": geom_y,
                                    },
                                }
                                dst.write(rec_on)

                            if xoff_v is not None:
                                geom_x = (
                                    e_off
                                    if e_off is not None
                                    else float(xoff_v)
                                )
                                geom_y = n_off if n_off is not None else 0.0
                                rec_off = {
                                    "geometry": {
                                        "type": "Point",
                                        "coordinates": (geom_x, geom_y),
                                    },
                                    "properties": {
                                        "profile": str(pname),
                                        "xon": float(xon_v)
                                        if xon_v is not None
                                        else None,
                                        "xoff": float(xoff_v),
                                        "dates": dates_s,
                                        "kind": "xoff",
                                        "X": geom_x,
                                        "Y": geom_y,
                                    },
                                }
                                dst.write(rec_off)

                    # Only record the shapefile path if we actually created it
                    # (i.e., baselines was not None). When baselines is None we
                    # skipped shapefile creation above.
                    written_files.append(shp_path)
    except (OSError, IOError, ValueError) as e:
        print(f"⚠️ Warning: could not write shapefile: {e}")

    if not written_files:
        print("No results to write.")
        input("\nPress Enter to continue...")
        return

    print("✅ Results written:")
    for p in written_files:
        print(f"   {p}")

    input("\nPress Enter to continue...")

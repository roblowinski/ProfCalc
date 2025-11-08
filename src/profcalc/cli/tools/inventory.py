"""Inventory report generator

Generate comprehensive inventory reports for BMAP and related profile
files. The report includes profile counts, survey dates, point statistics,
elevation ranges and basic metadata.

Usage examples:
    - CLI: call the module's CLI entry (if available) or import
        :func:`generate_inventory_report` directly.

            python -m profcalc.cli.tools.inventory input.bmap -o inventory.txt

    - Menu: Quick Tools → Inventory (invokes :func:`execute_from_menu`).
"""

import argparse
from pathlib import Path
from typing import Any, Dict, List

from tabulate import tabulate

from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.cli.quick_tools.quick_tool_utils import (
    default_output_path,
    timestamped_output_path,
)
from profcalc.common.bmap_io import read_bmap_freeformat


def execute_from_cli(args: list[str]) -> None:
    """
    Execute file inventory from command line.

    Args:
        args: Command-line arguments (excluding the -i flag)
    """
    parser = argparse.ArgumentParser(
        prog="profcalc -i",
        description="Generate comprehensive inventory report for BMAP files",
    )
    parser.add_argument("file", help="BMAP file to inventory")
    parser.add_argument(
        "-o",
        "--output",
        required=False,
        help="Output report file path (default: output_inventory.txt)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Include detailed per-profile statistics",
    )

    parsed_args = parser.parse_args(args)

    # Execute inventory
    print(f"🔍 Analyzing {parsed_args.file}...")
    report = generate_inventory_report(
        parsed_args.file, verbose=parsed_args.verbose
    )

    # Write output
    out_path = parsed_args.output
    if not out_path:
        out_path = default_output_path(
            "inventory", parsed_args.file, ext=".txt"
        )
    try:
        Path(out_path).write_text(report, encoding="utf-8")
        print(f"✅ Inventory report written to: {out_path}")
    except Exception as e:
        log_quick_tool_error(
            "inventory", f"Failed to write inventory report: {e}"
        )
        print(f"❌ Failed to write inventory report: {e}")


def generate_inventory_report(file_path: str, verbose: bool = False) -> str:
    """
    Generate comprehensive inventory report for a BMAP file.

    Args:
        file_path: Path to BMAP file
        verbose: Whether to include detailed per-profile statistics

    Returns:
        Formatted inventory report string
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read profiles
    profiles = read_bmap_freeformat(file_path)

    # Calculate statistics
    stats = _calculate_file_statistics(profiles)

    # Generate report
    return _format_inventory_report(path, profiles, stats, verbose)


def _calculate_file_statistics(
    profiles: list,
) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics from profiles.

    Args:
        profiles: List of Profile objects

    Returns:
        Dictionary of statistics
    """
    total_profiles = len(profiles)
    total_points = sum(len(p.x) for p in profiles)

    # Collect dates
    dates = [p.date for p in profiles if p.date]
    unique_dates = sorted(set(dates)) if dates else []

    # Collect profile names and count duplicates
    profile_names: Dict[str, int] = {}
    for p in profiles:
        profile_names[p.name] = profile_names.get(p.name, 0) + 1

    unique_profile_names = len(profile_names)

    # Calculate elevation statistics
    all_elevations = []
    for p in profiles:
        all_elevations.extend(p.z.tolist())

    min_elev = min(all_elevations) if all_elevations else 0.0
    max_elev = max(all_elevations) if all_elevations else 0.0
    avg_elev = (
        sum(all_elevations) / len(all_elevations) if all_elevations else 0.0
    )

    # Calculate X coordinate statistics
    all_x = []
    for p in profiles:
        all_x.extend(p.x.tolist())

    min_x = min(all_x) if all_x else 0.0
    max_x = max(all_x) if all_x else 0.0

    # Profile point statistics
    points_per_profile = [len(p.x) for p in profiles]
    min_points = min(points_per_profile) if points_per_profile else 0
    max_points = max(points_per_profile) if points_per_profile else 0
    avg_points = (
        sum(points_per_profile) / len(points_per_profile)
        if points_per_profile
        else 0
    )

    return {
        "total_profiles": total_profiles,
        "unique_profile_names": unique_profile_names,
        "profile_names": profile_names,
        "total_points": total_points,
        "dates": unique_dates,
        "min_elev": min_elev,
        "max_elev": max_elev,
        "avg_elev": avg_elev,
        "min_x": min_x,
        "max_x": max_x,
        "min_points": min_points,
        "max_points": max_points,
        "avg_points": avg_points,
    }


def _format_inventory_report(
    path: Path,
    profiles: list,
    stats: Dict[str, Any],
    verbose: bool,
) -> str:
    """
    Format inventory report.

    Args:
        path: Path to BMAP file
        profiles: List of Profile objects
        stats: Statistics dictionary
        verbose: Whether to include detailed per-profile info

    Returns:
        Formatted report string
    """

    # Table 1: One line per profile & survey date
    table1_headers = [
        "PROFILE ID",
        "SURVEY START DATE",
        "SURVEY END DATE",
        "FILE NAME",
    ]
    table1_rows = []
    for profile in profiles:
        # For BMAP, survey start and end date are the same (single date per profile)
        survey_date = profile.date if profile.date else "Not specified"
        table1_rows.append([profile.name, survey_date, survey_date, path.name])

    table1 = tabulate(table1_rows, headers=table1_headers, tablefmt="github")

    # Table 2: Per-profile summary (group by profile name)
    from collections import defaultdict

    profile_dates: dict[str, List[str]] = defaultdict(list)
    for profile in profiles:
        if profile.date:
            profile_dates[profile.name].append(profile.date)
        else:
            profile_dates[profile.name].append("")

    table2_headers = [
        "PROFILE ID",
        "NUMBER OF SURVEYS",
        "DATE OF FIRST SURVEY",
        "DATE OF LAST SURVEY",
    ]
    table2_rows = []
    for pname, dates in sorted(profile_dates.items()):
        # Remove empty dates, sort
        clean_dates = sorted([d for d in dates if d])
        n_surveys = len(dates)
        first_date = clean_dates[0] if clean_dates else "Not specified"
        last_date = clean_dates[-1] if clean_dates else "Not specified"
        table2_rows.append([pname, n_surveys, first_date, last_date])

    table2 = tabulate(table2_rows, headers=table2_headers, tablefmt="github")

    lines = [
        "=" * 80,
        "BMAP FILE INVENTORY REPORT",
        "=" * 80,
        f"File: {path.name}",
        f"Path: {path.parent}",
        f"Size: {path.stat().st_size:,} bytes",
        "",
        "PROFILE & SURVEY TABLE",
        table1,
        "",
        "PROFILE SUMMARY TABLE",
        table2,
        "",
        "=" * 80,
    ]
    return "\n".join(lines)


def execute_from_menu() -> None:
    """Execute file inventory from interactive menu."""
    print("\n" + "=" * 60)
    print("BMAP FILE INVENTORY")
    print("=" * 60)

    # Get user inputs
    import glob

    input_patterns = input(
        "Enter BMAP/data file path(s) or wildcard(s) (e.g., '*.dat src/profcalc/data/required_inputs/*.bmap'): "
    ).strip()

    output_file = timestamped_output_path("inventory", ext=".txt")

    verbose_input = (
        input("Include detailed per-profile information? (y/n) [n]: ")
        .strip()
        .lower()
    )
    verbose = verbose_input == "y"

    # Expand wildcards and split input
    patterns = input_patterns.split()
    all_files = set()
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if not matches:
            print(f"⚠️  No files matched pattern: {pattern}")
        all_files.update(matches)
    all_files = sorted(all_files)
    if not all_files:
        print("❌ No files to process. Exiting.")
        input("\nPress Enter to continue...")
        return

    try:
        print(
            f"\n🔄 Generating inventory report for {len(all_files)} file(s)..."
        )

        report = generate_inventory_report(all_files, verbose=verbose)

        Path(output_file).write_text(report, encoding="utf-8")

        # Print summary
        print("\n" + report)
        print(f"\n✅ Report saved to: {output_file}")

    except FileNotFoundError as e:
        log_quick_tool_error(
            "inventory", f"File not found during inventory generation: {e}"
        )
        print(f"\n❌ Error: {e}")
    except (OSError, ValueError, TypeError, RuntimeError) as e:
        log_quick_tool_error(
            "inventory", f"Unexpected error during inventory generation: {e}"
        )
        print(f"\n❌ Unexpected error: {e}")

    input("\nPress Enter to continue...")

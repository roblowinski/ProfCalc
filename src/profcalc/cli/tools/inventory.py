# =============================================================================
# Beach Profile Inventory Report Generator
# =============================================================================
#
# FILE: src/profcalc/cli/tools/inventory.py
#
# PURPOSE:
# This tool generates comprehensive inventory reports for BMAP and related
# beach profile files, providing detailed metadata and statistics about survey
# data collections. It analyzes file contents to extract profile counts, survey
# dates, point statistics, elevation ranges, and other key metadata for data
# management and quality assessment.
#
# WHAT IT'S FOR:
# - Analyzes BMAP and compatible profile data files
# - Generates detailed inventory reports with file metadata
# - Provides profile counts, date ranges, and spatial statistics
# - Supports both single file and batch directory analysis
# - Offers verbose mode for detailed per-profile breakdowns
# - Enables data discovery and quality assessment workflows
# - Supports multiple file selection through graphical dialogs
#
# WORKFLOW POSITION:
# This tool is used in the "Quick Tools" section for data exploration and
# management. It's typically one of the first tools used when working with
# new survey datasets, helping users understand what data they have before
# proceeding to detailed analysis. It's also useful for data validation and
# quality control processes.
#
# LIMITATIONS:
# - Primarily designed for BMAP format files (may work with similar formats)
# - Statistical calculations assume standard profile data structure
# - Directory scanning is recursive and may be slow for large file collections
# - Report formatting depends on tabulate library for table display
# - Memory usage scales with number of profiles and file size
#
# ASSUMPTIONS:
# - Input files contain valid beach profile data in supported formats
# - File system permissions allow reading of selected files and directories
# - Profile data includes standard fields (X, Z coordinates, dates, etc.)
# - Users can interpret statistical summaries and metadata reports
# - Tabulate library is available for report formatting
#
# =============================================================================

"""Inventory report generator

Generate comprehensive inventory reports for BMAP and related profile
files. The report includes profile counts, survey dates, point statistics,
elevation ranges and basic metadata.

Usage examples:
    - Menu: Quick Tools → Inventory (invokes :func:`execute_from_menu`).
"""

from pathlib import Path
from typing import Any, Dict, List

from tabulate import tabulate

from profcalc.cli.file_dialogs import select_directory, select_multiple_files
from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.cli.quick_tools.quick_tool_utils import (
    timestamped_output_path,
)
from profcalc.common.bmap_io import read_bmap_freeformat


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
    avg_elev = sum(all_elevations) / len(all_elevations) if all_elevations else 0.0

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
        sum(points_per_profile) / len(points_per_profile) if points_per_profile else 0
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
    import os

    print("\nSelect files to inventory:")
    print("1. Select individual files")
    print("2. Select directories to scan recursively")
    print("3. Cancel")

    choice = input("\nSelect option [1/2/3]: ").strip()

    all_files = set()

    if choice == "1":
        # Select multiple individual files
        selected_files = select_multiple_files("Select BMAP/data files for inventory")
        if not selected_files:
            print("❌ No files selected. Exiting.")
            input("\nPress Enter to continue...")
            return
        all_files.update(selected_files)

    elif choice == "2":
        # Select directories to scan
        selected_dirs = []
        while True:
            dir_path = select_directory("Select directory to scan for BMAP/data files")
            if not dir_path:
                break
            selected_dirs.append(dir_path)
            if input("Select another directory? (y/N): ").strip().lower() != "y":
                break

        if not selected_dirs:
            print("❌ No directories selected. Exiting.")
            input("\nPress Enter to continue...")
            return

        # Scan selected directories for common file extensions
        for dir_path in selected_dirs:
            # Look for common profile file extensions
            for ext in ["*.dat", "*.bmap", "*.txt", "*.csv"]:
                pattern = os.path.join(dir_path, "**", ext)
                matches = glob.glob(pattern, recursive=True)
                all_files.update(matches)

    else:
        print("❌ Cancelled.")
        input("\nPress Enter to continue...")
        return

    all_files = sorted(all_files)
    if not all_files:
        print("❌ No files found to process. Exiting.")
        input("\nPress Enter to continue...")
        return

    output_file = timestamped_output_path("inventory", ext=".txt")

    verbose_input = (
        input("Include detailed per-profile information? (y/n) [n]: ").strip().lower()
    )
    verbose = verbose_input == "y"

    try:
        print(f"\n🔄 Generating inventory report for {len(all_files)} file(s)...")

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

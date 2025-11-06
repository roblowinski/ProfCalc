"""
File Inventory - Generate comprehensive inventory reports for BMAP files.

Analyzes BMAP free format files and generates detailed reports showing:
- Total profile count
- Survey dates
- Point statistics
- Elevation ranges
- File metadata
"""

import argparse
from pathlib import Path
from typing import Any, Dict

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
        "-o", "--output", required=True, help="Output report file path"
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
    Path(parsed_args.output).write_text(report, encoding="utf-8")
    print(f"✅ Inventory report written to: {parsed_args.output}")


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
    lines = [
        "=" * 80,
        "BMAP FILE INVENTORY REPORT",
        "=" * 80,
        f"File: {path.name}",
        f"Path: {path.parent}",
        f"Size: {path.stat().st_size:,} bytes",
        "",
        "SUMMARY STATISTICS",
        "-" * 80,
        f"Total Surveys: {stats['total_profiles']}",
        f"Unique Profile Names: {stats['unique_profile_names']}",
        f"Total Data Points: {stats['total_points']:,}",
        f"Average Points per Survey: {stats['avg_points']:.1f}",
        "",
    ]

    # Date range
    if stats["dates"]:
        lines.append("SURVEY DATES")
        lines.append("-" * 80)
        lines.append(
            f"Date Range: {stats['dates'][0]} to {stats['dates'][-1]}"
        )
        lines.append(f"Total Survey Dates: {len(stats['dates'])}")
        if len(stats["dates"]) <= 10:
            lines.append("Dates: " + ", ".join(stats["dates"]))
        lines.append("")

    # Coordinate ranges
    lines.extend(
        [
            "COORDINATE RANGES",
            "-" * 80,
            f"X Range: {stats['min_x']:.2f} to {stats['max_x']:.2f} ft "
            f"(span: {stats['max_x'] - stats['min_x']:.2f} ft)",
            f"Z Range: {stats['min_elev']:.2f} to {stats['max_elev']:.2f} ft NAVD88 "
            f"(span: {stats['max_elev'] - stats['min_elev']:.2f} ft)",
            f"Average Elevation: {stats['avg_elev']:.2f} ft NAVD88",
            "",
        ]
    )

    # Point statistics
    lines.extend(
        [
            "POINT STATISTICS",
            "-" * 80,
            f"Minimum Points per Survey: {stats['min_points']}",
            f"Maximum Points per Survey: {stats['max_points']}",
            f"Average Points per Survey: {stats['avg_points']:.1f}",
            "",
        ]
    )

    # Profile name summary
    lines.extend(
        [
            "PROFILE SUMMARY",
            "-" * 80,
        ]
    )

    for profile_name, count in sorted(stats["profile_names"].items()):
        survey_text = "survey" if count == 1 else "surveys"
        lines.append(f"  {profile_name}: {count} {survey_text}")

    lines.append("")

    # Detailed per-profile information if verbose
    if verbose:
        lines.extend(
            [
                "DETAILED PROFILE INFORMATION",
                "-" * 80,
            ]
        )

        for i, profile in enumerate(profiles, 1):
            lines.append(f"\nSurvey #{i}: {profile.name}")
            lines.append(
                f"  Date: {profile.date if profile.date else 'Not specified'}"
            )
            lines.append(
                f"  Description: {profile.description if profile.description else 'None'}"
            )
            lines.append(f"  Points: {len(profile.x)}")
            lines.append(
                f"  X Range: {min(profile.x):.2f} to {max(profile.x):.2f} ft"
            )
            lines.append(
                f"  Z Range: {min(profile.z):.2f} to {max(profile.z):.2f} ft NAVD88"
            )
            lines.append(
                f"  Avg Elevation: {sum(profile.z) / len(profile.z):.2f} ft NAVD88"
            )

        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)


def execute_from_menu() -> None:
    """Execute file inventory from interactive menu."""
    print("\n" + "=" * 60)
    print("BMAP FILE INVENTORY")
    print("=" * 60)

    # Get user inputs
    input_file = input("Enter BMAP file path: ").strip()
    output_file = input("Enter output report file path: ").strip()

    verbose_input = (
        input("Include detailed per-profile information? (y/n) [n]: ")
        .strip()
        .lower()
    )
    verbose = verbose_input == "y"

    try:
        print("\n🔄 Generating inventory report...")

        report = generate_inventory_report(input_file, verbose=verbose)

        Path(output_file).write_text(report, encoding="utf-8")

        # Print summary
        print("\n" + report)
        print(f"\n✅ Report saved to: {output_file}")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except (OSError, ValueError, TypeError, RuntimeError) as e:
        print(f"\n❌ Unexpected error: {e}")

    input("\nPress Enter to continue...")

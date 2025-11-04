"""
Bounds Finder - Find common X coordinate ranges across BMAP profiles.

Quick command-line tool to extract common X bounds from BMAP free format files.
"""

import argparse
import glob
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from profcalc.common.bmap_io import read_bmap_freeformat
from profcalc.core.profile_stats import calculate_common_ranges


def _profiles_to_dict(
    profiles: Iterable[Any],
) -> Dict[str, List[List[Tuple[float, float]]]]:
    """Convert profile objects to the dict format expected by
    `calculate_common_ranges`.

    Args:
        profiles: An iterable of profile objects returned by
            ``read_bmap_freeformat``. Each object must expose ``x`` and
            ``z`` sequence attributes (coordinates) and a string ``name``.

    Returns:
        Mapping from profile name to list of surveys. Each survey is a list
        of ``(x, z)`` tuples (floats).
    """
    result = defaultdict(list)
    for profile in profiles:
        # Convert numpy arrays to list of tuples
        points = [(float(x), float(z)) for x, z in zip(profile.x, profile.z)]
        result[profile.name].append(points)
    return dict(result)


def execute_from_cli(args: List[str]) -> None:
    """Run the bounds finder from the command line.

    This parses CLI arguments, reads BMAP free-format file(s), computes the
    common X ranges for each profile, formats the results and writes them to
    disk.

    Args:
        args: List of command-line arguments (typically ``sys.argv[1:]``).

    Raises:
        SystemExit: If no files are found or no valid profiles are parsed.
    """
    parser = argparse.ArgumentParser(
        prog="profcalc -b",
        description="Find common X coordinate bounds per profile",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="BMAP file(s) to analyze (wildcards supported)",
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Output file path"
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["table", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--mhw",
        type=float,
        help="Optional MHW elevation (ft NAVD88) for additional metrics",
    )

    parsed_args = parser.parse_args(args)

    # Expand wildcards and collect all files
    all_files = []
    for pattern in parsed_args.files:
        matched_files = glob.glob(pattern)
        if matched_files:
            all_files.extend(matched_files)
        else:
            # If no wildcard match, assume it's a direct file path
            all_files.append(pattern)

    if not all_files:
        print("Error: No files found matching the pattern(s)", file=sys.stderr)
        sys.exit(1)

    # Parse all files and combine profiles
    print(f"📂 Reading {len(all_files)} file(s)...")
    all_profiles: dict[str, list] = {}

    for file_path in all_files:
        try:
            profiles = read_bmap_freeformat(file_path)
            profile_dict = _profiles_to_dict(profiles)
            # Merge profiles (combine surveys from different files)
            for profile_name, surveys in profile_dict.items():
                if profile_name not in all_profiles:
                    all_profiles[profile_name] = []
                all_profiles[profile_name].extend(surveys)
        except Exception as e:
            print(f"⚠️  Warning: Error reading {file_path}: {e}")
            continue

    if not all_profiles:
        print("Error: No valid profiles found in input files", file=sys.stderr)
        sys.exit(1)

    # Calculate common ranges
    print(f"📊 Analyzing {len(all_profiles)} profile(s)...")
    common_ranges = calculate_common_ranges(
        all_profiles, mhw_elev=parsed_args.mhw
    )

    # Format output
    if parsed_args.format == "csv":
        output = _format_csv(
            common_ranges, mhw_provided=parsed_args.mhw is not None
        )
    else:
        output = _format_table(
            common_ranges, mhw_provided=parsed_args.mhw is not None
        )

    # Write output
    Path(parsed_args.output).write_text(output)
    print(f"✅ Results written to {parsed_args.output}")
    print(f"   Profiles analyzed: {len(common_ranges)}")


def _format_table(
    ranges: Dict[
        str,
        Tuple[
            float,
            float,
            int,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            str,
        ],
    ],
    mhw_provided: bool = False,
) -> str:
    """Format the computed ranges into a human-readable ASCII table.

    Args:
        ranges: Mapping from profile name to a statistics tuple. The tuple
            layout is produced by :func:`calculate_common_ranges` (see that
            function for precise ordering of elements).
        mhw_provided: If True, include the beach type / MHW-related column in
            the output.

    Returns:
        A multi-line string containing the formatted table.
    """
    lines = ["=" * 80]
    lines.append("BMAP COMMON BOUNDS ANALYSIS")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total Profiles: {len(ranges)}")
    lines.append("")
    lines.append("-" * 80)

    if mhw_provided:
        lines.append(
            f"{'Profile':<12} | {'Xmin (ft)':>10} | {'Xmax (ft)':>10} | "
            f"{'Range (ft)':>11} | {'Surveys':>7} | {'Beach Type':<13}"
        )
    else:
        lines.append(
            f"{'Profile':<12} | {'Xmin (ft)':>10} | {'Xmax (ft)':>10} | "
            f"{'Range (ft)':>11} | {'Surveys':>7}"
        )

    lines.append("-" * 80)

    for profile_name, stats in sorted(ranges.items()):
        xmin, xmax, num_surveys = stats[0], stats[1], stats[2]
        beach_type = stats[14] if len(stats) > 14 else "UNKNOWN"
        range_ft = xmax - xmin

        if mhw_provided:
            lines.append(
                f"{profile_name:<12} | {xmin:>10.2f} | {xmax:>10.2f} | "
                f"{range_ft:>11.2f} | {num_surveys:>7} | {beach_type:<13}"
            )
        else:
            lines.append(
                f"{profile_name:<12} | {xmin:>10.2f} | {xmax:>10.2f} | "
                f"{range_ft:>11.2f} | {num_surveys:>7}"
            )

    lines.append("-" * 80)
    return "\n".join(lines)


def _format_csv(
    ranges: Dict[
        str,
        Tuple[
            float,
            float,
            int,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            str,
        ],
    ],
    mhw_provided: bool = False,
) -> str:
    """Format the computed ranges as CSV.

    Args:
        ranges: Mapping from profile name to a statistics tuple.
        mhw_provided: Whether MHW elevation was supplied and CSV should
            include the beach type column.

    Returns:
        CSV text where each row corresponds to one profile's summary.
    """
    if mhw_provided:
        lines = ["profile,xmin_ft,xmax_ft,range_ft,num_surveys,beach_type"]
    else:
        lines = ["profile,xmin_ft,xmax_ft,range_ft,num_surveys"]

    for profile_name, stats in sorted(ranges.items()):
        xmin, xmax, num_surveys = stats[0], stats[1], stats[2]
        beach_type = stats[14] if len(stats) > 14 else "UNKNOWN"
        range_ft = xmax - xmin

        if mhw_provided:
            lines.append(
                f"{profile_name},{xmin:.2f},{xmax:.2f},{range_ft:.2f},{num_surveys},{beach_type}"
            )
        else:
            lines.append(
                f"{profile_name},{xmin:.2f},{xmax:.2f},{range_ft:.2f},{num_surveys}"
            )

    return "\n".join(lines)


def execute_from_menu() -> None:
    """Interactive menu wrapper for the bounds finder.

    Prompts the user for a file pattern, output destination and optional
    MHW elevation, then forwards the constructed arguments to
    :func:`execute_from_cli`.
    """
    print("\n" + "=" * 60)
    print("FIND COMMON BOUNDS")
    print("=" * 60)

    # Get user inputs
    file_pattern = input("Enter BMAP file pattern (e.g., *.dat): ").strip()
    output_file = input("Enter output file path: ").strip()

    format_input = input("Output format (table/csv) [table]: ").strip().lower()
    format_type = "csv" if format_input == "csv" else "table"

    mhw_input = input(
        "Enter MHW elevation (ft NAVD88) [optional, press Enter to skip]: "
    ).strip()
    mhw_elev = float(mhw_input) if mhw_input else None

    try:
        # Build args list for execute_from_cli
        args = [file_pattern, "-o", output_file, "-f", format_type]
        if mhw_elev is not None:
            args.extend(["--mhw", str(mhw_elev)])

        # Execute
        execute_from_cli(args)

    except Exception as e:
        print(f"\n❌ Error: {e}")

    input("\nPress Enter to continue...")

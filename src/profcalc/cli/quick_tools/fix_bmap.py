"""
Fix BMAP Point Counts - Correct inaccurate point counts in BMAP files.

Scans BMAP free format files and corrects the point count on line 2 of each
profile to match the actual number of coordinate points in the file.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Tuple


def execute_from_cli(args: list[str]) -> None:
    """
    Execute BMAP point count fixer from command line.

    Args:
        args: Command-line arguments (excluding the -f flag)
    """
    parser = argparse.ArgumentParser(
        prog="profcalc -f",
        description="Fix incorrect point counts in BMAP free format files",
    )
    parser.add_argument("input_file", help="Input BMAP file to fix")
    parser.add_argument("-o", "--output", required=True, help="Output corrected BMAP file")
    parser.add_argument("--report", help="Optional correction report file")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed correction information",
    )

    parsed_args = parser.parse_args(args)

    # Execute fix
    print(f"🔍 Analyzing {parsed_args.input_file}...")
    corrections = fix_bmap_point_counts(
        parsed_args.input_file, parsed_args.output, verbose=parsed_args.verbose
    )

    # Generate report
    report = _generate_correction_report(
        parsed_args.input_file, parsed_args.output, corrections
    )

    # Output report
    if parsed_args.report:
        Path(parsed_args.report).write_text(report)
        print(f"📄 Correction report written to: {parsed_args.report}")
    else:
        print("\n" + report)


def _is_header_line(line: str) -> bool:
    """
    Check if a line is a profile header (starts with non-numeric token).

    Args:
        line: Line to check

    Returns:
        True if line is a profile header, False if it's a coordinate line
    """
    if not line.strip():
        return False
    first_token = line.strip().split()[0]
    # Headers start with letters or profile names, coordinates start with numbers
    return not first_token[0].isdigit() and first_token[0] not in ['+', '-', '.']


def fix_bmap_point_counts(
    input_file: str, output_file: str, verbose: bool = False
) -> Dict[str, Tuple[int, int]]:
    """
    Fix point counts in BMAP file and write corrected version.

    Args:
        input_file: Path to input BMAP file
        output_file: Path to output corrected file
        verbose: Whether to show detailed progress

    Returns:
        Dictionary mapping profile names to (declared_count, actual_count) tuples
        for profiles that needed correction
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    corrections: Dict[str, Tuple[int, int]] = {}
    total_profiles = 0

    with input_path.open("r") as infile, output_path.open("w") as outfile:
        lines = infile.readlines()
        i = 0

        while i < len(lines):
            # Skip empty lines
            while i < len(lines) and not lines[i].strip():
                outfile.write(lines[i])
                i += 1

            if i >= len(lines):
                break

            # Read profile header (line 1)
            if not _is_header_line(lines[i]):
                # Not a valid header, skip
                outfile.write(lines[i])
                i += 1
                continue

            total_profiles += 1
            profile_name = lines[i].strip().split()[0]
            outfile.write(lines[i])
            i += 1

            if i >= len(lines):
                break

            # Read point count line (line 2)
            try:
                declared_count = int(lines[i].strip())
            except ValueError:
                print(
                    f"⚠️  Warning: Invalid point count for {profile_name}, skipping",
                    file=sys.stderr,
                )
                outfile.write(lines[i])
                i += 1
                continue

            i += 1

            # Read actual coordinate points until we hit the next header or EOF
            points = []
            while i < len(lines):
                # Stop if we hit the next profile header or an empty line followed by a header
                if _is_header_line(lines[i]):
                    break
                if not lines[i].strip():
                    # Check if next non-empty line is a header
                    j = i + 1
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    if j < len(lines) and _is_header_line(lines[j]):
                        break
                points.append(lines[i])
                i += 1

            actual_count = len(points)

            # Check if correction needed
            if declared_count != actual_count:
                corrections[profile_name] = (declared_count, actual_count)
                if verbose:
                    diff = actual_count - declared_count
                    sign = "+" if diff > 0 else ""
                    print(f"  ✏️  {profile_name}: {declared_count} → {actual_count} ({sign}{diff})")

            # Write corrected count and points
            outfile.write(f"{actual_count}\n")
            for point_line in points:
                outfile.write(point_line)

    return corrections


def _generate_correction_report(
    input_file: str, output_file: str, corrections: Dict[str, Tuple[int, int]]
) -> str:
    """
    Generate human-readable correction report.

    Args:
        input_file: Input file path
        output_file: Output file path
        corrections: Dictionary of corrections made

    Returns:
        Formatted report string
    """
    lines = [
        "=" * 60,
        "BMAP POINT COUNT CORRECTION REPORT",
        "=" * 60,
        f"Input File:  {input_file}",
        f"Output File: {output_file}",
        "",
    ]

    if corrections:
        lines.append(f"Profiles Corrected: {len(corrections)}")
        lines.append("")
        lines.append("Corrections Made:")
        lines.append("-" * 60)

        for profile_name, (declared, actual) in sorted(corrections.items()):
            diff = actual - declared
            sign = "+" if diff > 0 else ""
            lines.append(
                f"  {profile_name:<12} | Declared: {declared:>4} | Actual: {actual:>4} | "
                f"Diff: {sign}{diff:>4}"
            )

        lines.append("-" * 60)
        lines.append("")
        lines.append("✅ All corrections applied successfully")
    else:
        lines.append("✅ No corrections needed - all point counts accurate")

    lines.append("=" * 60)
    return "\n".join(lines)


def execute_from_menu() -> None:
    """Execute BMAP point count fixer from interactive menu."""
    print("\n" + "=" * 60)
    print("FIX BMAP POINT COUNTS")
    print("=" * 60)

    # Get user inputs
    input_file = input("Enter input BMAP file path: ").strip()
    output_file = input("Enter output file path: ").strip()

    verbose_input = input("Show detailed corrections? (y/n) [n]: ").strip().lower()
    verbose = verbose_input == "y"

    report_input = input("Save report to file? (y/n) [n]: ").strip().lower()
    report_file = None
    if report_input == "y":
        report_file = input("Enter report file path: ").strip()

    try:
        print("\n🔄 Analyzing BMAP file and fixing point counts...")

        corrections = fix_bmap_point_counts(input_file, output_file, verbose=verbose)

        report = _generate_correction_report(input_file, output_file, corrections)

        if report_file:
            Path(report_file).write_text(report)
            print(f"\n📄 Report saved to: {report_file}")

        print("\n" + report)
        print(f"\n✅ Corrected file written to: {output_file}")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

    input("\nPress Enter to continue...")


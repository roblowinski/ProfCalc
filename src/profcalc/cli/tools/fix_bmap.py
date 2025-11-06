"""
Fix BMAP Point Counts - Correct inaccurate point counts in BMAP files.

Scans BMAP free format files and corrects the point count on line 2 of each
profile to match the actual number of coordinate points in the file.

Supports multiple input formats:
- BMAP free format (any extension)
- CSV files (with/without headers, automatic column detection)
- 9-column CSV with metadata headers
"""

import argparse
import glob
import sys
from pathlib import Path
from typing import Dict, Tuple

from profcalc.common.file_parser import ParsedFile, parse_file


def fix_bmap_point_counts(
    input_file, output_file, verbose=False, skip_confirmation=False
):
    """
    Fixes point counts in profile files (BMAP, CSV) and writes corrected output.

    Uses centralized format detection and parsing to support multiple input formats.

    Args:
        input_file: Path to input file
        output_file: Path to output file
        verbose: If True, print detailed corrections
        skip_confirmation: If True, skip format detection confirmation

    Returns:
        Dictionary of corrections: {profile_name: (declared_count, actual_count)}
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    # Parse file using centralized parser with format detection
    try:
        parsed = parse_file(input_path, skip_confirmation=skip_confirmation)
    except (OSError, ValueError, TypeError, ImportError) as e:
        if verbose:
            print(f"\n❌ Error parsing file: {e}")
        raise

    corrections = {}

    # Check each profile for point count discrepancies
    for profile in parsed.profiles:
        profile_id = profile["profile_id"]
        declared_count = profile.get("point_count", 0)
        actual_count = profile["actual_point_count"]

        if declared_count != actual_count:
            corrections[profile_id] = (declared_count, actual_count)
            if verbose:
                diff = actual_count - declared_count
                sign = "+" if diff > 0 else ""
                print(
                    f"  ✏️  {profile_id}: {declared_count} → {actual_count} ({sign}{diff})"
                )

    # Write corrected output only if corrections were made
    if corrections:
        _write_corrected_file(parsed, output_path)

    return corrections


def _write_corrected_file(parsed: ParsedFile, output_path: Path) -> None:
    """
    Write corrected file in the appropriate format.

    Args:
        parsed: ParsedFile object with corrected data
        output_path: Path to output file
    """
    format_type = parsed.format_type

    if format_type == "bmap":
        _write_bmap_format(parsed, output_path)
    elif format_type == "csv":
        _write_csv_format(parsed, output_path)
    else:
        raise ValueError(f"Unsupported format for output: {format_type}")


def _write_bmap_format(parsed: ParsedFile, output_path: Path) -> None:
    """Write corrected BMAP free format file."""
    lines = []

    for profile in parsed.profiles:
        # Write profile header
        header = profile.get("raw_header", "")
        if not header:
            # Reconstruct header from components
            parts = [profile["profile_id"]]
            if profile.get("date"):
                parts.append(profile["date"])
            if profile.get("purpose"):
                parts.append(profile["purpose"])
            header = " ".join(parts)

        lines.append(header + "\n")

        # Write corrected point count
        actual_count = profile["actual_point_count"]
        lines.append(f"{actual_count}\n")

        # Write coordinates
        for coord in profile["coordinates"]:
            x = coord["x"]
            y = coord["y"]
            lines.append(f"{x} {y}\n")

    output_path.write_text("".join(lines), encoding="utf-8")


def _write_csv_format(parsed: ParsedFile, output_path: Path) -> None:
    """Write corrected delimited format file (CSV/TSV/space-delimited)."""
    lines = []

    # Get delimiter from parsed file
    delimiter = parsed.delimiter if hasattr(parsed, "delimiter") else ","

    # Write metadata header if present
    if parsed.metadata.get("header_lines"):
        for header_line in parsed.metadata["header_lines"]:
            lines.append(header_line + "\n")
    # Or write column header if original had one
    elif parsed.has_header and parsed.column_mapping:
        # Reconstruct header from column mapping
        max_idx = max(parsed.column_mapping.values())
        headers = [""] * (max_idx + 1)
        for header, idx in parsed.column_mapping.items():
            # Skip internal mapping keys like PROFILE_ID, X, Y, Z
            if header not in (
                "PROFILE_ID",
                "X",
                "Y",
                "Z",
                "DATE",
                "TIME",
                "POINT_NUM",
                "TYPE",
                "DESCRIPTION",
            ):
                if idx < len(headers):
                    headers[idx] = header
        lines.append(delimiter.join(headers) + "\n")

    # Write data rows preserving all columns
    for profile in parsed.profiles:
        if "all_columns" in profile:
            # Use preserved columns
            for row in profile["all_columns"]:
                lines.append(delimiter.join(row) + "\n")
        else:
            # Reconstruct from coordinates
            for coord in profile["coordinates"]:
                parts = [
                    profile["profile_id"],
                    str(coord["x"]),
                    str(coord["y"]),
                ]
                if "z" in coord:
                    parts.append(str(coord["z"]))
                lines.append(delimiter.join(parts) + "\n")

    output_path.write_text("".join(lines), encoding="utf-8")


def _generate_multi_file_report(all_corrections, no_corrections):
    lines = [
        "=" * 60,
        "BMAP FREE FORMAT FILE POINT COUNT CORRECTION REPORT",
        "=" * 60,
        "",
    ]
    if all_corrections:
        lines.append(f"Files with corrections: {len(all_corrections)}")
        for in_file, (out_file, corrections) in all_corrections.items():
            lines.append("")
            lines.append(f"Input File:  {in_file}")
            lines.append(f"Output File: {out_file}")
            lines.append(f"Profiles Corrected: {len(corrections)}")
            lines.append("Corrections Made:")
            lines.append("-" * 80)
            lines.append(
                f"{'Profile Name':<20} | {'Bad (input) count':>16} | {'Corrected count':>16}"
            )
            lines.append("-" * 80)
            for profile_name, (declared, actual) in sorted(
                corrections.items()
            ):
                lines.append(
                    f"{profile_name:<20} | {declared:>16} | {actual:>16}"
                )
            lines.append("-" * 80)
            lines.append("✅ All corrections applied successfully")
    if no_corrections:
        lines.append("")
        lines.append("Files with no corrections needed:")
        for in_file in no_corrections:
            lines.append(f"- {in_file}")
    lines.append("=" * 60)
    return "\n".join(lines)


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
    parser.add_argument(
        "input_pattern",
        help="Input BMAP file pattern (wildcards allowed, e.g. '*.ASC')",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="Output directory for corrected BMAP files",
    )
    parser.add_argument("--report", help="Optional correction report file")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed correction information",
    )

    parsed_args = parser.parse_args(args)

    # Backup output file if it exists

    input_files = [
        Path(f) for f in sorted(glob.glob(parsed_args.input_pattern))
    ]
    if not input_files:
        print(f"❌ No files matched pattern: {parsed_args.input_pattern}")
        sys.exit(1)

    output_dir = Path(parsed_args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set report path: use specified or default to input directory
    if parsed_args.report:
        report_path = Path(parsed_args.report)
    else:
        input_dir = input_files[0].parent
        report_path = input_dir / "bmap_point_count_fix_report.txt"

    # Backup report file if it exists
    if report_path.exists():
        bak_report_path = report_path.with_suffix(report_path.suffix + ".bak")
        if bak_report_path.exists():
            bak_report_path.unlink()
        report_path.rename(bak_report_path)

    all_corrections = {}
    no_corrections = []
    for in_file in input_files:
        in_path = Path(in_file)
        out_file = in_path.with_name(in_path.stem + "_fix" + in_path.suffix)
        print(
            f"[DEBUG] Checking input file: {in_file} (exists: {in_path.exists()})"
        )
        if not in_path.exists():
            print(f"[ERROR] Input file does not exist: {in_file}")
            continue
        # Backup output file if it exists
        if out_file.exists():
            bak_path = out_file.with_suffix(out_file.suffix + ".bak")
            if bak_path.exists():
                bak_path.unlink()
            out_file.rename(bak_path)
        print(f"🔍 Analyzing {in_file} -> {out_file} ...")
        corrections = fix_bmap_point_counts(
            str(in_path),
            str(out_file),
            verbose=parsed_args.verbose,
            skip_confirmation=True,
        )
        if corrections:
            all_corrections[str(in_file)] = (str(out_file), corrections)
        else:
            no_corrections.append(str(in_file))

    # Write multi-file report if requested
    if report_path:
        report_text = _generate_multi_file_report(
            all_corrections, no_corrections
        )
        report_path.write_text(report_text, encoding="utf-8")
        print(f"\n📄 Report saved to: {report_path}")


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
        "BMAP FREE FORMAT FILE POINT COUNT CORRECTION REPORT",
        "=" * 60,
        f"Input File:  {input_file}",
        f"Output File: {output_file}",
        "",
    ]

    if corrections:
        lines.append(f"Profiles Corrected: {len(corrections)}")
        lines.append("")
        lines.append("Corrections Made:")
        lines.append("-" * 80)
        lines.append(
            f"{'Profile Name':<20} | {'Bad (input) count':>16} | {'Corrected count':>16}"
        )
        lines.append("-" * 80)
        for profile_name, (declared, actual) in sorted(corrections.items()):
            lines.append(f"{profile_name:<20} | {declared:>16} | {actual:>16}")
        lines.append("-" * 80)
        lines.append("")
        lines.append("✅ All corrections applied successfully")
    else:
        lines.append("✅ No corrections needed - all point counts accurate")
        lines.append("")
        lines.append("Files with no corrections needed:")
        lines.append(f"- {input_file}")

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

    verbose_input = (
        input("Show detailed corrections? (y/n) [n]: ").strip().lower()
    )
    verbose = verbose_input == "y"

    report_input = input("Save report to file? (y/n) [n]: ").strip().lower()
    report_file = None
    if report_input == "y":
        report_file = input("Enter report file path: ").strip()

    try:
        print("\n🔄 Analyzing file and fixing point counts...")

        corrections = fix_bmap_point_counts(
            input_file, output_file, verbose=verbose, skip_confirmation=False
        )

        report = _generate_correction_report(
            input_file, output_file, corrections
        )

        if report_file:
            Path(report_file).write_text(report, encoding="utf-8")
            print(f"\n📄 Report saved to: {report_file}")

        print("\n" + report)
        print(f"\n✅ Corrected file written to: {output_file}")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except (OSError, ValueError, TypeError, RuntimeError) as e:
        print(f"\n❌ Unexpected error: {e}")


# Add CLI entrypoint
if __name__ == "__main__":
    execute_from_cli(sys.argv[1:])

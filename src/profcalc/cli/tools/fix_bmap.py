"""Fix BMAP Point Counts

Scan BMAP free-format and compatible delimited files to correct incorrect
point counts written in profile headers. Writes corrected output and an
optional correction report.

Usage examples:
    - CLI: run the fixer with an input pattern and output directory::

            python -m profcalc.cli.tools.fix_bmap "*.ASC" -o corrected_dir

    - Menu: Quick Tools → Fix BMAP Point Counts (invokes :func:`execute_from_menu`).
"""

import argparse
import glob
import sys
from pathlib import Path
from typing import Dict, Tuple

from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.cli.quick_tools.quick_tool_utils import (
    default_output_path,
    timestamped_output_path,
)
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
        log_quick_tool_error(
            "fix_bmap", f"Error parsing file {input_path}: {e}", exc=e
        )
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


def scan_bmap_for_corrections(
    input_file: str, skip_confirmation: bool = False
):
    """Scan a single file and return the parsed object and corrections dict.

    This does not write any output files. Caller may inspect `parsed` and
    use `_write_corrected_file` to write corrected output when ready.
    """
    input_path = Path(input_file)
    # Parse file using centralized parser with format detection
    parsed = parse_file(input_path, skip_confirmation=skip_confirmation)

    corrections: Dict[str, Tuple[int, int]] = {}
    for profile in parsed.profiles:
        profile_id = profile["profile_id"]
        declared_count = profile.get("point_count", 0)
        actual_count = profile["actual_point_count"]
        if declared_count != actual_count:
            corrections[profile_id] = (declared_count, actual_count)

    return parsed, corrections


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
        msg = f"❌ No files matched pattern: {parsed_args.input_pattern}"
        log_quick_tool_error("fix_bmap", msg)
        print(msg)
        sys.exit(1)

    output_dir = Path(parsed_args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set report path: use specified or a default
    if parsed_args.report:
        report_path = Path(parsed_args.report)
    else:
        try:
            report_path = Path(
                default_output_path(
                    "fix_bmap", str(input_files[0]), ext=".txt"
                )
            )
        except (OSError, ValueError, TypeError):
            report_path = (
                input_files[0].parent / "bmap_point_count_fix_report.txt"
            )

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
        try:
            report_path.write_text(report_text, encoding="utf-8")
            print(f"\n📄 Report saved to: {report_path}")
        except (OSError, IOError) as e:
            log_quick_tool_error("fix_bmap", f"Failed to write report: {e}", e)
            print(f"\n❌ Failed to write report: {e}")


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

    while True:
        # Get input file and scan for corrections first
        input_file = input(
            "Enter input BMAP file path (or blank to return): "
        ).strip()
        if not input_file:
            break

        try:
            parsed, corrections = scan_bmap_for_corrections(
                input_file, skip_confirmation=False
            )
        except FileNotFoundError as e:
            log_quick_tool_error(
                "fix_bmap", f"File not found during scan: {e}", exc=e
            )
            print(f"\n❌ Error: {e}")
            continue
        except (OSError, ValueError, TypeError, ImportError) as e:
            log_quick_tool_error(
                "fix_bmap", f"Error parsing file during menu scan: {e}", exc=e
            )
            print(f"\n❌ Error parsing file: {e}")
            continue

        # Display corrections on screen
        print("\n--- Correction Summary ---")
        if corrections:
            for pname, (declared, actual) in sorted(corrections.items()):
                diff = actual - declared
                sign = "+" if diff > 0 else ""
                print(f"  ✏️  {pname}: {declared} → {actual} ({sign}{diff})")
        else:
            print("✅ No point-count corrections needed.")

        # Ask for log file path (default to a timestamped output to avoid overwriting)
        default_log = str(
            Path(timestamped_output_path("fix_bmap", ext=".fix.log"))
        )
        log_choice = input(
            f"Save correction log to file? [Y/{default_log}] (enter 'n' to skip): "
        ).strip()
        report_file = None
        if not log_choice or log_choice.lower() in ("y", "yes"):
            report_file = default_log
        elif log_choice.lower() in ("n", "no"):
            report_file = None
        else:
            report_file = log_choice

        # Ask for output file path (allow overwrite)
        out_prompt = "Enter output file path (leave blank to overwrite the input file): "
        output_file = input(out_prompt).strip()
        if not output_file:
            output_file = input_file

        # Confirm overwrite if output exists and differs from input
        out_path = Path(output_file)
        if out_path.exists() and str(out_path) != str(Path(input_file)):
            ok = (
                input(
                    f"Output file {output_file} exists. Overwrite? (y/n) [n]: "
                )
                .strip()
                .lower()
            )
            if ok not in ("y", "yes"):
                print("Cancelled write. No changes applied.")
                # Ask whether to process another file
                again = (
                    input("Process another file? (y/n) [y]: ").strip().lower()
                )
                if again in ("n", "no"):
                    break
                else:
                    continue

        try:
            # Write corrected file (only writes corrected data if corrections exist)
            if corrections:
                _write_corrected_file(parsed, out_path)
            else:
                # No corrections - write a copy if user requested to write
                write_copy = (
                    input(
                        "No corrections found. Write a copy of the file anyway? (y/n) [n]: "
                    )
                    .strip()
                    .lower()
                )
                if write_copy in ("y", "yes"):
                    _write_corrected_file(parsed, out_path)

            # Generate and save report/log if requested
            report_text = _generate_correction_report(
                input_file, output_file, corrections
            )
            if report_file:
                try:
                    Path(report_file).write_text(report_text, encoding="utf-8")
                    print(f"\n📄 Report saved to: {report_file}")
                except (OSError, IOError) as e:
                    log_quick_tool_error(
                        "fix_bmap", f"Failed to write report file: {e}", e
                    )
                    print(f"\n❌ Failed to write report file: {e}")

            # Print summary to screen
            print("\n" + report_text)
            if corrections:
                print(f"\n✅ Corrected file written to: {output_file}")
            else:
                print("\n✅ No corrections were necessary.")

        except (OSError, ValueError, TypeError, RuntimeError) as e:
            log_quick_tool_error(
                "fix_bmap", f"Unexpected error during fix_bmap menu: {e}"
            )
            print(f"\n❌ Unexpected error: {e}")

        # Ask whether to process another file
        again = input("Process another file? (y/n) [y]: ").strip().lower()
        if again in ("n", "no"):
            break


# Add CLI entrypoint
if __name__ == "__main__":
    execute_from_cli(sys.argv[1:])


def execute_modify_headers_menu() -> None:
    """Interactive tool to inspect and modify profile headers in a BMAP file.

    Prompts the user for a file, lists profiles and their current headers,
    allows editing the header text for selected profiles, and writes the
    modified file to an output path chosen by the user.
    """
    print("\n" + "=" * 60)
    print("MODIFY BMAP PROFILE HEADERS")
    print("=" * 60)

    input_file = input(
        "Enter input BMAP file path (or blank to cancel): "
    ).strip()
    if not input_file:
        print("Cancelled.")
        return

    try:
        parsed = parse_file(Path(input_file), skip_confirmation=False)
    except (OSError, ValueError, TypeError) as e:
        print(f"\n❌ Error parsing file: {e}")
        return

    profiles = parsed.profiles
    if not profiles:
        print("No profiles found in file.")
        return

    print(f"Found {len(profiles)} profiles:")
    for i, p in enumerate(profiles, 1):
        raw_hdr = p.get("raw_header") or p.get("profile_id")
        print(f"  {i}. {p.get('profile_id')}  -> header: {raw_hdr}")

    # Allow editing headers one by one
    for i, p in enumerate(profiles, 1):
        cur = p.get("raw_header") or p.get("profile_id")
        ans = (
            input(f"Edit header for {p.get('profile_id')}? (y/n) [n]: ")
            .strip()
            .lower()
        )
        if ans not in ("y", "yes"):
            continue
        new_hdr = input(f"Enter new header text (current: {cur}): ").strip()
        if new_hdr:
            p["raw_header"] = new_hdr

    out_path = input(
        "Enter output file path (blank to overwrite input): "
    ).strip()
    if not out_path:
        out_path = input_file

    try:
        _write_corrected_file(parsed, Path(out_path))
        print(f"\n✅ Wrote modified file to: {out_path}")
    except (OSError, IOError, ValueError) as e:
        print(f"\n❌ Failed to write modified file: {e}")

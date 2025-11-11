# =============================================================================
# Beach Profile Data Scanner and Discovery Tool
# =============================================================================
#
# FILE: src/profcalc/cli/quick_tools/profile_scanner.py
#
# PURPOSE:
# This module provides intelligent scanning and discovery of beach profile data
# files across filesystem directories. It automatically detects various file
# formats containing profile data, analyzes their contents, and provides tools
# for batch processing and export of discovered datasets.
#
# WHAT IT'S FOR:
# - Recursively scans directories for files containing beach profile data
# - Automatically detects multiple file formats (9-column, BMAP, CSV, etc.)
# - Provides detailed statistics and summaries of discovered data
# - Enables interactive selection and export of profile datasets
# - Supports batch processing of large collections of survey files
# - Offers both programmatic API and interactive menu-driven interface
#
# WORKFLOW POSITION:
# This tool is used in the "Quick Tools" section for data discovery and
# exploration workflows. It's particularly useful when working with large
# collections of survey files or when the exact location and format of data
# files is unknown. It helps users quickly identify and organize profile data
# before detailed analysis.
#
# LIMITATIONS:
# - File scanning can be slow for very large directory structures
# - Format detection relies on heuristics and may have false positives/negatives
# - Memory usage scales with number of discovered profiles
# - Interactive export requires user input for large datasets
# - Some exotic file formats may not be detected
#
# ASSUMPTIONS:
# - Profile data files contain standard X,Z coordinate information
# - File system permissions allow directory traversal and file reading
# - Users have sufficient disk space for temporary processing
# - Interactive mode is appropriate for the use case
# - Discovered files contain valid beach profile data
#
# =============================================================================

import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from profcalc.cli.file_dialogs import select_directory
from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.cli.quick_tools.quick_tool_utils import (
    timestamped_output_path,
    write_tabulate,
)
from profcalc.common.bmap_io import (
    Profile,
    format_date_for_bmap,
    read_bmap_freeformat,
    write_bmap_profiles,
)
from profcalc.common.csv_io import read_csv_profiles, write_csv_profiles
from profcalc.common.error_handler import BeachProfileError
from profcalc.common.ninecol_io import read_9col_profiles

"""Profile scanner quick-tool utilities.

This module provides an interactive quick-tool that scans a filesystem
folder for files that contain beach profile data. It attempts readers in
the following order: 9-col reader, BMAP freeformat reader, CSV-like
reader, and finally a lightweight numeric-heuristic detector. Found
profiles are summarized and can be interactively exported as BMAP or
CSV files.

Key exported functions:
- `scan_folder(folder, recursive=True) -> List[dict]`: non-interactive
    scanner that returns discovered entries and can be used in scripts.
- `scan_folder_with_stats(folder, recursive=True) -> tuple[List[dict], dict]`:
    enhanced scanner that returns both results and detailed statistics.
- `execute_from_menu() -> None`: interactive menu-driven tool used by the
    Quick Tools menu.
"""


def _scan_file_for_profiles(path: Path) -> List[dict]:
    """Scan a single file for profile-like content.

    The function tries multiple readers in order (9-col, BMAP, CSV) and
    returns a list of discovery dictionaries when profiles are found.

    Args:
        path: Path to the file to inspect.

    Returns:
        A list of dicts describing discovered profiles. The dict keys are
        consistent with the interactive tool's expectations (e.g.:
        'profile_id', 'date', 'file', 'parsed', 'point_count', etc.). If
        no profiles are detected an empty list is returned.
    """

    results: List[dict] = []
    # Try 9-col parser first
    try:
        profiles = read_9col_profiles(str(path))
        for p in profiles:
            try:
                pc = len(getattr(p, "x", []))
                xmin = float(min(p.x)) if pc else ""
                xmax = float(max(p.x)) if pc else ""
                zmin = float(min(p.z)) if pc else ""
                zmax = float(max(p.z)) if pc else ""
            except (AttributeError, TypeError, ValueError, IndexError):
                pc = ""
                xmin = xmax = zmin = zmax = ""

            results.append(
                {
                    "profile_id": getattr(p, "name", "") or "",
                    "station": "",
                    "purpose": "",
                    "date": getattr(p, "date", "") or "",
                    "parsed": True,
                    "file": str(path),
                    "point_count": pc,
                    "xmin": xmin,
                    "xmax": xmax,
                    "zmin": zmin,
                    "zmax": zmax,
                }
            )
        if results:
            return results
    except (
        OSError,
        ValueError,
        TypeError,
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        BeachProfileError,
    ) as e:
        log_quick_tool_error("profile_scanner", f"9-col reader failed for {path}: {e}")
        pass

    # Try BMAP parser: prefer the higher-level reader to obtain Profile objects
    try:
        b_profiles = read_bmap_freeformat(str(path))
        if b_profiles:
            for p in b_profiles:
                try:
                    pc = len(getattr(p, "x", []))
                    xmin = float(min(p.x)) if pc else ""
                    xmax = float(max(p.x)) if pc else ""
                    zmin = float(min(p.z)) if pc else ""
                    zmax = float(max(p.z)) if pc else ""
                except (AttributeError, TypeError, ValueError, IndexError):
                    pc = ""
                    xmin = xmax = zmin = zmax = ""

                results.append(
                    {
                        "profile_id": getattr(p, "name", "") or "",
                        "station": "",
                        "purpose": getattr(p, "description", "") or "",
                        "date": getattr(p, "date", "") or "",
                        "parsed": True,
                        "file": str(path),
                        "point_count": pc,
                        "xmin": xmin,
                        "xmax": xmax,
                        "zmin": zmin,
                        "zmax": zmax,
                    }
                )
            if results:
                return results
    except (
        OSError,
        ValueError,
        TypeError,
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        BeachProfileError,
    ) as e:
        log_quick_tool_error("profile_scanner", f"BMAP reader failed for {path}: {e}")
        pass

    # Try CSV-like detection
    try:
        df = pd.read_csv(path, nrows=5)
    except (OSError, ValueError, TypeError, UnicodeDecodeError) as e:
        log_quick_tool_error("profile_scanner", f"CSV detection failed for {path}: {e}")
        return []

    cols = {c.strip().lower(): c for c in df.columns}
    # Candidate column names
    id_keys = ["profile id", "profile", "id", "profile_id"]
    date_keys = ["date", "survey_date"]
    station_keys = ["station", "sta", "station_id"]
    purpose_keys = ["purpose", "purpose_code"]

    found_id = None
    for k in id_keys:
        if k in cols:
            found_id = cols[k]
            break

    # If we don't have a profile id column, skip csv
    if not found_id:
        return []

    # Read full file to gather unique profiles
    try:
        df_full = pd.read_csv(path)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as e:
        log_quick_tool_error("profile_scanner", f"Full CSV read failed for {path}: {e}")
        return []

    for pid, group in df_full.groupby(found_id):
        row = {
            "profile_id": str(pid) if pid is not None else "",
            "station": "",
            "purpose": "",
            "date": "",
            "file": str(path),
        }
        # station
        for k in station_keys:
            if k in cols:
                row["station"] = (
                    str(group.iloc[0][cols[k]])
                    if not pd.isna(group.iloc[0][cols[k]])
                    else ""
                )
                break
        for k in purpose_keys:
            if k in cols:
                row["purpose"] = (
                    str(group.iloc[0][cols[k]])
                    if not pd.isna(group.iloc[0][cols[k]])
                    else ""
                )
                break
        for k in date_keys:
            if k in cols:
                row["date"] = (
                    str(group.iloc[0][cols[k]])
                    if not pd.isna(group.iloc[0][cols[k]])
                    else ""
                )
                break

        results.append(row)

    if results:
        return results

    # If no parser matched, run a lightweight heuristic to detect possible numeric
    # profile-like data. If detected, return a marker so caller can notify user.
    if _detect_possible_profile_content(path):
        return [{"possible": True, "file": str(path)}]

    return []


def _detect_possible_profile_content(path: Path, max_lines: int = 200) -> bool:
    """Lightweight heuristic to detect files that may contain profile-like numeric data.

    Returns True if a majority of inspected lines contain at least two numeric tokens.
    This is a conservative heuristic used only to warn the user about potential data
    when parsing with known readers fails.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = []
            for i, ln in enumerate(fh):
                if i >= max_lines:
                    break
                ln = ln.strip()
                if not ln:
                    continue
                lines.append(ln)
    except (OSError, UnicodeDecodeError) as e:
        log_quick_tool_error(
            "profile_scanner", f"Failed to detect content in {path}: {e}"
        )
        return False

    if not lines:
        return False

    numeric_lines = 0
    total = 0
    for ln in lines:
        total += 1
        parts = ln.split()
        num_count = 0
        for tok in parts:
            try:
                float(tok)
                num_count += 1
            except ValueError:
                # try stripping commas
                try:
                    float(tok.replace(",", ""))
                    num_count += 1
                except ValueError:
                    continue
        if num_count >= 2:
            numeric_lines += 1

    # If at least half of inspected lines have >=2 numeric tokens, flag as possible
    return total >= 5 and (numeric_lines / total) >= 0.5


def scan_folder_with_stats(
    folder: str | Path, recursive: bool = True, file_extensions: List[str] | None = None
) -> tuple[List[dict], dict]:
    """Scan a directory for files that may contain profiles, with detailed statistics.

    This is an enhanced version of scan_folder that also returns comprehensive
    statistics about the scan operation.

    Args:
        folder: Directory to scan (path or string).
        recursive: If True, scan subdirectories recursively.
        file_extensions: List of file extensions to include (e.g., ['.txt', '.csv']).
                        If None, all files are included.

    Returns:
        A tuple of (results, statistics) where:
        - results: List of dicts describing discovered profiles or possible files
        - statistics: Dict with detailed scan statistics
    """

    import time

    start_time = time.time()

    p = Path(folder)
    if not p.exists() or not p.is_dir():
        raise FileNotFoundError(folder)

    entries: List[dict] = []
    stats = {
        "total_files_scanned": 0,
        "files_by_type": {
            "9col": 0,
            "bmap": 0,
            "csv": 0,
            "possible": 0,
            "unreadable": 0,
            "empty_no_profiles": 0,
        },
        "parsing_results": {
            "successful_parses": 0,
            "failed_parses": 0,
            "total_profiles_found": 0,
            "average_profiles_per_file": 0.0,
        },
        "performance": {"scan_duration_seconds": 0.0, "files_per_second": 0.0},
        "file_sizes": {
            "total_size_bytes": 0,
            "average_size_bytes": 0.0,
            "largest_file": {"path": "", "size": 0},
        },
    }

    if recursive:
        all_files = [f for f in p.rglob("*") if f.is_file()]
    else:
        all_files = [f for f in p.iterdir() if f.is_file()]

    # Filter by file extensions if specified
    if file_extensions:
        # Convert to lowercase for case-insensitive matching
        extensions_lower = [ext.lower().lstrip(".") for ext in file_extensions]
        all_files = [
            f for f in all_files if f.suffix.lower().lstrip(".") in extensions_lower
        ]

    stats["total_files_scanned"] = len(all_files)

    for f in all_files:
        try:
            # Track file size
            try:
                file_size = f.stat().st_size
                stats["file_sizes"]["total_size_bytes"] += file_size
                if file_size > stats["file_sizes"]["largest_file"]["size"]:
                    stats["file_sizes"]["largest_file"] = {
                        "path": str(f),
                        "size": file_size,
                    }
            except (OSError, AttributeError):
                pass  # Skip size tracking if unavailable

            found = _scan_file_for_profiles(f)

            if found:
                # Categorize the file type based on the results
                has_parsed = any(r.get("parsed") for r in found)
                has_possible = any(r.get("possible") for r in found)

                if has_parsed:
                    stats["parsing_results"]["successful_parses"] += 1
                    # Try to determine the format by checking the parsing result
                    # This is a heuristic based on the result structure
                    for r in found:
                        if r.get("parsed"):
                            # Check if it has the characteristics of different formats
                            profile_count = len(found)
                            stats["parsing_results"]["total_profiles_found"] += (
                                profile_count
                            )

                            # Heuristic: 9-col files typically have many profiles per file
                            # BMAP files typically have fewer profiles per file
                            # CSV files can vary
                            if profile_count > 5:
                                stats["files_by_type"]["9col"] += 1
                            elif any(
                                "purpose" in str(r.get("purpose", "")) for r in found
                            ):
                                stats["files_by_type"]["bmap"] += 1
                            else:
                                stats["files_by_type"]["csv"] += 1
                            break
                elif has_possible:
                    stats["files_by_type"]["possible"] += 1
                    stats["parsing_results"]["failed_parses"] += 1

                entries.extend(found)
            else:
                stats["files_by_type"]["empty_no_profiles"] += 1
                stats["parsing_results"]["failed_parses"] += 1

        except (OSError, PermissionError) as e:
            stats["files_by_type"]["unreadable"] += 1
            log_quick_tool_error("profile_scanner", f"Skipped unreadable file {f}: {e}")
            continue

    # Calculate derived statistics
    end_time = time.time()
    duration = end_time - start_time
    stats["performance"]["scan_duration_seconds"] = duration
    if duration > 0:
        stats["performance"]["files_per_second"] = (
            stats["total_files_scanned"] / duration
        )

    if stats["total_files_scanned"] > 0:
        stats["file_sizes"]["average_size_bytes"] = (
            stats["file_sizes"]["total_size_bytes"] / stats["total_files_scanned"]
        )

    successful_files = stats["parsing_results"]["successful_parses"]
    if successful_files > 0:
        stats["parsing_results"]["average_profiles_per_file"] = (
            stats["parsing_results"]["total_profiles_found"] / successful_files
        )

    # Detect duplicate profiles
    duplicate_stats = _detect_duplicate_profiles(entries)
    stats["duplicates"] = duplicate_stats

    return entries, stats


def _detect_duplicate_profiles(entries: List[dict]) -> dict:
    """Detect duplicate profiles based on profile data.

    Args:
        entries: List of profile entries from scanning

    Returns:
        Dictionary with duplicate statistics
    """
    from collections import defaultdict

    # Only consider parsed profiles for duplicate detection
    parsed_entries = [e for e in entries if e.get("parsed", False)]

    # Group profiles by a signature based on key data
    profile_groups = defaultdict(list)

    for entry in parsed_entries:
        # Create a signature based on profile_id, coordinate bounds, and point count
        profile_id = entry.get("profile_id", "").strip()
        xmin = entry.get("xmin", "")
        xmax = entry.get("xmax", "")
        zmin = entry.get("zmin", "")
        zmax = entry.get("zmax", "")
        point_count = entry.get("point_count", "")

        # Create signature - use profile_id if available, otherwise use coordinate bounds
        if profile_id:
            signature = f"{profile_id}|{xmin}|{xmax}|{zmin}|{zmax}|{point_count}"
        else:
            # For profiles without IDs, use coordinate bounds as signature
            signature = f"no_id|{xmin}|{xmax}|{zmin}|{zmax}|{point_count}"

        profile_groups[signature].append(entry)

    # Find duplicate groups (more than one profile with same signature)
    duplicate_groups = []
    total_duplicate_profiles = 0

    for signature, group in profile_groups.items():
        if len(group) > 1:
            duplicate_groups.append(
                {
                    "signature": signature,
                    "count": len(group),
                    "files": [entry.get("file", "") for entry in group],
                    "profile_ids": [entry.get("profile_id", "") for entry in group],
                }
            )
            total_duplicate_profiles += len(group)

    return {
        "duplicate_groups_found": len(duplicate_groups),
        "total_duplicate_profiles": total_duplicate_profiles,
        "unique_profiles": len(parsed_entries)
        - total_duplicate_profiles
        + len(duplicate_groups),
        "duplicate_groups": duplicate_groups,
    }


def _interactive_filter_profiles(entries: List[dict], out_dir: Path) -> List[dict]:
    """Interactive filtering of profile results.

    Args:
        entries: List of parsed profile entries
        out_dir: Output directory for any generated files

    Returns:
        Filtered list of entries
    """
    if not entries:
        return entries

    print(f"\nFound {len(entries)} profiles. Would you like to filter the results?")
    print("Available filters:")
    print(
        "  id:<pattern>     - Filter by profile ID (supports wildcards: MA*, *001, etc.)"
    )
    print("  date:<start-end> - Filter by date range (YYYY-MM-DD format)")
    print("  points:<min-max> - Filter by point count range")
    print("  file:<pattern>   - Filter by filename pattern")
    print("  clear            - Clear all filters")
    print("  show             - Show current results")
    print("  done             - Finish filtering")
    print("\nExamples:")
    print("  id:MA*           - Show only profiles starting with 'MA'")
    print("  date:2023-01-01-2023-12-31 - Show profiles from 2023")
    print("  points:10-100    - Show profiles with 10-100 points")
    print("  file:*.csv       - Show only profiles from CSV files")

    filtered_entries = entries.copy()
    active_filters = []

    while True:
        print(f"\nCurrent results: {len(filtered_entries)} profiles")
        if active_filters:
            print(f"Active filters: {', '.join(active_filters)}")

        choice = input("\nEnter filter (or 'done' to continue): ").strip()

        if not choice or choice.lower() == "done":
            break
        elif choice.lower() == "clear":
            filtered_entries = entries.copy()
            active_filters = []
            print("All filters cleared.")
        elif choice.lower() == "show":
            if filtered_entries:
                print("\nCurrent filtered results (first 10):")
                for i, entry in enumerate(filtered_entries[:10], 1):
                    pid = entry.get("profile_id", "no ID")
                    file_name = Path(entry.get("file", "")).name
                    points = entry.get("point_count", "unknown")
                    print(f"  {i}. {pid} ({points} points) - {file_name}")
                if len(filtered_entries) > 10:
                    print(f"  ... and {len(filtered_entries) - 10} more")
            else:
                print("No profiles match current filters.")
        elif choice.startswith("id:"):
            pattern = choice[3:].strip()
            if pattern:
                import fnmatch

                filtered_entries = [
                    e
                    for e in filtered_entries
                    if fnmatch.fnmatch(e.get("profile_id", ""), pattern)
                ]
                active_filters.append(f"id:{pattern}")
                print(f"Applied ID filter: {pattern}")
            else:
                print("Invalid ID pattern.")
        elif choice.startswith("date:"):
            date_range = choice[5:].strip()
            if "-" in date_range:
                try:
                    start_str, end_str = date_range.split("-", 1)
                    start_date = (
                        pd.to_datetime(start_str.strip()) if start_str.strip() else None
                    )
                    end_date = (
                        pd.to_datetime(end_str.strip()) if end_str.strip() else None
                    )

                    def date_in_range(entry: Dict[str, Any]) -> bool:
                        date_str = entry.get("date", "")
                        if not date_str:
                            return False
                        try:
                            entry_date = pd.to_datetime(date_str)
                            if start_date and entry_date < start_date:
                                return False
                            if end_date and entry_date > end_date:
                                return False
                            return True
                        except (ValueError, TypeError):
                            return False

                    filtered_entries = [e for e in filtered_entries if date_in_range(e)]
                    active_filters.append(f"date:{date_range}")
                    print(f"Applied date filter: {date_range}")
                except (ValueError, TypeError) as e:
                    print(
                        f"Invalid date range format. Use YYYY-MM-DD-YYYY-MM-DD. Error: {e}"
                    )
            else:
                print("Invalid date range. Use format: date:start_date-end_date")
        elif choice.startswith("points:"):
            range_str = choice[7:].strip()
            if "-" in range_str:
                try:
                    min_str, max_str = range_str.split("-", 1)
                    min_points = int(min_str.strip()) if min_str.strip() else None
                    max_points = int(max_str.strip()) if max_str.strip() else None

                    def points_in_range(entry: Dict[str, Any]) -> bool:
                        points = entry.get("point_count", 0)
                        if min_points is not None and points < min_points:
                            return False
                        if max_points is not None and points > max_points:
                            return False
                        return True

                    filtered_entries = [
                        e for e in filtered_entries if points_in_range(e)
                    ]
                    active_filters.append(f"points:{range_str}")
                    print(f"Applied point count filter: {range_str}")
                except (ValueError, TypeError) as e:
                    print(
                        f"Invalid point range. Use format: points:min-max. Error: {e}"
                    )
            else:
                print("Invalid point range. Use format: points:min-max")
        elif choice.startswith("file:"):
            pattern = choice[5:].strip()
            if pattern:
                import fnmatch

                filtered_entries = [
                    e
                    for e in filtered_entries
                    if fnmatch.fnmatch(Path(e.get("file", "")).name, pattern)
                ]
                active_filters.append(f"file:{pattern}")
                print(f"Applied filename filter: {pattern}")
            else:
                print("Invalid filename pattern.")
        else:
            print(
                "Unknown filter. Type 'done' to continue or see available filters above."
            )

    if len(filtered_entries) != len(entries):
        print(
            f"\nFiltering complete. Showing {len(filtered_entries)} of {len(entries)} profiles."
        )
    else:
        print(
            f"\nNo filtering applied. Proceeding with all {len(filtered_entries)} profiles."
        )

    return filtered_entries


def scan_folder(folder: str | Path, recursive: bool = True) -> List[dict]:
    """Scan a directory for files that may contain profiles.

    This is the non-interactive API intended for scripts. It returns a
    list of discovery dictionaries for every file that contains parsed
    profiles or is heuristically identified as possibly containing
    profile-like numeric data.

    Args:
        folder: Directory to scan (path or string).
        recursive: If True, scan subdirectories recursively.

    Returns:
        A list of dicts describing discovered profiles or possible files.
    """
    results, _ = scan_folder_with_stats(folder, recursive)
    return results


def execute_from_menu() -> None:
    """Interactive quick-tool: prompt for a folder, show results and export.

    This function drives the full interactive workflow: scanning, optional
    project/year filtering, interactive selection (paged REPL), and export
    of selected profiles to BMAP or CSV. It performs all IO via stdin/stdout
    and is intentionally interactive.
    """

    folder = select_directory("Select folder to scan for profiles")
    if not folder:
        print("Cancelled.")
        return
    rec = input("Scan subfolders recursively? (Y/n) [Y]: ").strip().lower()
    recursive = rec != "n"

    # Prompt for file extensions to filter by
    ext_input = input(
        "File extensions to scan (comma-separated, e.g. txt,csv,xlsx) [all]: "
    ).strip()
    file_extensions = None
    if ext_input:
        # Parse comma-separated extensions, strip whitespace and dots
        file_extensions = [
            ext.strip().lstrip(".") for ext in ext_input.split(",") if ext.strip()
        ]

    try:
        results, stats = scan_folder_with_stats(
            folder, recursive=recursive, file_extensions=file_extensions
        )
    except FileNotFoundError as e:
        print(f"Folder not found: {e}")
        log_quick_tool_error("profile_scanner", f"Folder scan failed: {e}")
        return

    if not results:
        print("No profiles found in the specified folder.")
        return

    # Display enhanced statistics
    print("\n" + "=" * 60)
    print("SCAN STATISTICS")
    print("=" * 60)
    if file_extensions:
        print(f"File extensions filtered: {', '.join(file_extensions)}")
    print(f"Total files scanned: {stats['total_files_scanned']}")
    print(f"Scan duration: {stats['performance']['scan_duration_seconds']:.2f} seconds")
    print(f"Files per second: {stats['performance']['files_per_second']:.1f}")

    print("\nFile types found:")
    for file_type, count in stats["files_by_type"].items():
        if count > 0:
            print(f"  {file_type}: {count}")

    print("\nParsing results:")
    print(f"  Successful parses: {stats['parsing_results']['successful_parses']}")
    print(f"  Failed parses: {stats['parsing_results']['failed_parses']}")
    print(f"  Total profiles found: {stats['parsing_results']['total_profiles_found']}")
    if stats["parsing_results"]["successful_parses"] > 0:
        print(
            f"  Average profiles per file: {stats['parsing_results']['average_profiles_per_file']:.1f}"
        )

    if stats["file_sizes"]["total_size_bytes"] > 0:
        total_mb = stats["file_sizes"]["total_size_bytes"] / (1024 * 1024)
        avg_kb = stats["file_sizes"]["average_size_bytes"] / 1024
        print("\nFile sizes:")
        print(f"  Total size: {total_mb:.1f} MB")
        print(f"  Average size: {avg_kb:.1f} KB")

    # Separate parsed profiles from possible files
    parsed_entries = [r for r in results if not r.get("possible", False)]
    possible_files = [r for r in results if r.get("possible", False)]

    if possible_files:
        print(f"\nPossible unparsed files: {len(possible_files)}")
        print(
            "These files contain numeric data that may be profiles but couldn't be parsed."
        )
        print("You can inspect them manually or use other tools.")

        # Continue with the rest of the interactive logic...
        print("Cancelled.")
        return
    rec = input("Scan subfolders recursively? (Y/n) [Y]: ").strip().lower()
    recursive = rec != "n"

    # Prompt for file extensions to filter by
    ext_input = input(
        "File extensions to scan (comma-separated, e.g. txt,csv,xlsx) [all]: "
    ).strip()
    file_extensions = None
    if ext_input:
        # Parse comma-separated extensions, strip whitespace and dots
        file_extensions = [
            ext.strip().lstrip(".") for ext in ext_input.split(",") if ext.strip()
        ]

    try:
        results, stats = scan_folder_with_stats(
            folder, recursive=recursive, file_extensions=file_extensions
        )
    except FileNotFoundError as e:
        print(f"Folder not found: {e}")
        log_quick_tool_error("profile_scanner", f"Folder scan failed: {e}")
        return

    if not results:
        print("No profiles found in the specified folder.")
        return

    # Display enhanced statistics
    print("\n" + "=" * 60)
    print("SCAN STATISTICS")
    print("=" * 60)
    if file_extensions:
        print(f"File extensions filtered: {', '.join(file_extensions)}")
    print(f"Total files scanned: {stats['total_files_scanned']}")
    print(f"Scan duration: {stats['performance']['scan_duration_seconds']:.2f} seconds")
    print(f"Files per second: {stats['performance']['files_per_second']:.1f}")

    print("\nFile types found:")
    for file_type, count in stats["files_by_type"].items():
        if count > 0:
            print(f"  {file_type}: {count}")

    print("\nParsing results:")
    print(f"  Successful parses: {stats['parsing_results']['successful_parses']}")
    print(f"  Failed parses: {stats['parsing_results']['failed_parses']}")
    print(f"  Total profiles found: {stats['parsing_results']['total_profiles_found']}")
    if stats["parsing_results"]["successful_parses"] > 0:
        print(
            f"  Average profiles per file: {stats['parsing_results']['average_profiles_per_file']:.1f}"
        )

    if stats["file_sizes"]["total_size_bytes"] > 0:
        total_mb = stats["file_sizes"]["total_size_bytes"] / (1024 * 1024)
        avg_kb = stats["file_sizes"]["average_size_bytes"] / 1024
        print("\nFile sizes:")
        print(f"  Total size: {total_mb:.1f} MB")
        print(f"  Average size: {avg_kb:.1f} KB")
        if stats["file_sizes"]["largest_file"]["path"]:
            largest_mb = stats["file_sizes"]["largest_file"]["size"] / (1024 * 1024)
            print(
                f"  Largest file: {largest_mb:.1f} MB ({Path(stats['file_sizes']['largest_file']['path']).name})"
            )

    # Display duplicate information
    if stats["duplicates"]["duplicate_groups_found"] > 0:
        print("\nDuplicate detection:")
        print(
            f"  Duplicate groups found: {stats['duplicates']['duplicate_groups_found']}"
        )
        print(
            f"  Total duplicate profiles: {stats['duplicates']['total_duplicate_profiles']}"
        )
        print(f"  Unique profiles: {stats['duplicates']['unique_profiles']}")

        # Show details of duplicate groups (limit to first few for brevity)
        print("\n  Top duplicate groups:")
        for i, group in enumerate(stats["duplicates"]["duplicate_groups"][:5], 1):
            profile_ids = [pid for pid in group["profile_ids"] if pid]
            id_display = profile_ids[0] if profile_ids else "no ID"
            files_display = len(set(group["files"]))
            print(
                f"    {i}. {id_display} ({group['count']} copies in {files_display} files)"
            )
        if len(stats["duplicates"]["duplicate_groups"]) > 5:
            print(
                f"    ... and {len(stats['duplicates']['duplicate_groups']) - 5} more groups"
            )

    success_rate = 0.0
    if stats["total_files_scanned"] > 0:
        success_rate = (
            stats["parsing_results"]["successful_parses"] / stats["total_files_scanned"]
        ) * 100
    print(f"\nSuccess rate: {success_rate:.1f}% of files contained parseable profiles")
    print("=" * 60 + "\n")

    # Determine output directory for any generated files. Use the scanned
    # folder so outputs are colocated with input data (user request).
    try:
        out_dir = Path(folder).resolve()
    except (OSError, RuntimeError) as e:
        log_quick_tool_error(
            "profile_scanner", f"Failed to resolve output directory for {folder}: {e}"
        )
        out_dir = Path.cwd()

    # Separate parsed entries (to show in the summary table) and possible-but-unparsed files
    parsed_entries = [r for r in results if r.get("parsed")]
    possible_files = [r for r in results if r.get("possible")]

    # Offer interactive search/filtering of results
    parsed_entries = _interactive_filter_profiles(parsed_entries, out_dir)

    # Attempt to load the canonical profile->project mapping from the
    # beach_profile_network.csv file (kept under data/required_inputs).
    # If present, annotate parsed entries with a 'project' key and offer
    # an interactive filter by project to reduce large result sets.
    try:
        net_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "required_inputs"
            / "beach_profile_network.csv"
        )
        profile_project_map = {}
        if net_path.exists():
            try:
                df_net = pd.read_csv(net_path, dtype=str)
                # find likely column names
                cols_lower = {c.strip().lower(): c for c in df_net.columns}
                profile_col = None
                project_col = None
                for k in ["profile_name", "profile", "profile_id", "profile_name"]:
                    if k in cols_lower:
                        profile_col = cols_lower[k]
                        break
                for k in ["project", "project_name"]:
                    if k in cols_lower:
                        project_col = cols_lower[k]
                        break
                if profile_col and project_col:
                    for _, row in df_net.iterrows():
                        pid = str(row.get(profile_col, "")).strip()
                        proj = str(row.get(project_col, "")).strip()
                        if pid:
                            profile_project_map[pid] = proj
            except (
                OSError,
                pd.errors.EmptyDataError,
                pd.errors.ParserError,
                ValueError,
            ) as e:
                log_quick_tool_error(
                    "profile_scanner",
                    f"Failed to load project mapping from {net_path}: {e}",
                )
                profile_project_map = {}
        else:
            profile_project_map = {}
    except (OSError, ValueError) as e:
        log_quick_tool_error(
            "profile_scanner", f"Error accessing project mapping file: {e}"
        )
        profile_project_map = {}

    # Annotate parsed entries with the project when available
    if profile_project_map:
        for r in parsed_entries:
            pid = r.get("profile_id")
            r["project"] = profile_project_map.get(str(pid), "")
    else:
        for r in parsed_entries:
            r["project"] = ""

    # If mapping provided and there are multiple projects, offer an interactive
    # filter so users can narrow large scans to a single project before saving.
    try:
        projects_in_results = {}
        for r in parsed_entries:
            p = r.get("project") or "(unknown)"
            projects_in_results.setdefault(p, 0)
            projects_in_results[p] += 1
        if profile_project_map and len(projects_in_results) > 1:
            print("\nProjects found in scan:")
            proj_list = [p for p in sorted(projects_in_results.keys())]
            for i, p in enumerate(proj_list, start=1):
                print(f"{i}: {p} ({projects_in_results.get(p)})")
            sel = input(
                "Filter results to a project? Enter numbers (e.g. 1) or blank to keep all: "
            ).strip()
            if sel:
                sel_parts = [s.strip() for s in sel.split(",") if s.strip()]
                chosen = set()
                for part in sel_parts:
                    try:
                        idx = int(part)
                        if 1 <= idx <= len(proj_list):
                            chosen.add(proj_list[idx - 1])
                    except (ValueError, TypeError):
                        # allow matching by exact project name as fallback
                        if part in proj_list:
                            chosen.add(part)
                if chosen:
                    parsed_entries = [
                        r for r in parsed_entries if (r.get("project") in chosen)
                    ]

            # After project filtering, offer an optional year-based date filter.
            try:
                # Extract year (4-digit) where possible from the parsed 'date' field.
                for r in parsed_entries:
                    r_year = None
                    dstr = (r.get("date") or "").strip()
                    if dstr:
                        # look for a 4-digit year first
                        m = re.search(r"(\d{4})", dstr)
                        if m:
                            try:
                                r_year = int(m.group(1))
                            except (ValueError, TypeError):
                                r_year = None
                        else:
                            # fallback: try pandas to_datetime to parse dates like 01/02/2018
                            try:
                                dt = pd.to_datetime(dstr, errors="coerce")
                                if not pd.isna(dt):
                                    r_year = int(dt.year)
                            except (ValueError, TypeError):
                                r_year = None
                    r["year"] = r_year

                years = sorted({r["year"] for r in parsed_entries if r.get("year")})
                if years and sys.stdin.isatty():
                    print(
                        f"\nDetected survey years in results: {years[0]} - {years[-1]} (sample of years present)"
                    )
                    want = input("Filter results by year? (y/N): ").strip().lower()
                    if want == "y":
                        print(
                            "Enter a year range (e.g. 2010-2020), a single year (e.g. 2018), or 'back N' to include surveys from the last N years (e.g. back 5)."
                        )
                        yr_input = input("Year filter: ").strip().lower()
                        if yr_input:
                            min_year = None
                            max_year = None
                            if yr_input.startswith("back"):
                                try:
                                    parts = yr_input.split()
                                    n = (
                                        int(parts[1])
                                        if len(parts) > 1
                                        else int(re.sub(r"[^0-9]", "", yr_input))
                                    )
                                    now = datetime.now()
                                    max_year = now.year
                                    min_year = now.year - n
                                except (ValueError, TypeError):
                                    min_year = None
                                    max_year = None
                            elif "-" in yr_input:
                                try:
                                    a, b = yr_input.split("-", 1)
                                    min_year = int(a)
                                    max_year = int(b)
                                except (ValueError, TypeError):
                                    min_year = None
                                    max_year = None
                            else:
                                try:
                                    y = int(re.sub(r"[^0-9]", "", yr_input))
                                    min_year = max_year = y
                                except (ValueError, TypeError):
                                    min_year = None
                                    max_year = None

                            if min_year is not None and max_year is not None:
                                before_count = len(parsed_entries)
                                parsed_entries = [
                                    r
                                    for r in parsed_entries
                                    if (
                                        r.get("year") is not None
                                        and min_year <= r.get("year") <= max_year
                                    )
                                ]
                                after_count = len(parsed_entries)
                                print(
                                    f"Filtered by year: {min_year}-{max_year}. Entries reduced {before_count} -> {after_count}."
                                )
                                if not parsed_entries:
                                    print(
                                        "No entries match the selected year range. Continuing with no date filtering."
                                    )
                                    # nothing to restore here; just continue
                # remove temporary 'year' keys
                for r in parsed_entries:
                    r.pop("year", None)
            except (ValueError, TypeError, OSError) as e:
                # non-fatal; continue without date filtering
                log_quick_tool_error("profile_scanner", f"Date filtering failed: {e}")
                for r in parsed_entries:
                    r.pop("year", None)
    except (ValueError, TypeError, OSError) as e:
        # Non-fatal: if anything goes wrong with filtering, continue without it
        log_quick_tool_error("profile_scanner", f"Project/year filtering failed: {e}")
        pass

    if not parsed_entries and not possible_files:
        print("No profiles found in the specified folder.")
        return

    # Print summary table for parsed entries only
    headers = ["Profile ID", "Station", "Purpose", "Date", "File"]
    rows: List[List[str]] = []
    for r in parsed_entries:
        rows.append(
            [
                r.get("profile_id", ""),
                r.get("station", ""),
                r.get("purpose", ""),
                r.get("date", ""),
                r.get("file", ""),
            ]
        )

    if rows:
        # Try to use tabulate to produce a pretty table and save it to a
        # timestamped file located in the scanned folder.
        out_filename = str(
            out_dir / Path(timestamped_output_path("profile_scanner", ext=".txt"))
        )
        saved_text = write_tabulate(out_filename, headers, rows)
        if saved_text:
            # tabulate available: print the pretty text and inform user where it was saved
            print(saved_text)
            # Append possible-unparsed file notes as footnotes, if any
            if possible_files:
                try:
                    with open(out_filename, "a", encoding="utf-8") as ftxt:
                        ftxt.write("\n\nPossible unparsed files (inspect manually):\n")
                        for pf in possible_files:
                            ftxt.write(f" - {pf.get('file')}\n")
                except (OSError, IOError) as e:
                    log_quick_tool_error(
                        "profile_scanner",
                        f"Failed to append possible files to {out_filename}: {e}",
                    )
                    pass
            print(f"\nSummary table saved to: {out_filename}")
        else:
            # Fallback to simple column formatting
            widths = [
                max(len(str(h)), max((len(str(row[i])) for row in rows), default=0))
                for i, h in enumerate(headers)
            ]
            fmt = "  ".join(f"{{:<{w}}}" for w in widths)
            print(fmt.format(*headers))
            print("-" * (sum(widths) + 2 * (len(widths) - 1)))
            for row in rows:
                print(fmt.format(*row))
            # Also write the fallback plain text table to the timestamped file for consistency
            try:
                with open(out_filename, "w", encoding="utf-8") as fout:
                    fout.write("\t".join(headers) + "\n")
                    for row in rows:
                        fout.write("\t".join(str(x) for x in row) + "\n")
                    if possible_files:
                        fout.write("\nPossible unparsed files (inspect manually):\n")
                        for pf in possible_files:
                            fout.write(f" - {pf.get('file')}\n")
                print(f"\nSummary table saved to: {out_filename}")
            except (OSError, IOError) as e:
                log_quick_tool_error(
                    "profile_scanner",
                    f"Failed to write summary table to {out_filename}: {e}",
                )
                pass
    else:
        print("No parsed profiles were found.")

    # Notify about possible unparsed files (do NOT include them in the table)
    if possible_files:
        print(
            "\nNote: the following files may contain profile-like data but could not be parsed. Please inspect them manually:"
        )
        for pf in possible_files:
            print(f" - {pf.get('file')}")

    # If there are no parsed entries, but there are possible files, save a note file for the user
    if not parsed_entries:
        if possible_files:
            out_filename = str(
                out_dir / Path(timestamped_output_path("profile_scanner", ext=".txt"))
            )
            try:
                with open(out_filename, "w", encoding="utf-8") as fout:
                    fout.write("Possible unparsed files detected:\n")
                    for pf in possible_files:
                        fout.write(f" - {pf.get('file')}\n")
                print(
                    f"\nNote: possible profile-containing files were saved to: {out_filename}"
                )
            except (OSError, IOError) as e:
                log_quick_tool_error(
                    "profile_scanner",
                    f"Failed to write possible files note to {out_filename}: {e}",
                )
                pass
        return

    # Prompt user to save any of the parsed profiles
    save_prompt = (
        input("\nSave any of these profiles to a file? (y/N): ").strip().lower()
    )
    if save_prompt != "y":
        return

    # Selection and paging configuration
    PAGE_SIZE = 20
    SHOW_INLINE_LIMIT = 30
    SUGGEST_FILTER_THRESHOLD = 100
    HARD_DISPLAY_LIMIT = 500
    LARGE_SELECTION_CONFIRM = 50

    # Helper: parse numeric selection strings (1-based indices, ranges)
    def parse_selection(s: str, max_idx: int) -> List[int]:
        parts = [p.strip() for p in s.split(",") if p.strip()]
        picks: List[int] = []
        for part in parts:
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    a_i = int(a)
                    b_i = int(b)
                    if a_i <= 0 or b_i <= 0:
                        continue
                    for v in range(min(a_i, b_i), max(a_i, b_i) + 1):
                        if 1 <= v <= max_idx:
                            picks.append(v - 1)
                except (ValueError, TypeError):
                    continue
            else:
                try:
                    v = int(part)
                    if 1 <= v <= max_idx:
                        picks.append(v - 1)
                except (ValueError, TypeError):
                    continue
        # unique and preserve order
        seen = set()
        out: List[int] = []
        for idx in picks:
            if idx not in seen:
                seen.add(idx)
                out.append(idx)
        return out

    # If results are huge, encourage filtering or export
    total_results = len(parsed_entries)
    if total_results > HARD_DISPLAY_LIMIT:
        print(f"\nVery large result set ({total_results} entries).")
        choice = (
            input(
                "Apply additional filters (f), export results to CSV (e), or cancel (c)? [f/e/c]: "
            )
            .strip()
            .lower()
        )
        if choice == "e":
            # export current parsed_entries to timestamped CSV in the scanned folder
            try:
                out_csv = str(
                    out_dir
                    / Path(
                        timestamped_output_path(
                            "profile_scanner_full_results", ext=".csv"
                        )
                    )
                )
                df_out = pd.DataFrame(parsed_entries)
                df_out.to_csv(out_csv, index=False)
                print(f"Exported {len(parsed_entries)} entries to: {out_csv}")
            except (OSError, IOError, pd.errors.ParserError) as e:
                print(f"Failed to export results: {e}")
                log_quick_tool_error("profile_scanner", f"Export failed: {e}")
            return
        if choice == "c":
            print("Aborting save due to large result set. Please re-run with filters.")
            return

    # If results are large but not huge, suggest filtering
    if total_results > SUGGEST_FILTER_THRESHOLD:
        print(
            f"\nLarge result set ({total_results} entries). Consider filtering before selecting."
        )
        cont = (
            input("Continue to interactive selector (c) or filter now (f)? [f/c]: ")
            .strip()
            .lower()
            or "f"
        )
        if cont == "f":
            # user can rely on project-based filter shown earlier or use REPL filter below; continue into REPL
            pass

    # If small enough, show simple numbered list and accept inline selection
    if total_results <= SHOW_INLINE_LIMIT:
        print("\nFound profiles:")
        for i, r in enumerate(parsed_entries, start=1):
            proj = r.get("project", "")
            print(
                f"{i}: {r.get('profile_id', '')} {('[' + proj + ']') if proj else ''} ({r.get('file', '')})"
            )
        selection = input("Enter profile numbers to save (e.g. 1,3-5): ").strip()
        if not selection:
            print("No selection made. Aborting save.")
            return
        indices = parse_selection(selection, len(parsed_entries))
        if not indices:
            print("No valid selections found. Aborting save.")
            return
    else:
        # Enter interactive paged REPL for medium/large result sets
        entries_master = list(parsed_entries)
        entries_view = list(entries_master)
        selection_set = set()
        page = 0

        def display_page(page_idx: int) -> None:
            start = page_idx * PAGE_SIZE
            end = min(len(entries_view), start + PAGE_SIZE)
            print(
                f"\nShowing {start + 1}-{end} of {len(entries_view)} (page {page_idx + 1})"
            )
            print(" idx  sel  Profile ID [Project]  File")
            print("---- ---- --------------------  ----")
            for i in range(start, end):
                r = entries_view[i]
                sel = "*" if i in selection_set else " "
                proj = r.get("project", "")
                fid = r.get("file", "")
                print(
                    f"{i + 1:4d}  {sel:3s}  {r.get('profile_id', '')[:25]:25s} {('[' + proj + ']') if proj else '':20s} {fid}"
                )
            print(
                "\nCommands: n(next) p(prev) g<num> goto, f <term> filter, r reset filter, m <nums> mark, u <nums> unmark, a mark all, c clear marks, e export csv, d done, q cancel, h help"
            )

        # REPL loop
        while True:
            display_page(page)
            cmd = input("cmd> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("n", "next"):
                if (page + 1) * PAGE_SIZE < len(entries_view):
                    page += 1
                else:
                    print("Already at last page.")
                continue
            if cmd.lower() in ("p", "prev"):
                if page > 0:
                    page -= 1
                else:
                    print("Already at first page.")
                continue
            if cmd.lower().startswith("g"):
                try:
                    val = int(cmd[1:].strip())
                    if val >= 1 and (val - 1) * PAGE_SIZE < len(entries_view):
                        page = val - 1
                    else:
                        print("Invalid page number.")
                except (ValueError, TypeError):
                    print("Usage: g<page_number>")
                continue
            if cmd.lower().startswith("f "):
                term = cmd[2:].strip().lower()
                if term:
                    entries_view = [
                        r
                        for r in entries_master
                        if term
                        in (
                            str(r.get("profile_id", "")).lower()
                            + " "
                            + str(r.get("project", "")).lower()
                            + " "
                            + str(r.get("file", "")).lower()
                        )
                    ]
                    selection_set.clear()
                    page = 0
                continue
            if cmd.lower() == "r":
                entries_view = list(entries_master)
                selection_set.clear()
                page = 0
                continue
            if cmd.lower().startswith("m "):
                numpart = cmd[2:].strip()
                picked = parse_selection(numpart, len(entries_view))
                for p in picked:
                    selection_set.add(p)
                print(
                    f"Marked {len(picked)} entries (total marked: {len(selection_set)})"
                )
                continue
            if cmd.lower().startswith("u "):
                numpart = cmd[2:].strip()
                picked = parse_selection(numpart, len(entries_view))
                for p in picked:
                    selection_set.discard(p)
                print(
                    f"Unmarked {len(picked)} entries (total marked: {len(selection_set)})"
                )
                continue
            if cmd.lower() == "a":
                selection_set = set(range(len(entries_view)))
                print(f"Marked all ({len(selection_set)}) entries")
                continue
            if cmd.lower() == "c":
                selection_set.clear()
                print("Cleared all marks")
                continue
            if cmd.lower() == "e":
                try:
                    out_csv = str(
                        out_dir
                        / Path(
                            timestamped_output_path(
                                "profile_scanner_export", ext=".csv"
                            )
                        )
                    )
                    pd.DataFrame(entries_view).to_csv(out_csv, index=False)
                    print(f"Exported {len(entries_view)} entries to: {out_csv}")
                except (OSError, IOError, pd.errors.ParserError) as e:
                    print(f"Failed to export: {e}")
                    log_quick_tool_error("profile_scanner", f"REPL export failed: {e}")
                continue
            if cmd.lower() in ("d", "done"):
                if not selection_set:
                    yn = (
                        input(
                            "No profiles marked. Use all current filtered entries? (y/N): "
                        )
                        .strip()
                        .lower()
                    )
                    if yn != "y":
                        continue
                    indices = list(range(len(entries_view)))
                else:
                    indices = sorted(selection_set)
                # map indices back to global parsed_entries indices
                # We will set parsed_entries to entries_view for subsequent save logic
                parsed_entries = list(entries_view)
                indices = [int(i) for i in indices]
                # Confirm large selections
                if len(indices) >= LARGE_SELECTION_CONFIRM:
                    ok = (
                        input(
                            f"You selected {len(indices)} profiles. Continue? (y/N): "
                        )
                        .strip()
                        .lower()
                    )
                    if ok != "y":
                        continue
                break
            if cmd.lower() in ("q", "cancel"):
                print("Selection cancelled. Aborting save.")
                return
            if cmd.lower() in ("h", "help"):
                print(
                    "Commands: n,p,g<num>, f <term>, r, m <nums>, u <nums>, a, c, e, d (done), q (cancel)"
                )
                continue
            print("Unknown command. Type 'h' for help.")

    indices = parse_selection(selection, len(parsed_entries))
    if not indices:
        print("No valid selections found. Aborting save.")
        return

    # Helper to read Profile objects from a file (attempt all readers)
    def _get_profiles_from_file(
        path: Path, target_profile_id: str | None = None
    ) -> List[Profile]:
        """Read Profile objects from a file using available readers.

        Tries the 9-col reader, the BMAP freeformat reader, and a CSV
        reader in order. If `target_profile_id` is provided only profiles
        whose `.name` matches the target are returned.

        Args:
            path: Path to the input file.
            target_profile_id: Optional profile id to filter returned results.

        Returns:
            A list of `Profile` objects or an empty list if none could be read.
        """
        # Try 9-col
        try:
            profiles = read_9col_profiles(str(path))
            if profiles:
                if target_profile_id:
                    return [
                        p
                        for p in profiles
                        if (getattr(p, "name", None) == target_profile_id)
                    ]
                return profiles
        except (OSError, ValueError, TypeError) as e:
            log_quick_tool_error(
                "profile_scanner", f"9-col read failed for {path}: {e}"
            )
            pass

        # Try BMAP (returns Profile objects via read_bmap_freeformat)
        try:
            profiles = read_bmap_freeformat(str(path))
            if profiles:
                if target_profile_id:
                    return [
                        p
                        for p in profiles
                        if (getattr(p, "name", None) == target_profile_id)
                    ]
                return profiles
        except (OSError, ValueError, TypeError) as e:
            log_quick_tool_error("profile_scanner", f"BMAP read failed for {path}: {e}")
            pass

        # Try CSV parsing
        try:
            profiles = read_csv_profiles(str(path))
            if profiles:
                if target_profile_id:
                    return [
                        p
                        for p in profiles
                        if (getattr(p, "name", None) == target_profile_id)
                    ]
                return profiles
        except (OSError, ValueError, TypeError, pd.errors.ParserError) as e:
            log_quick_tool_error("profile_scanner", f"CSV read failed for {path}: {e}")
            pass

        return []

    # Ask whether user wants a single combined output or multiple grouped outputs
    save_mode = (
        input(
            "\nSave to (1) single combined file or (2) multiple files/groups? [1/2] [1]: "
        ).strip()
        or "1"
    )

    def _write_bmap_append(profiles: List[Profile], out_path: Path) -> None:
        """Append Profile objects to a BMAP freeformat file.

        Args:
            profiles: List of Profile objects to append.
            out_path: Destination file path.
        """

        # Append profiles to existing BMAP file
        with open(out_path, "a", encoding="utf-8") as f:
            for profile in profiles:
                header_parts = [profile.name]
                if getattr(profile, "date", None):
                    header_parts.append(
                        format_date_for_bmap(profile.date) or str(profile.date)
                    )
                if getattr(profile, "description", None):
                    header_parts.append(profile.description)
                f.write(" ".join([str(p) for p in header_parts]) + "\n")
                f.write(f"{len(profile.x)}\n")
                for x, z in zip(profile.x, profile.z):
                    f.write(f"{x:.3f} {z:.3f}\n")
                f.write("\n")

    def _write_csv_append(profiles: List[Profile], out_path: Path) -> None:
        """Append profiles to a CSV file without duplicating headers.

        Writes to a temporary file via `write_csv_profiles` then appends the
        body (skipping the header) to the destination path.
        """

        # write to temp then append without header
        tmp = Path(tempfile.NamedTemporaryFile(delete=False).name)
        try:
            write_csv_profiles(profiles, tmp)
            # append content without header
            with (
                open(tmp, "r", encoding="utf-8") as fin,
                open(out_path, "a", encoding="utf-8") as fout,
            ):
                lines = fin.readlines()
                if len(lines) > 1:
                    fout.writelines(lines[1:])
        except (OSError, IOError) as e:
            log_quick_tool_error(f"CSV append failed for {out_path}: {e}")
        finally:
            try:
                tmp.unlink()
            except (OSError, IOError):
                pass

    def _write_shapefile(profiles: List[Profile], out_path: Path) -> bool:
        """Write profiles as a point shapefile.

        Creates a point shapefile where each profile is represented by its
        first point or centroid.

        Args:
            profiles: Profiles to write.
            out_path: Destination shapefile path (without extension).

        Returns:
            True on success, False otherwise.
        """
        try:
            import shapefile
        except ImportError:
            print(
                "Shapefile export requires 'pyshp' package. Install with: pip install pyshp"
            )
            return False

        try:
            # Create shapefile writer
            shp_base = str(out_path).replace(".shp", "")  # Remove extension if present
            w = shapefile.Writer(shp_base, shapeType=shapefile.POINT)

            # Define fields
            w.field("PROFILE_ID", "C", 50)
            w.field("DATE", "C", 20)
            w.field("DESCRIPTION", "C", 100)
            w.field("POINT_COUNT", "N", 10, 0)
            w.field("X_MIN", "N", 12, 6)
            w.field("X_MAX", "N", 12, 6)
            w.field("Y_MIN", "N", 12, 6)
            w.field("Y_MAX", "N", 12, 6)
            w.field("Z_MIN", "N", 12, 6)
            w.field("Z_MAX", "N", 12, 6)

            for profile in profiles:
                if not hasattr(profile, "x") or not profile.x:
                    continue

                # Use first point as the shapefile point
                x_coord = float(profile.x[0])
                y_coord = (
                    0.0  # Default Y coordinate since profiles are typically 2D (X,Z)
                )

                # Calculate bounds
                x_min = min(profile.x) if profile.x else 0
                x_max = max(profile.x) if profile.x else 0
                z_min = min(profile.z) if hasattr(profile, "z") and profile.z else 0
                z_max = max(profile.z) if hasattr(profile, "z") and profile.z else 0

                # Add point and record
                w.point(x_coord, y_coord)
                w.record(
                    PROFILE_ID=getattr(profile, "name", ""),
                    DATE=getattr(profile, "date", ""),
                    DESCRIPTION=getattr(profile, "description", ""),
                    POINT_COUNT=len(profile.x),
                    X_MIN=float(x_min),
                    X_MAX=float(x_max),
                    Y_MIN=0.0,
                    Y_MAX=0.0,
                    Z_MIN=float(z_min),
                    Z_MAX=float(z_max),
                )

            w.close()
            print(f"Created shapefile: {shp_base}.shp (with .dbf and .shx files)")
            return True

        except (IOError, OSError, ValueError) as e:
            print(f"Failed to create shapefile: {e}")
            log_quick_tool_error("profile_scanner", f"Shapefile creation failed: {e}")
            return False

    def _write_summary_report(
        parsed_entries: List[dict], stats: dict, out_path: Path
    ) -> bool:
        """Write a comprehensive summary report with statistics and duplicate information.

        Args:
            parsed_entries: Parsed profile entries.
            stats: Scan statistics.
            out_path: Destination report file path.

        Returns:
            True on success, False otherwise.
        """
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("PROFILE SCANNER SUMMARY REPORT\n")
                f.write("=" * 50 + "\n\n")

                # Scan overview
                f.write("SCAN OVERVIEW\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total files scanned: {stats.get('total_files_scanned', 0)}\n")
                f.write(
                    f"Scan duration: {stats.get('performance', {}).get('scan_duration_seconds', 0):.2f} seconds\n"
                )
                f.write(
                    f"Files per second: {stats.get('performance', {}).get('files_per_second', 0):.1f}\n\n"
                )

                # File types
                f.write("FILE TYPES FOUND\n")
                f.write("-" * 20 + "\n")
                for file_type, count in stats.get("files_by_type", {}).items():
                    if count > 0:
                        f.write(f"  {file_type}: {count}\n")
                f.write("\n")

                # Parsing results
                f.write("PARSING RESULTS\n")
                f.write("-" * 20 + "\n")
                parsing = stats.get("parsing_results", {})
                f.write(f"  Successful parses: {parsing.get('successful_parses', 0)}\n")
                f.write(f"  Failed parses: {parsing.get('failed_parses', 0)}\n")
                f.write(
                    f"  Total profiles found: {parsing.get('total_profiles_found', 0)}\n"
                )
                if parsing.get("successful_parses", 0) > 0:
                    f.write(
                        f"  Average profiles per file: {parsing.get('average_profiles_per_file', 0):.1f}\n"
                    )
                f.write("\n")

                # File sizes
                if stats.get("file_sizes", {}).get("total_size_bytes", 0) > 0:
                    f.write("FILE SIZE STATISTICS\n")
                    f.write("-" * 20 + "\n")
                    total_mb = stats["file_sizes"]["total_size_bytes"] / (1024 * 1024)
                    avg_kb = stats["file_sizes"]["average_size_bytes"] / 1024
                    f.write(f"  Total size: {total_mb:.1f} MB\n")
                    f.write(f"  Average size: {avg_kb:.1f} KB\n")
                    if stats["file_sizes"].get("largest_file", {}).get("path"):
                        largest_mb = stats["file_sizes"]["largest_file"]["size"] / (
                            1024 * 1024
                        )
                        f.write(
                            f"  Largest file: {largest_mb:.1f} MB ({Path(stats['file_sizes']['largest_file']['path']).name})\n"
                        )
                    f.write("\n")

                # Duplicate information
                duplicates = stats.get("duplicates", {})
                if duplicates.get("duplicate_groups_found", 0) > 0:
                    f.write("DUPLICATE ANALYSIS\n")
                    f.write("-" * 20 + "\n")
                    f.write(
                        f"  Duplicate groups found: {duplicates['duplicate_groups_found']}\n"
                    )
                    f.write(
                        f"  Total duplicate profiles: {duplicates['total_duplicate_profiles']}\n"
                    )
                    f.write(f"  Unique profiles: {duplicates['unique_profiles']}\n\n")

                    f.write("  Duplicate Groups:\n")
                    for i, group in enumerate(
                        duplicates.get("duplicate_groups", []), 1
                    ):
                        profile_ids = [pid for pid in group["profile_ids"] if pid]
                        id_display = profile_ids[0] if profile_ids else "no ID"
                        f.write(
                            f"    Group {i}: {group['count']} copies of profile '{id_display}'\n"
                        )
                        f.write(
                            f"      Files: {', '.join([Path(f).name for f in group['files']])}\n"
                        )
                    f.write("\n")

                # Profile details
                f.write("PROFILE DETAILS\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total profiles in results: {len(parsed_entries)}\n\n")

                for i, entry in enumerate(parsed_entries[:50], 1):  # Limit to first 50
                    f.write(f"Profile {i}:\n")
                    f.write(f"  ID: {entry.get('profile_id', 'no ID')}\n")
                    f.write(f"  File: {Path(entry.get('file', '')).name}\n")
                    f.write(f"  Point count: {entry.get('point_count', 'unknown')}\n")
                    f.write(f"  Date: {entry.get('date', 'no date')}\n")
                    if entry.get("xmin") is not None:
                        f.write(
                            f"  Bounds: X({entry.get('xmin'):.2f} to {entry.get('xmax'):.2f}), Z({entry.get('zmin'):.2f} to {entry.get('zmax'):.2f})\n"
                        )
                    f.write("\n")

                if len(parsed_entries) > 50:
                    f.write(f"... and {len(parsed_entries) - 50} more profiles\n")

            print(f"Summary report saved to: {out_path}")
            return True

        except (IOError, OSError) as e:
            print(f"Failed to write summary report: {e}")
            log_quick_tool_error(
                "profile_scanner", f"Summary report creation failed: {e}"
            )
            return False

    def _write_filtered_export(parsed_entries: List[dict], out_path: Path) -> bool:
        """Export the current filtered profile entries as a structured data file.

        Args:
            parsed_entries: Current filtered profile entries.
            out_path: Destination file path.

        Returns:
            True on success, False otherwise.
        """
        try:
            import pandas as pd

            # Convert entries to DataFrame
            data = []
            for entry in parsed_entries:
                data.append(
                    {
                        "profile_id": entry.get("profile_id", ""),
                        "station": entry.get("station", ""),
                        "purpose": entry.get("purpose", ""),
                        "date": entry.get("date", ""),
                        "file": entry.get("file", ""),
                        "point_count": entry.get("point_count", ""),
                        "xmin": entry.get("xmin", ""),
                        "xmax": entry.get("xmax", ""),
                        "ymin": entry.get("ymin", ""),
                        "ymax": entry.get("ymax", ""),
                        "zmin": entry.get("zmin", ""),
                        "zmax": entry.get("zmax", ""),
                        "parsed": entry.get("parsed", False),
                    }
                )

            df = pd.DataFrame(data)
            df.to_csv(out_path, index=False)

            print(
                f"Filtered export saved to: {out_path} ({len(parsed_entries)} profiles)"
            )
            return True

        except (IOError, OSError) as e:
            print(f"Failed to write filtered export: {e}")
            log_quick_tool_error("profile_scanner", f"Filtered export failed: {e}")
            return False

    def _confirm_overwrite_append(path: Path) -> str:
        """Ask the user whether to overwrite, append or cancel when a file exists.

        Returns:
            'w' for overwrite, 'a' for append, 'c' for cancel.
        """

        if not path.exists():
            return "w"
        choice = (
            input(
                f"File {path} exists. Overwrite (O), Append (A), or Cancel (C)? [C]: "
            )
            .strip()
            .lower()
        )
        if choice == "o":
            return "w"
        if choice == "a":
            return "a"
        return "c"

    def _write_group(
        profiles: List[Profile],
        fmt_choice: str,
        out_path: Path,
        parsed_entries: List[dict] = None,
        stats: dict = None,
    ) -> bool:
        """Write a group of profiles to the specified output path.

        The function supports both overwrite (atomic write) and append
        modes determined by user input via `_confirm_overwrite_append`.

        Args:
            profiles: Profiles to write.
            fmt_choice: '1' for BMAP, '2' for CSV, '3' for shapefile, '4' for summary, '5' for filtered export.
            out_path: Destination path.
            parsed_entries: Profile entries (needed for formats 4 and 5).
            stats: Scan statistics (needed for format 4).

        Returns:
            True on success, False otherwise.
        """

        # Handle special export formats that don't use standard profile writing
        if fmt_choice == "3":
            return _write_shapefile(profiles, out_path)
        elif fmt_choice == "4":
            return _write_summary_report(parsed_entries or [], stats or {}, out_path)
        elif fmt_choice == "5":
            return _write_filtered_export(parsed_entries or [], out_path)

        mode = _confirm_overwrite_append(out_path)
        if mode == "c":
            print(f"Skipping {out_path}")
            return False
        # atomic write for overwrite: write to temp then move
        if mode == "w":
            tmpf = Path(
                tempfile.NamedTemporaryFile(delete=False, dir=str(out_path.parent)).name
            )
            try:
                if fmt_choice == "2":
                    write_csv_profiles(profiles, tmpf)
                else:
                    write_bmap_profiles(profiles, tmpf)
                shutil.move(str(tmpf), str(out_path))
            except (OSError, shutil.Error) as e:
                print(f"Failed to write {out_path}: {e}")
                log_quick_tool_error(f"Group write failed for {out_path}: {e}")
                try:
                    tmpf.unlink()
                except (OSError, IOError):
                    pass
                return False
            return True
        else:
            # append
            try:
                if fmt_choice == "2":
                    _write_csv_append(profiles, out_path)
                else:
                    _write_bmap_append(profiles, out_path)
                return True
            except (OSError, IOError) as e:
                print(f"Failed to append to {out_path}: {e}")
                log_quick_tool_error(f"Group append failed for {out_path}: {e}")
                return False

    # Get profile groups
    if save_mode == "2":
        grp_input = input(
            "Enter groups separated by ';' (e.g. 1-3,5;4;6) or 'auto' to write one file per selected profile: "
        ).strip()
        groups: List[List[int]] = []
        if grp_input.lower() == "auto":
            groups = [[i] for i in indices]
        else:
            # parse groups
            for part in [g.strip() for g in grp_input.split(";") if g.strip()]:
                # reuse parse_selection on the group part
                sel = parse_selection(part, len(parsed_entries))
                if sel:
                    groups.append(sel)
        if not groups:
            print("No valid groups provided. Aborting save.")
            return
    else:
        # single group combining all selected
        groups = [indices]

    # Ask for output format
    print("\nSelect output format:")
    print("1. BMAP free format")
    print("2. CSV")
    print("3. Point shapefile (.shp)")
    print("4. Summary report (statistics + duplicates)")
    print("5. Filtered export (apply current filters)")
    fmt_choice = input("Choose format (1/2/3/4/5) [1]: ").strip() or "1"

    # For each group, collect profiles and write files
    for gi, group in enumerate(groups, start=1):
        group_profiles: List[Profile] = []
        for sel_idx in group:
            entry = parsed_entries[sel_idx]
            file_path = Path(entry.get("file", ""))
            pid = entry.get("profile_id", "") or None
            try:
                found_profiles = _get_profiles_from_file(file_path, pid)
                if found_profiles:
                    group_profiles.extend(found_profiles)
            except (OSError, ValueError, TypeError) as e:
                log_quick_tool_error(
                    f"Failed to read profiles from {file_path} for PID {pid}: {e}"
                )
                continue

        if not group_profiles:
            print(f"No profiles available for group {gi}. Skipping.")
            continue

        # ask for filename for this group (provide default in scanned folder)
        if fmt_choice == "3":
            ext = ".shp"
        elif fmt_choice == "4":
            ext = ".txt"
        elif fmt_choice == "5":
            ext = ".csv"
        else:
            ext = ".txt"  # Default for BMAP and CSV
        default_name = str(
            out_dir
            / Path(timestamped_output_path(f"profile_scanner_group{gi}", ext=ext))
        )
        out_path = (
            input(
                f"Enter output filename for group {gi} [default: {default_name}]: "
            ).strip()
            or default_name
        )
        out_p = Path(out_path)

        success = _write_group(group_profiles, fmt_choice, out_p, parsed_entries, stats)
        if success:
            print(f"Saved {len(group_profiles)} profile(s) to {out_p}")


def execute_from_cli(args: List[str]) -> int:
    # simple CLI: args[0] = folder, optional --no-recursive
    # This quick-tool is interactive-only (menu-driven). Expose a CLI would
    # create a runnable entrypoint which we intentionally avoid. Tests that
    # iterate quick_tools modules expect calling execute_from_cli to raise
    # NotImplementedError or ImportError to enforce menu-only usage.
    raise NotImplementedError(
        "profile_scanner is interactive-only; use from the Quick Tools menu"
    )

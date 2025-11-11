# =============================================================================
# Beach Profile Survey Date Extraction Tool
# =============================================================================
#
# FILE: src/profcalc/cli/tools/get_profile_dates.py
#
# PURPOSE:
# This tool extracts and analyzes survey dates from 9-column beach profile
# survey files, providing comprehensive reports on temporal coverage and
# survey frequency for each profile. It helps users understand the temporal
# distribution of their survey data and identify gaps in monitoring coverage.
#
# WHAT IT'S FOR:
# - Extracts unique survey dates from 9-column survey data files
# - Generates per-profile reports of survey temporal coverage
# - Identifies survey frequency and temporal gaps
# - Creates CSV and formatted text reports of date information
# - Supports both programmatic and interactive usage
# - Handles multiple survey types within the same dataset
#
# WORKFLOW POSITION:
# This tool is used during data exploration and quality assessment phases
# to understand the temporal characteristics of survey datasets. It's
# particularly important for long-term monitoring programs where consistent
# temporal coverage is critical for trend analysis and erosion rate calculations.
#
# LIMITATIONS:
# - Specifically designed for 9-column survey data format
# - Requires properly formatted date information in the data
# - May not handle irregular date formats or missing date data
# - Large datasets may require significant processing time
#
# ASSUMPTIONS:
# - Input files follow the 9-column survey data format standard
# - Date information is present and properly formatted in the data
# - Profile IDs are consistent and meaningful for temporal analysis
# - Users understand survey date concepts and temporal analysis
# - Date ranges are appropriate for the monitoring objectives
#
# =============================================================================

"""Extract Profile Survey Dates

Extract unique survey dates from 9-column survey files and generate
comprehensive date reports per profile ID.

Usage examples:
    - Menu: Quick Tools → Extract Profile Dates (invokes :func:`execute_from_menu`).
"""

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from profcalc.cli.menu_system import notify_and_wait
from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.cli.quick_tools.quick_tool_utils import (
    timestamped_output_path,
)


def execute_from_menu() -> None:
    """Interactive, menu-driven entry point for the profile dates extraction tool.

    Prompts user for a 9-column survey file, extracts survey dates by profile
    and survey type, and generates CSV and formatted text outputs.
    """
    from profcalc.cli.file_dialogs import select_input_file

    print("\n" + "=" * 60)
    print("EXTRACT PROFILE SURVEY DATES")
    print("=" * 60)

    # Get input file
    print("Select a 9-column file...")
    file_path = select_input_file("Select 9-Column File")
    if not file_path:
        print("No file selected.")
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        print(f"File not found: {file_path}")
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    # Process the file
    try:
        result = _process_profile_dates_file(str(file_path_obj))
        if result is None:
            notify_and_wait("", prompt="\nPress Enter to continue...")
            return
    except (IOError, OSError, ValueError, UnicodeDecodeError) as e:
        log_quick_tool_error("get_profile_dates", f"Error processing file: {e}", exc=e)
        print(f"❌ Error processing file: {e}")
        notify_and_wait("", prompt="\nPress Enter to continue...")
        return

    header_row, table_data, txt_table = result

    # Generate output file names
    base_dir = file_path_obj.parent
    ts = timestamped_output_path("get_profile_dates", ext="").split("_")[
        -2
    ]  # Extract timestamp part
    base_name = f"output_get_profile_dates_{ts}"

    # Write CSV output
    csv_path = base_dir / f"{base_name}.csv"
    try:
        _write_csv_file(csv_path, header_row, table_data)
        print(f"✅ CSV output saved to: {csv_path}")
    except (IOError, OSError, PermissionError) as e:
        log_quick_tool_error("get_profile_dates", f"Failed to write CSV: {e}", exc=e)
        print(f"❌ Failed to write CSV: {e}")

    # Write text output
    txt_path = base_dir / f"{base_name}.txt"
    try:
        _write_text_file(txt_path, txt_table)
        print(f"✅ Text output saved to: {txt_path}")
    except (IOError, OSError, PermissionError) as e:
        log_quick_tool_error("get_profile_dates", f"Failed to write text: {e}", exc=e)
        print(f"❌ Failed to write text: {e}")

    # Display formatted table
    if txt_table:
        print("\nFormatted Table:\n")
        print(txt_table)

    notify_and_wait("", prompt="\nPress Enter to continue...")


def _process_profile_dates_file(
    file_path: str,
) -> tuple[list[str], list[list[str]], str] | None:
    """Process a 9-column survey file and extract profile dates.

    Returns:
        Tuple of (header_row, table_data, formatted_text) or None if error.
    """
    tool_name = "get_profile_dates"

    try:
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                first = next(reader)
            except StopIteration:
                msg = "File is empty."
                print(f"❌ {msg}")
                log_quick_tool_error(tool_name, msg)
                return None
            except (csv.Error, OSError) as e:
                msg = f"Could not read CSV file: {e}"
                print(f"❌ {msg}")
                log_quick_tool_error(tool_name, msg)
                return None

            # Detect if first row is header
            header = _is_header_row(first)
            if header:
                columns = [c.strip().lower() for c in first]
                data_rows = []
                for _ in range(20):  # Sample first 20 rows for detection
                    try:
                        data_rows.append(next(reader))
                    except StopIteration:
                        break
                # Use sampled data rows for detection
                idx_type = _detect_survey_type_column(data_rows)
                if idx_type is None:
                    idx_type = 7
                    msg = "Could not confidently detect survey type column. Using default column 8."
                    print(f"⚠️  {msg}")
                    log_quick_tool_error(tool_name, msg)
                else:
                    msg = f"Detected survey type column: {idx_type + 1} ({columns[idx_type]})"
                    print(f"✅ {msg}")
                # Get all remaining rows
                all_rows = data_rows + list(reader)
            else:
                columns = [f"col{i + 1}" for i in range(9)]
                all_rows = [first] + list(reader)
                data_rows = all_rows[:20]
                idx_type = _detect_survey_type_column(data_rows)
                if idx_type is None:
                    idx_type = 7
                    msg = "Could not confidently detect survey type column. Using default column 8."
                    print(f"⚠️  {msg}")
                    log_quick_tool_error(tool_name, msg)
                else:
                    msg = f"Detected survey type column: {idx_type + 1}"
                    print(f"✅ {msg}")

            if len(columns) != 9:
                msg = "File does not have 9 columns."
                print(f"❌ {msg}")
                log_quick_tool_error(tool_name, msg)
                return None

            # Process data
            profiles = defaultdict(lambda: defaultdict(set))
            all_dates = defaultdict(set)

            for row in all_rows:
                if len(row) != 9:
                    msg = f"Skipping row with {len(row)} columns: {row}"
                    print(f"⚠️  {msg}")
                    log_quick_tool_error(tool_name, msg)
                    continue

                pid = row[0].strip()  # Profile ID
                date_raw = row[1].strip()  # Date
                typ = row[idx_type].strip().lower()  # Survey type

                date = _parse_date(date_raw)
                if not pid or not date:
                    msg = f"Skipping row with invalid profile/date: {row}"
                    print(f"⚠️  {msg}")
                    log_quick_tool_error(tool_name, msg)
                    continue

                if typ not in ("topo", "wading", "hydro"):
                    msg = f"Skipping row with unknown type '{typ}': {row}"
                    print(f"⚠️  {msg}")
                    log_quick_tool_error(tool_name, msg)
                    continue

                profiles[pid][typ].add(date)
                all_dates[pid].add(date)

            # Build output table
            header_row = [
                "Profile ID",
                "Topo Date 1",
                "Topo Date 2",
                "Wading Date 1",
                "Wading Date 2",
                "Hydro Date 1",
                "Hydro Date 2",
                "Duration (days)",
            ]

            table_data = []
            for pid in sorted(profiles):
                row = [pid]
                for typ in ("topo", "wading", "hydro"):
                    dates = sorted(profiles[pid][typ])
                    row += [d.strftime("%Y-%m-%d") for d in dates[:2]]
                    if len(dates) < 2:
                        row += [""] * (2 - len(dates))

                if all_dates[pid]:
                    min_d = min(all_dates[pid])
                    max_d = max(all_dates[pid])
                    duration = (max_d - min_d).days
                    duration_str = str(duration)
                else:
                    duration_str = ""
                row.append(duration_str)
                table_data.append(row)

            # Generate formatted text table
            txt_table = _format_table_text(header_row, table_data)

            return header_row, table_data, txt_table

    except (IOError, OSError, ValueError, UnicodeDecodeError, IndexError) as e:
        log_quick_tool_error(tool_name, f"Unexpected error: {e}", exc=e)
        print(f"❌ Unexpected error: {e}")
        return None


def _is_header_row(row: list[str]) -> bool:
    """Check if a row appears to be a header row."""
    if len(row) != 9:
        return False

    # Simple heuristic: if most values look like column names or are non-numeric
    text_count = 0
    for cell in row:
        cell = cell.strip().lower()
        if not cell:
            continue
        # Check if it looks like a date or number
        if not any(char.isdigit() for char in cell):
            text_count += 1
        elif cell in ("profile", "date", "type", "topo", "wading", "hydro"):
            text_count += 1

    return text_count >= 3


def _detect_survey_type_column(
    rows: list[list[str]], known_types=("topo", "wading", "hydro")
) -> int | None:
    """Detect which column contains survey type information."""
    if not rows:
        return None

    col_counts = [0] * 9
    for row in rows:
        if len(row) != 9:
            continue
        for i, val in enumerate(row):
            if val.strip().lower() in known_types:
                col_counts[i] += 1

    max_count = max(col_counts)
    if max_count == 0:
        return None

    # If multiple columns have the same max count, ambiguous
    if col_counts.count(max_count) > 1:
        return None

    return col_counts.index(max_count)


def _parse_date(val: str) -> Optional[datetime.date]:
    """Parse a date string into a date object."""
    from datetime import datetime

    val = val.strip()
    if not val:
        return None

    # Try various date formats
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%d%b%Y",
        "%d %b %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue

    return None


def _format_table_text(header_row: list[str], table_data: list[list[str]]) -> str:
    """Format table data as a text table."""
    try:
        from tabulate import tabulate

        return tabulate(table_data, headers=header_row, tablefmt="github")
    except ImportError:
        # Fallback ASCII table
        lines = []
        lines.append("=" * 100)
        lines.append("PROFILE SURVEY DATES")
        lines.append("=" * 100)

        # Header
        header_line = " | ".join(f"{h:<12}" for h in header_row[:4])  # First 4 columns
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Data (simplified for first few columns)
        for row in table_data[:20]:  # Limit to first 20 rows
            data_line = " | ".join(f"{cell:<12}" for cell in row[:4])
            lines.append(data_line)

        if len(table_data) > 20:
            lines.append(f"... and {len(table_data) - 20} more profiles")

        return "\n".join(lines)


def _write_csv_file(
    file_path: Path, header_row: list[str], table_data: list[list[str]]
) -> None:
    """Write table data to CSV file."""
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header_row)
        writer.writerows(table_data)


def _write_text_file(file_path: Path, content: str) -> None:
    """Write text content to file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


__all__ = ["execute_from_menu"]

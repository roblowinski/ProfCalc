#!/usr/bin/env python3
"""
get_profile_dates.py

Quick tool to scan a 9-column survey file and generate a table of unique survey dates per profile ID.

Features:
- Prompts user for the 9-column CSV file path.
- Validates file structure and contents.
- For each profile ID, collects up to 2 unique dates for each type (topo, wading, hydro).
- Outputs a table with columns:
    Profile ID, Topo Date 1, Topo Date 2, Wading Date 1, Wading Date 2, Hydro Date 1, Hydro Date 2, Duration
    - Duration is the difference (in days) between the earliest and latest date for that profile.
- Handles files with or without headers.

Output:
- Prints the table to the console in CSV format.
- Saves the table as 'output_profile_dates.csv' in the current directory.
- Prints a nicely formatted text table using the tabulate library (if installed).
- Saves the formatted table as 'output_profile_dates.txt' in the current directory.

Requirements:
- Python 3.x
- tabulate (for pretty text table output; install via pip if needed)

Usage: python get_profile_dates.py
"""

import argparse
import csv
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.cli.quick_tools.quick_tool_utils import (
    is_header as util_is_header,
)
from profcalc.cli.quick_tools.quick_tool_utils import (
    parse_date as util_parse_date,
)
from profcalc.cli.quick_tools.quick_tool_utils import (
    write_csv as util_write_csv,
)
from profcalc.cli.quick_tools.quick_tool_utils import (
    write_tabulate as util_write_tabulate,
)


def prompt_file():
    path = input("Enter path to 9-column survey file: ").strip()
    if not os.path.isfile(path):
        msg = f"ERROR: File not found: {path}"
        print(msg)
        log_quick_tool_error("get_profile_dates", msg)
        return None
    return path


def is_header(row):
    return util_is_header(row)


def parse_date(val):
    return util_parse_date(val)

def detect_survey_type_column(rows, known_types=("topo", "wading", "hydro")):
    # For each column, count how many values match known survey types
    col_counts = [0] * 9
    for row in rows:
        if len(row) != 9:
            continue
        for i, val in enumerate(row):
            if val.strip().lower() in known_types:
                col_counts[i] += 1
    max_count = max(col_counts)
    if max_count == 0:
        return None  # No likely column found
    # If more than one column has the same max count, ambiguous
    if col_counts.count(max_count) > 1:
        return None
    return col_counts.index(max_count)

def build_arg_parser():
    p = argparse.ArgumentParser(description="Extract profile survey dates from a 9-column file")
    p.add_argument("input", nargs="?", help="Path to 9-column survey file")
    p.add_argument("--csv-out", default=None, help="CSV output path")
    p.add_argument("--txt-out", default=None, help="Text (pretty) output path")
    p.add_argument("--no-tabulate", action="store_true", help="Skip pretty text output")
    p.add_argument("--detect-rows", type=int, default=20, help="Number of rows to use for type detection")
    return p


def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    path = args.input or None
    if not path:
        path = prompt_file()
    if not path:
        return
    tool_name = "get_profile_dates"
    with open(path, newline='') as f:
        reader = csv.reader(f)
        try:
            first = next(reader)
        except Exception:
            msg = "ERROR: File is empty or unreadable."
            print(msg)
            log_quick_tool_error(tool_name, msg)
            return
        header = is_header(first)
        if header:
            columns = [c.strip().lower() for c in first]
            data_rows = []
            for _ in range(args.detect_rows):
                try:
                    data_rows.append(next(reader))
                except StopIteration:
                    break
            # Use first 20 data rows for detection
            idx_type = detect_survey_type_column(data_rows)
            if idx_type is None:
                idx_type = 7
                msg = "WARNING: Could not confidently detect survey type column. Using default column 8."
                print(msg)
                log_quick_tool_error(tool_name, msg)
            else:
                msg = f"Detected survey type column: {idx_type+1} ({columns[idx_type]})"
                print(msg)
                log_quick_tool_error(tool_name, msg)
            # Rewind reader to include all data rows
            all_rows = data_rows + list(reader)
        else:
            columns = [f"col{i+1}" for i in range(9)]
            # Use first 20 rows for detection
            all_rows = [first] + list(reader)
            data_rows = all_rows[: args.detect_rows]
            idx_type = detect_survey_type_column(data_rows)
            if idx_type is None:
                idx_type = 7
                msg = "WARNING: Could not confidently detect survey type column. Using default column 8."
                print(msg)
                log_quick_tool_error(tool_name, msg)
            else:
                msg = f"Detected survey type column: {idx_type+1}"
                print(msg)
                log_quick_tool_error(tool_name, msg)
        if len(columns) != 9:
            msg = "ERROR: File does not have 9 columns."
            print(msg)
            log_quick_tool_error(tool_name, msg)
            return
        # Indices
        idx_profile = 0
        idx_date = 1
        # Prepare data structure
        profiles = defaultdict(lambda: defaultdict(set))
        all_dates = defaultdict(set)
        # Read data
        for row in all_rows:
            if len(row) != 9:
                msg = f"WARNING: Skipping row with {len(row)} columns: {row}"
                print(msg)
                log_quick_tool_error(tool_name, msg)
                continue
            pid = row[idx_profile].strip()
            date_raw = row[idx_date].strip()
            typ = row[idx_type].strip().lower()
            date = parse_date(date_raw)
            if not pid or not date:
                msg = f"WARNING: Skipping row with invalid profile/date: {row}"
                print(msg)
                log_quick_tool_error(tool_name, msg)
                continue
            if typ not in ("topo", "wading", "hydro"):
                msg = f"WARNING: Skipping row with unknown type '{typ}': {row}"
                print(msg)
                log_quick_tool_error(tool_name, msg)
                continue
            profiles[pid][typ].add(date)
            all_dates[pid].add(date)

        # Prepare output table data
        header_row = [
            "Profile ID",
            "Topo Date 1", "Topo Date 2",
            "Wading Date 1", "Wading Date 2",
            "Hydro Date 1", "Hydro Date 2",
            "Duration (days)"
        ]
        table = []
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
                duration_str = f"{duration} days"
            else:
                duration_str = ""
            row.append(duration_str)
            table.append(row)

        # Write CSV output
        csv_out = args.csv_out or "output_get_profile_dates.csv"
        util_write_csv(csv_out, header_row, table)
        print(f"Saved CSV output to {csv_out}")

        # Write and print tabulate output
        txt_out = args.txt_out or "output_get_profile_dates.txt"
        txt_table = None
        if not args.no_tabulate:
            txt_table = util_write_tabulate(txt_out, header_row, table)
            if txt_table:
                print("\nFormatted Table:\n")
                print(txt_table)
                print(f"Saved formatted table to {txt_out}")
            else:
                print("tabulate library not found. Skipping pretty text table output.")

if __name__ == "__main__":
    main()

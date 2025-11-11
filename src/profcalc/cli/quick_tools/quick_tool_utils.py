# =============================================================================
# Quick Tool Utilities
# =============================================================================
#
# FILE: src/profcalc/cli/quick_tools/quick_tool_utils.py
#
# PURPOSE:
# This module provides shared utility functions used across quick tools in the
# ProfCalc CLI. It includes date parsing, header detection, output formatting,
# and other common functionality needed by multiple quick tool implementations.
#
# WHAT IT'S FOR:
# - Providing flexible date parsing for various formats
# - Detecting header rows in data files
# - Formatting output for CSV and tabular display
# - Supporting common data processing operations
# - Offering shared logging integration for quick tools

# WORKFLOW POSITION:
# This utility module serves as a common foundation for quick tool operations.
# Individual quick tools import and use these utilities to handle common tasks
# like date parsing and output formatting, ensuring consistency across tools.

# LIMITATIONS:
# - Date parsing limited to predefined formats
# - Header detection uses simple heuristics
# - Output formatting is basic
# - Limited to quick tool specific needs

# ASSUMPTIONS:
# - Date formats cover common use cases
# - Header detection heuristics are reliable
# - Output formatting meets user needs
# - Shared utilities reduce code duplication

# =============================================================================

"""quick_tool_utils.py

Shared utility functions for quick tools:
- Flexible date parsing
- Header detection
- Output formatting (CSV, tabulate)
- (Uses the shared quick tool logger)
"""

from datetime import datetime
from typing import List, Optional

from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error

# Flexible date parsing
DATE_FORMATS = [
    "%Y%m%d",
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d-%b-%Y",
    "%d%b%Y",
    "%Y/%m/%d",
]


def parse_date(val: str) -> Optional[datetime]:
    """Try to parse a string into a datetime using several common formats.

    Returns a datetime on success or None if parsing fails.
    """
    if not val:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return None


def is_header(row: List[str]) -> bool:
    """Return True if the row looks like a header (i.e. not numeric in the first columns)."""
    try:
        # If first three columns cast to float, this is likely data, not a header
        _ = [float(row[i]) for i in range(3)]
        return False
    except (ValueError, IndexError):
        return True


def write_csv(filename: str, header: List[str], rows: List[List[str]]) -> None:
    """Write header/rows to filename as CSV."""
    import csv

    with open(filename, "w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerow(header)
        writer.writerows(rows)


def write_tabulate(
    filename: str, header: List[str], rows: List[List[str]]
) -> Optional[str]:
    """Write a pretty text table using tabulate, if available.

    Returns the generated text if written, otherwise None.
    """
    try:
        from tabulate import tabulate

        txt_table = tabulate(rows, headers=header, tablefmt="github")
        with open(filename, "w", encoding="utf-8") as ftxt:
            ftxt.write(txt_table)
        return txt_table
    except ImportError:
        log_quick_tool_error(
            "quick_tool_utils",
            "tabulate library not found. Skipping pretty text table output.",
        )
        return None


def default_output_path(
    tool_name: str, input_path: Optional[str] = None, ext: Optional[str] = None
) -> str:
    """Return a default output filename for a quick tool.

    If ext is provided it will be used, otherwise the input file extension
    will be used when available; otherwise '.txt' is used.
    """
    from pathlib import Path

    if ext:
        if not ext.startswith("."):
            ext = "." + ext
    else:
        if input_path:
            try:
                ext = Path(input_path).suffix or ".txt"
            except OSError:
                ext = ".txt"
        else:
            ext = ".txt"

    return f"output_{tool_name}{ext}"


def timestamped_output_path(tool_name: str, ext: Optional[str] = None) -> str:
    """Return an output filename that contains a timestamp to avoid overwriting."""
    from datetime import datetime

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if ext and not ext.startswith("."):
        ext = "." + ext
    if not ext:
        ext = ".txt"
    return f"output_{tool_name}_{ts}{ext}"

# =============================================================================
# Convert Quick Tool Wrapper
# =============================================================================
#
# FILE: src/profcalc/cli/quick_tools/convert.py
#
# PURPOSE:
# This module provides format conversion utilities and a quick tool wrapper for
# converting between different coastal profile data formats (CSV, XYZ, BMAP,
# Shapefile). It includes lightweight conversion functions and menu integration
# for streamlined format conversion workflows.
#
# WHAT IT'S FOR:
# - Providing format conversion between coastal data formats
# - Supporting CSV, XYZ, BMAP, and Shapefile conversions
# - Enabling data interoperability across different systems
# - Offering menu-integrated access to conversion tools
# - Supporting automated format detection and conversion
#
# WORKFLOW POSITION:
# This quick tool serves as the primary interface for format conversion operations
# in the ProfCalc system. It provides both programmatic conversion utilities and
# menu-driven conversion workflows for users working with different data formats.
#
# LIMITATIONS:
# - Limited to supported format conversions
# - Requires compatible source data structure
# - Column mapping may need manual specification
# - Format detection based on file extensions
#
# ASSUMPTIONS:
# - Input files follow expected format conventions
# - Output formats are compatible with target systems
# - Column specifications are correctly provided
# - File paths are accessible for read/write operations
#
# =============================================================================

"""Simple format conversion utilities used by tests.

Lightweight CSV/XYZ conversion and a menu-only quick-tools wrapper.
"""

import csv
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


def _parse_column_order(
    s: Optional[Union[str, Dict[str, int]]],
) -> Dict[str, int]:
    """Parse column order specification into a mapping dictionary.

    Parameters:
        s: Column order as string (e.g., "x=0,y=1,z=2") or dict, or None for defaults

    Returns:
        Dictionary mapping column names to indices
    """
    if not s:
        return {"x": 0, "y": 1, "z": 2}
    if isinstance(s, dict):
        return s
    parts = str(s).split(",")
    mapping: Dict[str, int] = {}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            mapping[k.strip()] = int(v.strip())
    mapping.setdefault("x", 0)
    mapping.setdefault("y", 1)
    mapping.setdefault("z", 2)
    return mapping


def _detect_format(file_path: str) -> str:
    """Detect file format based on file extension.

    Parameters:
        file_path: Path to the file

    Returns:
        Format string: 'csv', 'xyz', or 'bmap'
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".csv":
        return "csv"
    if ext in (".xyz", ".dat"):
        return "xyz"
    return "bmap"


def _detect_xy_columns(
    headers: Optional[Union[Sequence[str], Dict[str, int]]],
) -> Optional[Dict[str, str]]:
    """Detect X/Y/Z column names from headers.

    Parameters:
        headers: Column headers as list or dict

    Returns:
        Dict mapping 'x', 'y', 'z' to column names, or None if not detected
    """
    if not headers:
        return None

    if isinstance(headers, dict):
        keys = {k.lower(): k for k in headers}
    else:
        keys = {str(k).lower(): str(k) for k in headers}

    if "easting" in keys and "northing" in keys and "elevation" in keys:
        return {
            "x": keys["easting"],
            "y": keys["northing"],
            "z": keys["elevation"],
        }
    if "x" in keys and "y" in keys and "z" in keys:
        return {"x": keys["x"], "y": keys["y"], "z": keys["z"]}

    if isinstance(headers, dict):
        header_list = list(headers.keys())
    else:
        header_list = list(headers)
    if len(header_list) >= 3:
        return {"x": header_list[0], "y": header_list[1], "z": header_list[2]}
    return None


def convert_format(
    input_file: str,
    output_file: str,
    *,
    from_format: str,
    to_format: str,
    column_order: Optional[Dict[str, int]] = None,
) -> None:
    inp = Path(input_file)
    outp = Path(output_file)
    if from_format == "csv" and to_format == "xyz":
        with inp.open("r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            csv_rows = list(reader)

        if not csv_rows:
            outp.write_text("", encoding="utf-8")
            return
        mapping = _detect_xy_columns(reader.fieldnames or [])
        if mapping is None:
            raise ValueError("Could not detect X/Y/Z columns in CSV")

        with outp.open("w", encoding="utf-8") as fh:
            writer = csv.writer(fh, delimiter=" ")
            for row in csv_rows:
                writer.writerow(
                    [
                        row[mapping["x"]],
                        row[mapping["y"]],
                        row.get(mapping.get("z"), ""),
                    ]
                )
        return

    if from_format == "xyz" and to_format == "csv":
        lines = []
        with inp.open("r", encoding="utf-8") as fh:
            for ln in fh:
                s = ln.strip()
                if not s:
                    continue
                if s.startswith("#"):
                    continue
                parts = s.split()
                if len(parts) < 3:
                    continue
                lines.append(parts[:3])
        with outp.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["x", "y", "z"])
            for parts in lines:
                writer.writerow(parts)
        return

    raise NotImplementedError(
        f"Conversion from {from_format} to {to_format} is not supported"
    )


# Menu-only wrappers
try:
    from profcalc.cli.tools import convert as _impl

    impl_execute_from_menu = getattr(_impl, "execute_from_menu", None)
except ImportError:  # pragma: no cover - import fallback

    def execute_from_menu() -> None:  # type: ignore
        raise ImportError("convert tool is not available")

else:
    from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error

    def execute_from_menu() -> None:
        try:
            if impl_execute_from_menu:
                return impl_execute_from_menu()
            raise ImportError("convert implementation has no menu entrypoint")
        except (
            ImportError,
            AttributeError,
            RuntimeError,
            OSError,
            ValueError,
        ) as e:  # pragma: no cover - log and re-raise
            log_quick_tool_error(
                "convert", f"Unhandled exception in convert quick tool: {e}"
            )
            raise

    def execute_from_cli(args: list[str]) -> None:  # type: ignore
        raise NotImplementedError(
            "Quick tools are menu-only; run via the interactive menu."
        )


__all__ = ["convert_format", "execute_from_menu", "execute_from_cli"]

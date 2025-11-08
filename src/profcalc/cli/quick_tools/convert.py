"""Simple format conversion utilities used by tests.

This is a lightweight implementation that supports the minimal features
exercised by the repository tests: CSV -> XYZ and XYZ -> CSV conversions
with an optional `column_order` override for XYZ input.
"""

import csv
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

# Prefer to reuse richer helpers from the full tools implementation when
# available (tests expect helpers like `_parse_column_order` and
# `_detect_format`). Fall back to local lightweight implementations.
try:
    from profcalc.cli.tools.convert import (
        _detect_format,
        _parse_column_order,
    )
except ImportError:  # pragma: no cover - fallback helpers

    def _parse_column_order(
        s: Optional[Union[str, Dict[str, int]]],
    ) -> Dict[str, int]:
        """Parse a simple column order spec (e.g. "x=0,y=1,z=2") into a mapping.

        This minimal fallback supports the limited patterns used in tests.
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
        # Ensure defaults
        mapping.setdefault("x", 0)
        mapping.setdefault("y", 1)
        mapping.setdefault("z", 2)
        return mapping

    def _detect_format(file_path: str) -> str:
        """Minimal detection: choose 'csv' if file extension is .csv else 'xyz'."""
        ext = Path(file_path).suffix.lower()
        if ext == ".csv":
            return "csv"
        if ext in (".xyz", ".dat"):
            return "xyz"
        return "bmap"


def _detect_xy_columns(
    headers: Optional[Union[Sequence[str], Dict[str, int]]],
) -> Optional[Dict[str, str]]:
    """Return mapping for x,y,z column names when reading CSV headers.

    headers: either an ordered sequence of header names, or a mapping
    from header name to index
    """
    if not headers:
        return None

    if isinstance(headers, dict):
        keys = {k.lower(): k for k in headers}
    else:
        # Sequence of header names
        keys = {str(k).lower(): str(k) for k in headers}

    if "easting" in keys and "northing" in keys and "elevation" in keys:
        return {
            "x": keys["easting"],
            "y": keys["northing"],
            "z": keys["elevation"],
        }
    if "utm_x" in keys and "utm_y" in keys and "elevation" in keys:
        return {"x": keys["utm_x"], "y": keys["utm_y"], "z": keys["elevation"]}
    if "x" in keys and "y" in keys and "z" in keys:
        return {"x": keys["x"], "y": keys["y"], "z": keys["z"]}
    # Fallback: try first three columns as x,y,z
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
    """Convert between simple CSV and XYZ formats.

    This function implements the small subset of functionality used by the
    repository tests. It intentionally avoids external dependencies.
    """
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

        lines = []
        for r in csv_rows:
            x = r.get(mapping["x"], "")
            y = r.get(mapping["y"], "")
            z = r.get(mapping["z"], "")
        try:
            from profcalc.cli.tools.convert import (
                execute_from_cli as impl_execute_from_cli,
            )
            from profcalc.cli.tools.convert import (
                execute_from_menu as impl_execute_from_menu,
            )
        except ImportError:  # pragma: no cover - import fallback

            def execute_from_menu() -> None:  # type: ignore
                raise ImportError("convert tool is not available")

            def execute_from_cli(args: list[str]) -> None:  # type: ignore
                raise ImportError("convert tool is not available")
        else:
            from profcalc.cli.quick_tools.quick_tool_logger import (
                log_quick_tool_error,
            )

            def execute_from_menu() -> None:
                try:
                    if impl_execute_from_menu:
                        return impl_execute_from_menu()
                    return impl_execute_from_cli([])
                except Exception as e:  # pragma: no cover - log and re-raise
                    log_quick_tool_error(
                        "convert",
                        f"Unhandled exception in convert quick tool: {e}",
                    )
                    raise
        with inp.open("r", encoding="utf-8") as fh:
            lines = [
                ln.strip()
                for ln in fh
                if ln.strip() and not ln.strip().startswith("#")
            ]

        xyz_rows: list[list[str]] = []
        for ln in lines:
            parts = ln.split()
            xyz_rows.append(parts)

        # Determine column indices
        if column_order:
            xi = int(column_order.get("x", 0))
            yi = int(column_order.get("y", 1))
            zi = int(column_order.get("z", 2))
        else:
            xi, yi, zi = 0, 1, 2

        # Write CSV with header x,y,z
        with outp.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["x", "y", "z"])
            for parts in xyz_rows:
                # Guard against short lines
                if len(parts) <= max(xi, yi, zi):
                    continue
                writer.writerow([parts[xi], parts[yi], parts[zi]])
        return

    raise NotImplementedError(
        f"Conversion from {from_format} to {to_format} is not supported"
    )


# Expose menu/CLI wrappers consistent with other quick_tools modules
try:
    from profcalc.cli.tools.convert import (
        execute_from_cli as impl_execute_from_cli,
    )
    from profcalc.cli.tools.convert import (
        execute_from_menu as impl_execute_from_menu,
    )
except ImportError:  # pragma: no cover - import fallback

    def execute_from_menu() -> None:  # type: ignore
        raise ImportError("convert tool is not available")

    def execute_from_cli(args: list[str]) -> None:  # type: ignore
        raise ImportError("convert tool is not available")
else:
    from profcalc.cli.quick_tools.quick_tool_logger import (
        log_quick_tool_error,
    )

    def execute_from_menu() -> None:
        try:
            if impl_execute_from_menu:
                return impl_execute_from_menu()
            return impl_execute_from_cli([])
        except Exception as e:  # pragma: no cover - log and re-raise
            log_quick_tool_error(
                "convert",
                f"Unhandled exception in convert quick tool: {e}",
            )
            raise


__all__ = ["convert_format", "execute_from_menu", "execute_from_cli"]

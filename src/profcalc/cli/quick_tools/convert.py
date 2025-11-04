"""Simple format conversion utilities used by tests.

This is a lightweight implementation that supports the minimal features
exercised by the repository tests: CSV -> XYZ and XYZ -> CSV conversions
with an optional `column_order` override for XYZ input.
"""

import csv
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


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
            lines.append(f"{x} {y} {z}\n")

        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text("".join(lines), encoding="utf-8")
        return

    if from_format == "xyz" and to_format == "csv":
        # Read xyz-like whitespace-separated columns
        outp.parent.mkdir(parents=True, exist_ok=True)
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

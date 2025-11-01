"""
io_reports.py
--------------
Generates BMAP-style ASCII reports for tool outputs (e.g., Profile Volume Report).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np


def write_volume_report(
    file_path: str,
    results: list[dict],
    contour_level: float = 0.0,
    title: Optional[str] = "Untitled",
):
    """
    Writes a BMAP-style 'Profile Volume Report' to ASCII.
    results: list of dicts with keys:
        - name (str)
        - date (str)
        - description (str)
        - x_on (float)
        - x_off (float)
        - volume_cuyd_per_ft (float)
        - contour_location (float)
    """
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        f.write(f"{title}\n")
        f.write("Profile Volume Report\n")
        f.write(f"Contour Level:\t{contour_level:.2f} ft\t\t\t\n\n")
        f.write(
            "Profile\tXOn(ft)\tXOff(ft)\tVolume(cu. yd/ft)\tContour Location(ft)\n"
        )

        for r in results:
            name_parts = [r.get("name", "")]
            if r.get("date"):
                name_parts.append(r["date"])
            if r.get("description"):
                name_parts.append(r["description"])
            profile_id = " ".join(name_parts)

            f.write(
                f"{profile_id}\t"
                f"{r.get('x_on', 0):.2f}\t"
                f"{r.get('x_off', 0):.2f}\t"
                f"{r.get('volume_cuyd_per_ft', 0):.3f}\t"
                f"{r.get('contour_location', 0):.2f}\n"
            )

    print(f"\n? BMAP-style Volume Report written to: {file_path}")


def write_cutfill_detailed_report(
    file_path: str,
    *,
    title: str,
    profile1_label: str,
    profile2_label: str,
    x_on: float,
    x_off: float,
    above_datum_cuyd_per_ft: float,
    below_datum_cuyd_per_ft: float,
    total_volume_cuyd_per_ft: float,
    shoreline_from_x: float,
    shoreline_to_x: float,
    shoreline_change: float,
    cells: list[dict],
):
    """
    Writes a BMAP-style 'Cut and Fill Report' including the per-cell table.

    cells: list of dicts with keys:
        - end_x (float)
        - end_z2 (float)
        - cell_vol_cuyd_per_ft (float)
        - cell_thickness_ft (float)
        - cum_vol_cuyd_per_ft (float)
        - gross_vol_cuyd_per_ft (float)
    """
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w") as f:
        f.write(f"{title}\n")
        f.write("Cut and Fill Report\n")
        f.write(f"Profile 1:\t{profile1_label}\t\t\t\t\t\n")
        f.write(f"Profile 2:\t{profile2_label}\t\t\t\t\t\n")
        f.write(f"XOn:\t{x_on:.2f} ft\t\t\t\t\t\n")
        f.write(f"XOff:\t{x_off:.2f} ft\t\t\t\t\t\n")
        f.write("Volume Change:\t\t\t\t\t\t\n")
        f.write(
            f"   Above Datum:\t{above_datum_cuyd_per_ft:.3f} cu. yd/ft\t\t\t\t\t\n"
        )
        f.write(
            f"   Below Datum:\t{below_datum_cuyd_per_ft:.3f} cu.yd/ft\t\t\t\t\t\n"
        )
        f.write(
            f"Total Volume:\t{total_volume_cuyd_per_ft:.3f} cu.yd/ft\t\t\t\t\t\n"
        )

        # Shoreline section
        if (shoreline_from_x == shoreline_from_x) and (
            shoreline_to_x == shoreline_to_x
        ):  # not NaN
            f.write(
                f"Shoreline Change:\t{shoreline_change:.2f} ft\t\t\t\t\t\n"
            )
            f.write(f"   From:\t{shoreline_from_x:.2f} ft\t\t\t\t\t\n")
            f.write(f"   To:\t{shoreline_to_x:.2f} ft\t\t\t\t\t\n")
        else:
            f.write("Shoreline Change:\tN/A\t\t\t\t\t\n")
            f.write("   From:\tN/A\t\t\t\t\t\n")
            f.write("   To:\tN/A\t\t\t\t\t\n")

        f.write("\t\t\t\t\t\t\n")
        f.write("Cell Changes:\t\t\t\t\t\t\n")
        f.write(
            "Cell #\tEnding Distance(ft)\tEnding Elevation(ft)\tCell Volume(cu. yd/ft)\tCell Thickness(ft)\tCumulative Volume(cu. yd/ft)\tGross Volume(cu. yd/ft)\n"
        )

        for i, c in enumerate(cells, start=1):
            f.write(
                f"{i}\t"
                f"{c['end_x']:.2f}\t"
                f"{c['end_z2']:.2f}\t"
                f"{c['cell_vol_cuyd_per_ft']:.3f}\t"
                f"{c['cell_thickness_ft']:.2f}\t"
                f"{c['cum_vol_cuyd_per_ft']:.3f}\t"
                f"{c['gross_vol_cuyd_per_ft']:.3f}\n"
            )


# ---------------------------------------------------------------------
# Bar Properties report (BMAP-style, single specific profile)
# ---------------------------------------------------------------------


def write_bar_properties_report(
    output_path: str,
    title: str,
    reference_label: str,
    specific_label: str,
    xstart: float,
    xend: float,
    min_depth_ft: float,
    min_depth_x_ft: float,
    max_height_ft: float,
    max_height_x_ft: float,
    bar_volume_cuyd_per_ft: float,
    bar_length_ft: float,
    center_of_mass_x_ft: float,
):
    """
    Writes an ASCII report like BMAP's Bar Properties output.

    Notes:
    - Minimum Depth is reported as a positive magnitude (abs of trough elevation).
    - Maximum Height is crestZ - troughZ (ft).
    - Center of Mass is the centroid X of volume (ft).
    """

    def fmt(v, nd=2):
        if v is None:
            return ""
        if isinstance(v, float):
            if np.isnan(v):
                return ""
            return f"{v:.{nd}f}"
        return str(v)

    lines = []
    lines.append(f"{title}".rstrip())
    lines.append("Bar Properties Report")
    lines.append(f"Reference Profile:\t{reference_label}")
    lines.append(f"Specific Profile:\t{specific_label}")
    lines.append(f"Bar XStart:\t{fmt(xstart)} ft")
    lines.append(f"Bar XEnd:\t{fmt(xend)} ft")
    lines.append(f"Minimum Depth:\t{fmt(min_depth_ft)} ft")
    lines.append(f"   Location:\t{fmt(min_depth_x_ft)} ft")
    lines.append(f"Maximum Height:\t{fmt(max_height_ft)} ft")
    lines.append(f"   Location:\t{fmt(max_height_x_ft)} ft")
    lines.append(f"Bar Volume:\t{fmt(bar_volume_cuyd_per_ft, 3)} cu. yd/ft")
    lines.append(f"Bar Length:\t{fmt(bar_length_ft)} ft")
    lines.append(f"Center of Mass:\t{fmt(center_of_mass_x_ft)} ft")

    with open(output_path, "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

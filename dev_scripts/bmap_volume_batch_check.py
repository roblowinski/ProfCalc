# Ensure src/ is in sys.path for imports
import os
import sys
from typing import Any, Dict, Iterable, Optional, Protocol

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from profcalc.common.bmap_io import read_bmap_freeformat  # noqa: E402


class ProfileProtocol(Protocol):
    """Protocol describing the minimal profile object used by this script.

    Attributes:
        x: Sequence or array-like of horizontal coordinates (ft).
        z: Sequence or array-like of elevations (ft).
        name: Profile identifier string (e.g., 'OC100').
    """

    x: Any
    z: Any
    name: str


def bmap_style_volume_above_contour(
    x: Iterable[float],
    z: Iterable[float],
    contour: float,
    dx: float = 10.0,
    debug_profile: Optional[str] = None,
    profile_name: Optional[str] = None,
    xon_override: Optional[float] = None,
    xoff_override: Optional[float] = None,
) -> float:
    """Calculate volume (cu yd/ft) using the legacy BMAP area routine.

    Computes the volume above a specified contour elevation using the same
    computational logic as the legacy BMAP system. This ensures consistency
    when comparing results between the new and legacy implementations.

    Args:
        x: Sequence of horizontal coordinates (ft). Must be array-like and
            correspond element-wise to z values.
        z: Sequence of elevations (ft) corresponding to x coordinates.
        contour: Elevation contour to compute volume above (ft).
        dx: Bin width used by the legacy area calculation routine (ft).
            Defaults to 10.0.
        debug_profile: Optional profile name that triggers detailed debug
            output when it matches the current profile_name.
        profile_name: Optional name of the current profile for debug output.
        xon_override: Optional XOn coordinate override to pass to the legacy
            routine. If None, uses the routine's default logic.
        xoff_override: Optional XOff coordinate override to pass to the legacy
            routine. If None, uses the routine's default logic.

    Returns:
        Volume in cubic yards per foot (cu yd/ft) above the specified contour.

    Notes:
        The legacy BMAP area calculation is imported inside this function to
        avoid loading legacy code at module import time. The area is converted
        to volume by dividing by 27 (cubic feet per cubic yard).
    """
    # Use the robust BMAP logic from ref_scripts
    from ref_scripts.bmap_AreaCalcs import area_above_contour_bmap

    # Pass XOn/XOff if provided
    xon: Optional[float] = xon_override
    xoff: Optional[float] = xoff_override
    area: float = area_above_contour_bmap(
        x, z, contour, dx=dx, xon=xon, xoff=xoff
    )
    if debug_profile and profile_name == debug_profile:
        print(
            f"[DEBUG] Profile {profile_name}: final_area={area}, volume_cuydft={area / 27.0}"
        )
    return area / 27.0  # cu yd/ft


def parse_bmap_report(path: str) -> Dict[str, float]:
    """Parse a BMAP report file and extract profile volume data.

    Reads a legacy BMAP report file and extracts volume calculations for each
    profile. The report format is expected to be tab-delimited with profile
    identifiers starting with 'OC' and volume values in the fourth column.

    Args:
        path: File system path to the BMAP report file (.rpt format).

    Returns:
        Dictionary mapping profile identifiers (e.g., 'OC100') to their
        corresponding volume values (cu yd/ft) as reported by BMAP.

    Raises:
        FileNotFoundError: If the specified report file does not exist.
        ValueError: If volume values cannot be parsed as floats.
    """
    bmap_vols: Dict[str, float] = {}
    with open(path, "r") as f:
        for line in f:
            if line.startswith("OC"):
                parts: list[str] = line.strip().split("\t")
                if len(parts) >= 4:
                    # Extract profile ID (first word in first column)
                    prof: str = parts[0].split()[0]
                    try:
                        vol: float = float(parts[3])
                        bmap_vols[prof] = vol
                    except ValueError:
                        continue
    return bmap_vols


def main() -> None:
    """Execute batch volume validation against legacy BMAP results.

    This script performs end-to-end validation of volume calculations by:
    1. Reading profile data from a BMAP free-format file
    2. Computing volumes above a specified contour using legacy BMAP logic
    3. Comparing computed volumes against values from a legacy BMAP report
    4. Reporting discrepancies and match statistics

    The script uses hardcoded file paths for the BMAP data and report files.
    Volume calculations include XOn/XOff coordinate overrides extracted from
    the BMAP report when available.

    Output:
        Tab-delimited table showing profile name, BMAP volume, calculated
        volume, and difference. Followed by summary statistics of matches
        within tolerance (±0.01 cu yd/ft).
    """
    # Path to the BMAP Free Format file
    bmap_file: str = r"c:/__PROJECTS/Scripts/Python/Coastal/profcalc/data/testing_files/bmap_calcs/OC_2021-2024_Monitoring.dat"
    contour: float = 4.0

    profiles: Iterable[ProfileProtocol] = read_bmap_freeformat(bmap_file)

    # --- Enhancement: Compare to BMAP report ---
    # Path to BMAP legacy report
    bmap_report: str = r"c:/__PROJECTS/Scripts/Python/Coastal/profcalc/data/testing_files/bmap_calcs/ContourLocationTest_BMAP_Results.rpt"

    bmap_vols: Dict[str, float] = parse_bmap_report(bmap_report)

    print("Profile\tBMAP Vol\tCalc Vol\tDiff")
    num_match: int = 0
    num_total: int = 0
    debug_profiles: set[str] = {
        "OC100",
        "OC104",
        "OC110",
        "OC120",
        "OC140",
        "OC150",
    }  # Profiles for detailed debug output
    for p in profiles:
        x = p.x
        z = p.z
        prof = p.name
        debug_profile: Optional[str] = prof if prof in debug_profiles else None
        # Get XOn/XOff from BMAP report if available
        xon: Optional[float] = None
        xoff: Optional[float] = None
        # Parse XOn/XOff from BMAP report line if present
        with open(bmap_report, "r") as f:
            for line in f:
                if line.startswith(prof):
                    parts: list[str] = line.strip().split("\t")
                    if len(parts) >= 3:
                        try:
                            xon = float(parts[1])
                            xoff = float(parts[2])
                        except Exception:
                            pass
                    break
        vol: float = bmap_style_volume_above_contour(
            x,
            z,
            contour,
            debug_profile=debug_profile,
            profile_name=prof,
            xon_override=xon,
            xoff_override=xoff,
        )
        bmap_vol: Optional[float] = bmap_vols.get(prof)
        if bmap_vol is not None:
            diff: float = vol - bmap_vol
            print(f"{prof}\t{bmap_vol:.3f}\t{vol:.3f}\t{diff:+.3f}")
            num_total += 1
            if abs(diff) < 0.01:
                num_match += 1
        else:
            print(f"{prof}\tN/A\t{vol:.3f}\tN/A")
    print(
        f"\nMatched: {num_match}/{num_total} profiles (|diff| < 0.01 cu yd/ft)"
    )


if __name__ == "__main__":
    main()


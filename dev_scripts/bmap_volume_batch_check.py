
# Ensure project root is in sys.path for imports
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


import os
import sys

# Ensure project root is in sys.path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from profcalc.common.bmap_io import read_bmap_freeformat


def bmap_style_volume_above_contour(x, z, contour, dx=10.0, debug_profile=None, profile_name=None, xon_override=None, xoff_override=None):
    # Use the robust BMAP logic from ref_scripts
    from ref_scripts.bmap_AreaCalcs import area_above_contour_bmap
    # Pass XOn/XOff if provided
    xon = xon_override
    xoff = xoff_override
    area = area_above_contour_bmap(x, z, contour, dx=dx, xon=xon, xoff=xoff)
    if debug_profile and profile_name == debug_profile:
        print(f"[DEBUG] Profile {profile_name}: final_area={area}, volume_cuydft={area/27.0}")
    return area / 27.0  # cu yd/ft

# Path to the BMAP Free Format file
bmap_file = r"c:/__PROJECTS/Scripts/Python/Coastal/Profile_Analysis/data/testing_files/bmap_calcs/OC_2021-2024_Monitoring.dat"
contour = 4.0

profiles = read_bmap_freeformat(bmap_file)


# --- Enhancement: Compare to BMAP report ---

# Path to BMAP legacy report
bmap_report = r"c:/__PROJECTS/Scripts/Python/Coastal/Profile_Analysis/data/testing_files/bmap_calcs/ContourLocationTest_BMAP_Results.rpt"

# Parse BMAP report: {profile: volume}

def parse_bmap_report(path):
    bmap_vols = {}
    with open(path, 'r') as f:
        for line in f:
            if line.startswith('OC'):
                parts = line.strip().split('\t')
                if len(parts) >= 4:
                    # Extract profile ID (first word in first column)
                    prof = parts[0].split()[0]
                    try:
                        vol = float(parts[3])
                        bmap_vols[prof] = vol
                    except ValueError:
                        continue
    return bmap_vols

bmap_vols = parse_bmap_report(bmap_report)

print("Profile\tBMAP Vol\tCalc Vol\tDiff")
num_match = 0
num_total = 0
debug_profiles = {"OC100", "OC104", "OC110", "OC120", "OC140", "OC150"}  # Profiles for detailed debug output
for p in profiles:
    x = p.x
    z = p.z
    prof = p.name
    debug_profile = prof if prof in debug_profiles else None
    # Get XOn/XOff from BMAP report if available
    xon = None
    xoff = None
    # Parse XOn/XOff from BMAP report line if present
    with open(bmap_report, 'r') as f:
        for line in f:
            if line.startswith(prof):
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    try:
                        xon = float(parts[1])
                        xoff = float(parts[2])
                    except Exception:
                        pass
                break
    vol = bmap_style_volume_above_contour(x, z, contour, debug_profile=debug_profile, profile_name=prof, xon_override=xon, xoff_override=xoff)
    bmap_vol = bmap_vols.get(prof)
    if bmap_vol is not None:
        diff = vol - bmap_vol
        print(f"{prof}\t{bmap_vol:.3f}\t{vol:.3f}\t{diff:+.3f}")
        num_total += 1
        if abs(diff) < 0.01:
            num_match += 1
    else:
        print(f"{prof}\tN/A\t{vol:.3f}\tN/A")
print(f"\nMatched: {num_match}/{num_total} profiles (|diff| < 0.01 cu yd/ft)")

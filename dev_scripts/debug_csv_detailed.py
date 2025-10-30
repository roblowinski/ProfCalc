"""Debug CSV parsing - detailed tracing."""
import sys

sys.path.insert(0, "src")

from pathlib import Path

# Read file
file_path = Path("data/input_files/3Col_NoHeader__NoID.csv")
lines = file_path.read_text().splitlines()

print(f"Total lines: {len(lines)}")
print("First 3 lines:")
for i, line in enumerate(lines[:3]):
    print(f"  {i}: {line}")

# Simulate parse_csv logic
delimiter = ','
has_header = False
data_start = 0
column_mapping = {}

print(f"\nhas_header: {has_header}")
print(f"data_start: {data_start}")
print(f"column_mapping: {column_mapping}")

# Parse first few lines manually
from profcalc.common.file_parser import (
    _extract_coordinates,
    _extract_profile_id,
)

print(f"\n{'='*80}")
print("Processing first 5 data lines...")
print('='*80)

profiles_dict = {}
for i in range(data_start, min(data_start + 5, len(lines))):
    line = lines[i].strip()
    if not line:
        print(f"Line {i}: EMPTY - skipping")
        continue

    parts = [p.strip() for p in line.split(delimiter)]
    print(f"\nLine {i}: {len(parts)} parts")
    print(f"  Raw: {line[:60]}...")
    print(f"  Parts: {parts}")

    if len(parts) < 3:
        print("  SKIPPED: less than 3 columns")
        continue

    # Extract profile ID
    profile_id = _extract_profile_id(parts, column_mapping)
    print(f"  Profile ID: '{profile_id}'")

    # Extract coordinates
    coord_data = _extract_coordinates(parts, column_mapping)
    print(f"  Coordinates: {coord_data}")

    if coord_data and coord_data.get('x') is not None and coord_data.get('y') is not None:
        print(f"  ✓ Valid coordinates - would add to profile '{profile_id}'")
        if profile_id not in profiles_dict:
            profiles_dict[profile_id] = {"coordinates": []}
        profiles_dict[profile_id]["coordinates"].append(coord_data)
    else:
        print("  ✗ Invalid/missing coordinates - skipping")

print(f"\n{'='*80}")
print(f"Profiles created: {len(profiles_dict)}")
for pid, pdata in profiles_dict.items():
    print(f"  {pid}: {len(pdata['coordinates'])} coordinates")

"""Debug CSV parsing to find why profiles aren't being created."""
import sys

sys.path.insert(0, "src")

from pathlib import Path

from profcalc.common.file_parser import parse_file

# Test with 3-column file
file_path = Path("data/input_files/3Col_NoHeader__NoID.csv")
print(f"Parsing: {file_path}")
print("=" * 80)

parsed = parse_file(file_path, skip_confirmation=True)

print(f"Format: {parsed.format_type}")
print(f"Has header: {parsed.has_header}")
print(f"Column mapping: {parsed.column_mapping}")
print(f"Delimiter: {parsed.delimiter}")
print(f"Profiles found: {len(parsed.profiles)}")
print()

if parsed.profiles:
    print("First profile:")
    prof = parsed.profiles[0]
    print(f"  ID: {prof['profile_id']}")
    print(f"  Coordinates: {len(prof['coordinates'])}")
    if prof['coordinates']:
        print(f"  First coord: {prof['coordinates'][0]}")
        print(f"  Last coord: {prof['coordinates'][-1]}")
else:
    print("NO PROFILES FOUND!")
    print()
    print("Debugging...")

    # Read lines and manually check
    lines = file_path.read_text().splitlines()
    print(f"Total lines in file: {len(lines)}")
    print(f"First line: {lines[0]}")
    print(f"Last line: {lines[-1]}")

    # Try parsing first line manually
    parts = lines[0].split(',')
    print(f"\nFirst line parts: {parts}")
    print(f"Number of parts: {len(parts)}")

    # Check if parts are numeric
    for i, p in enumerate(parts):
        try:
            float(p)
            print(f"  Part {i}: {p} -> NUMERIC")
        except ValueError:
            print(f"  Part {i}: {p} -> NOT NUMERIC")

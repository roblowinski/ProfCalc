"""Test baseline-aware coordinate transformations."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from profcalc.cli.quick_tools.convert import convert_format

print("=" * 70)
print("TEST 1: BMAP→XYZ WITH Origin Azimuth File (Coordinate Transformation)")
print("=" * 70)

convert_format(
    input_file="data/temp/test_bmap_with_baseline.txt",
    output_file="data/temp/test_bmap_to_xyz_with_baseline.xyz",
    from_format="bmap",
    to_format="xyz",
    baselines_file="data/temp/test_baselines.csv",
)

print("\n📄 Output XYZ file with real-world coordinates:")
print("-" * 70)
with open("data/temp/test_bmap_to_xyz_with_baseline.xyz") as f:
    lines = f.readlines()
    for line in lines:
        print(line.rstrip())
print("-" * 70)

print("\n" + "=" * 70)
print("TEST 2: BMAP→CSV WITHOUT Origin Azimuth File (Warning Expected)")
print("=" * 70)

convert_format(
    input_file="data/temp/test_bmap_with_baseline.txt",
    output_file="data/temp/test_bmap_to_csv_no_baseline.csv",
    from_format="bmap",
    to_format="csv",
    baselines_file=None,
)

print("\n📄 Output CSV file (Y coordinates should be 0.0):")
print("-" * 70)
with open("data/temp/test_bmap_to_csv_no_baseline.csv") as f:
    lines = f.readlines()
    for line in lines[:10]:
        print(line.rstrip())
print("-" * 70)

print("\n✅ All baseline tests complete!")
print("\nExpected behavior:")
print(
    "  - Test 1: X and Y coordinates should be transformed to real-world coordinates"
)
print("  - Test 2: Y coordinates should default to 0.0 with a warning message")

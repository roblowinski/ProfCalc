"""Test extra field preservation in conversions."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from profcalc.cli.quick_tools.convert import convert_format

print("=" * 60)
print("TEST 1: CSV→XYZ Conversion with Extra Columns")
print("=" * 60)

convert_format(
    input_file="data/temp/test_extra_columns.csv",
    output_file="data/temp/test_extra_output.xyz",
    from_format="csv",
    to_format="xyz",
)

# Read and display the output
print("\n📄 Output XYZ file content:")
print("-" * 60)
with open("data/temp/test_extra_output.xyz") as f:
    lines = f.readlines()
    for line in lines[:15]:  # Show first 15 lines
        print(line.rstrip())
print("-" * 60)

print("\n=" * 60)
print("TEST 2: XYZ→CSV Conversion (Round-trip)")
print("=" * 60)

convert_format(
    input_file="data/temp/test_extra_output.xyz",
    output_file="data/temp/test_roundtrip.csv",
    from_format="xyz",
    to_format="csv",
)

print("\n📄 Round-trip CSV file content:")
print("-" * 60)
with open("data/temp/test_roundtrip.csv") as f:
    lines = f.readlines()
    for line in lines[:10]:  # Show first 10 lines
        print(line.rstrip())
print("-" * 60)

print("\n=" * 60)
print("TEST 3: CSV→BMAP Conversion (Data Loss Warning)")
print("=" * 60)

convert_format(
    input_file="data/temp/test_extra_columns.csv",
    output_file="data/temp/test_bmap_warning.txt",
    from_format="csv",
    to_format="bmap",
)

print("\n✅ All tests complete!")

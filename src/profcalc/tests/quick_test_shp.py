"""Quick test for shapefile conversion without geopandas."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from profcalc.cli.quick_tools.convert import execute_from_cli

# Test 1: Should show error message about geopandas
print("=" * 60)
print("Test 1: Shapefile export without geopandas (expect error)")
print("=" * 60)

try:
    execute_from_cli(
        [
            "data/input_examples/test_profiles.csv",
            "--to",
            "shp-points",
            "-o",
            "data/temp/test_points.shp",
        ]
    )
except SystemExit:
    pass  # argparse may exit

print("\n" + "=" * 60)
print("Test 2: CSV → CSV conversion (should work)")
print("=" * 60)

try:
    execute_from_cli(
        [
            "data/input_examples/test_profiles.csv",
            "--to",
            "csv",
            "-o",
            "data/temp/test_roundtrip.csv",
        ]
    )
except SystemExit:
    pass

print("\nTest complete!")

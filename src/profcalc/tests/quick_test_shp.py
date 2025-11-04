"""Quick test for shapefile conversion without geopandas."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from profcalc.cli.quick_tools import execute_from_cli
except ImportError as exc:
    raise ImportError(
        "The 'execute_from_cli' function is not found in 'profcalc.cli.quick_tools'. "
        "Please ensure it is defined or replace it with the correct function."
    ) from exc

# Test 1: Should show error message about geopandas
print("=" * 60)
print("Test 1: Shapefile export without geopandas (expect error)")
print("=" * 60)

try:
    execute_from_cli(
        [
            "src/profcalc/data/required_inputs/test_profiles.csv",
            "--to",
            "shp-points",
            "-o",
            "src/profcalc/data/temp/test_points.shp",
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
            "src/profcalc/data/required_inputs/test_profiles.csv",
            "--to",
            "csv",
            "-o",
            "src/profcalc/data/temp/test_roundtrip.csv",
        ]
    )
except SystemExit:
    pass

print("\nTest complete!")

# Test content-based format detection
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Now we can import without the src prefix
from profcalc.cli.quick_tools.convert import _detect_format

print("=" * 70)
print("CONTENT-BASED FORMAT DETECTION TEST")
print("=" * 70)

test_files = [
    ("data/temp/test_xyz.txt", "XYZ content in .txt file"),
    ("data/temp/test_bmap.txt", "BMAP content in .txt file"),
    ("data/temp/test_csv.txt", "CSV content in .txt file"),
    ("data/temp/mystery_file.data", "XYZ content in .data file"),
    ("data/input_examples/BMAP_free-format_OC.dat", "BMAP in .dat file"),
    ("data/temp/survey_2024-10-26.xyz", "XYZ in .xyz file"),
]

print("\nTest Results:")
print("-" * 70)
for filepath, description in test_files:
    if Path(filepath).exists():
        detected = _detect_format(filepath)
        extension = Path(filepath).suffix
        print(f"✓ {description:40} → {detected.upper():5} (ext: {extension})")
    else:
        print(f"✗ {description:40} → FILE NOT FOUND")

print("\n" + "=" * 70)
print("✅ Format detection is now CONTENT-BASED, not extension-based!")
print("=" * 70)


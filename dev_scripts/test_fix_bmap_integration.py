"""
Test the integrated fix_bmap.py with new format detection.

This script tests the fix_bmap tool with different input formats.
"""

from pathlib import Path

from profcalc.cli.quick_tools.fix_bmap import fix_bmap_point_counts


def test_fix_bmap_integration():
    """Test fix_bmap with BMAP format file."""
    print("=" * 70)
    print("TESTING FIX_BMAP INTEGRATION WITH FORMAT DETECTION")
    print("=" * 70)
    print()

    test_files = [
        ("Bmap_FreeFormat.txt", "bmap"),
        ("4Col_WithHeader.csv", "csv_standard"),
        ("9Col_Untouched.dat", "csv_9col"),
    ]

    input_dir = Path(r"C:\__PROJECTS\Scripts\Python\Coastal\Profile_Analysis\data\input_files")
    output_dir = Path(r"C:\__PROJECTS\Scripts\Python\Coastal\Profile_Analysis\data\temp")
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, expected_format in test_files:
        input_file = input_dir / filename
        if not input_file.exists():
            print(f"SKIP: {filename} (file not found)")
            continue

        output_file = output_dir / f"fixed_{filename}"

        print(f"\nTesting: {filename}")
        print(f"Expected Format: {expected_format}")
        print("-" * 70)

        try:
            # Test with skip_confirmation=True for automated testing
            corrections = fix_bmap_point_counts(
                str(input_file),
                str(output_file),
                verbose=True,
                skip_confirmation=True
            )

            if corrections:
                print(f"\n✓ Found {len(corrections)} corrections")
                print(f"✓ Output written to: {output_file.name}")
            else:
                print("\n✓ No corrections needed (all counts accurate)")

        except Exception as e:
            print(f"\n✗ Error: {e}")

        print("=" * 70)


if __name__ == "__main__":
    test_fix_bmap_integration()

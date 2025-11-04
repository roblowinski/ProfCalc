"""
Test duplicate/ambiguous column name detection in CSV files.

Tests edge case where multiple columns match the same coordinate pattern.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from profcalc.cli.quick_tools.convert import convert_format


def test_duplicate_z_columns():
    """Test CSV with both 'z' and 'elevation' columns (both match Z pattern)."""
    test_file = Path("src/profcalc/data/temp/test_duplicate_z.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    # Create CSV with both 'z' and 'elevation' columns
    with test_file.open("w") as f:
        f.write("profile_id,x,y,z,distance,elevation\n")
        f.write("OC117,604523.45,4312567.89,5.67,100.0,5.67\n")
        f.write("OC117,604589.12,4312633.56,4.89,150.0,4.89\n")

    output_file = Path("src/profcalc/data/temp/test_duplicate_z_output.xyz")

    print("Converting CSV with duplicate Z columns (z and elevation)...")
    try:
        convert_format(
            input_file=str(test_file),
            output_file=str(output_file),
            from_format="csv",
            to_format="xyz",
        )
        print("✅ Conversion succeeded (should have warned about ambiguity)")

        # Verify the file was created
        assert output_file.exists(), "Output file should be created"

        # Read output to verify which column was used
        with output_file.open("r", encoding="utf-8") as f:
            content = f.read()
        print(f"\nOutput XYZ content:\n{content}")
        # Should contain the Z values (5.67, 4.89)
        assert "5.67" in content
        assert "4.89" in content

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise


def test_duplicate_x_columns():
    """Test CSV with multiple X coordinate columns (easting and utm_x)."""
    test_file = Path("src/profcalc/data/temp/test_duplicate_x.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    # Create CSV with both 'easting' and 'utm_x' columns
    with test_file.open("w") as f:
        f.write("profile_id,easting,northing,utm_x,utm_y,elevation\n")
        f.write("OC117,604523.45,4312567.89,604500.00,4312500.00,5.67\n")
        f.write("OC117,604589.12,4312633.56,604550.00,4312550.00,4.89\n")

    output_file = Path("src/profcalc/data/temp/test_duplicate_x_output.xyz")

    print("\nConverting CSV with duplicate X columns (easting and utm_x)...")
    try:
        convert_format(
            input_file=str(test_file),
            output_file=str(output_file),
            from_format="csv",
            to_format="xyz",
        )
        print("✅ Conversion succeeded (should have warned about ambiguity)")

        # Read output to verify first match was used (easting)
        with output_file.open("r", encoding="utf-8") as f:
            content = f.read()
        print(f"\nOutput XYZ content:\n{content}")
        # Should use 'easting' column (604523.45), not 'utm_x' (604500.00)
        assert "604523.45" in content
        assert "604589.12" in content

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise


def test_no_duplicate_columns():
    """Test CSV with no duplicate columns (should not warn)."""
    test_file = Path("src/profcalc/data/temp/test_no_duplicates.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    # Create CSV with unique, unambiguous columns
    with test_file.open("w") as f:
        f.write("profile_id,x,y,z\n")
        f.write("OC117,604523.45,4312567.89,5.67\n")
        f.write("OC117,604589.12,4312633.56,4.89\n")

    output_file = Path("src/profcalc/data/temp/test_no_dup_output.xyz")

    print("\nConverting CSV with no duplicate columns...")
    try:
        convert_format(
            input_file=str(test_file),
            output_file=str(output_file),
            from_format="csv",
            to_format="xyz",
        )
        print("✅ Conversion succeeded (no ambiguity warnings expected)")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise


def test_three_way_duplicate():
    """Test CSV with THREE columns all matching same pattern."""
    test_file = Path("src/profcalc/data/temp/test_three_way_dup.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    # Create CSV with z, elevation, AND height (all match Z pattern)
    with test_file.open("w") as f:
        f.write("profile_id,x,y,z,elevation,height\n")
        f.write("OC117,100.0,2000.0,5.0,5.5,6.0\n")
        f.write("OC117,150.0,2050.0,4.0,4.5,5.0\n")

    output_file = Path("src/profcalc/data/temp/test_three_dup_output.xyz")

    print("\nConverting CSV with THREE duplicate Z columns...")
    try:
        convert_format(
            input_file=str(test_file),
            output_file=str(output_file),
            from_format="csv",
            to_format="xyz",
        )
        print("✅ Conversion succeeded (should warn about 3-way ambiguity)")

        # Verify first match was used (z = 5.0, not elevation=5.5 or height=6.0)
        with output_file.open("r", encoding="utf-8") as f:
            content = f.read()
        lines = content.strip().split("\n")
        # Find first data line
        for line in lines:
            if not line.startswith(">") and not line.startswith("#"):
                parts = line.split()
                if len(parts) >= 3:
                    z_value = float(parts[2])
                    print(f"First Z value in output: {z_value}")
                    assert z_value == 5.0, (
                        f"Should use 'z' column (5.0), got {z_value}"
                    )
                    break

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    print("Testing duplicate/ambiguous column detection...\n")
    print("=" * 70)

    try:
        test_duplicate_z_columns()
    except AssertionError as e:
        print(f"\n❌ Test 1 failed: {e}")

    print("\n" + "=" * 70)

    try:
        test_duplicate_x_columns()
    except AssertionError as e:
        print(f"\n❌ Test 2 failed: {e}")

    print("\n" + "=" * 70)

    try:
        test_no_duplicate_columns()
    except AssertionError as e:
        print(f"\n❌ Test 3 failed: {e}")

    print("\n" + "=" * 70)

    try:
        test_three_way_duplicate()
    except AssertionError as e:
        print(f"\n❌ Test 4 failed: {e}")

    print("\n" + "=" * 70)
    print("\nAll duplicate column detection tests completed!")

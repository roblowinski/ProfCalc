"""
Test column count validation for XYZ files with --columns flag.

Tests edge case where --columns specifies indices exceeding available columns.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from profcalc.cli.quick_tools.convert import convert_format


def test_insufficient_columns_with_column_order():
    """Test that validation fails when file has fewer columns than column_order requires."""
    # Create 2-column XYZ file
    test_file = Path("src/profcalc/data/temp/test_2col.xyz")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    with test_file.open("w") as f:
        f.write("# Profile: TestProfile\n")
        f.write("100.0 5.67\n")  # Only 2 columns
        f.write("150.0 4.89\n")

    output_file = Path("src/profcalc/data/temp/test_2col_output.csv")

    # Try to convert with column order requiring 3 columns
    try:
        convert_format(
            input_file=str(test_file),
            output_file=str(output_file),
            from_format="xyz",
            to_format="csv",
            column_order={
                "x": 1,
                "y": 0,
                "z": 2,
            },  # Requires column index 2 (3rd column)
        )
        print("❌ Test failed: Should have raised ValueError")
        assert False, "Expected ValueError for insufficient columns"
    except ValueError as e:
        error_msg = str(e)
        print("✅ Validation correctly rejected insufficient columns")
        print(f"   Error message:\n{error_msg}")

        # Verify error message contains helpful information
        assert "Column count validation failed" in error_msg
        assert "Only 2 column(s) found" in error_msg
        assert "requires 3" in error_msg
        assert "Suggestions:" in error_msg


def test_sufficient_columns_passes():
    """Test that validation succeeds when file has enough columns."""
    # Create 3-column XYZ file
    test_file = Path("src/profcalc/data/temp/test_3col.xyz")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    with test_file.open("w") as f:
        f.write("# Profile: TestProfile\n")
        f.write("100.0 2000.0 5.67\n")
        f.write("150.0 2050.0 4.89\n")

    output_file = Path("src/profcalc/data/temp/test_3col_output.csv")

    # Convert with Y X Z order (still needs all 3 columns)
    try:
        convert_format(
            input_file=str(test_file),
            output_file=str(output_file),
            from_format="xyz",
            to_format="csv",
            column_order={"x": 1, "y": 0, "z": 2},
        )
        print("✅ File with sufficient columns converted successfully")
    except ValueError as e:
        print(f"❌ Test failed: Should not raise ValueError\n{e}")
        assert False, f"Unexpected error: {e}"


def test_default_column_order_with_3_columns():
    """Test that default column order works with standard 3-column files."""
    test_file = Path("src/profcalc/data/temp/test_default_cols.xyz")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    with test_file.open("w") as f:
        f.write("# Profile: TestProfile\n")
        f.write("100.0 2000.0 5.67\n")
        f.write("150.0 2050.0 4.89\n")

    output_file = Path("src/profcalc/data/temp/test_default_output.csv")

    # Convert without specifying column_order (uses default X Y Z)
    try:
        convert_format(
            input_file=str(test_file),
            output_file=str(output_file),
            from_format="xyz",
            to_format="csv",
            # No column_order specified
        )
        print("✅ Default column order works with 3-column file")
    except ValueError as e:
        print(f"❌ Test failed: {e}")
        assert False, f"Unexpected error: {e}"


def test_varying_column_counts():
    """Test file with varying column counts per line."""
    test_file = Path("src/profcalc/data/temp/test_varying_cols.xyz")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    with test_file.open("w") as f:
        f.write("# Profile: TestProfile\n")
        f.write("100.0 2000.0 5.67\n")  # 3 columns
        f.write("150.0 2050.0 4.89 0.05\n")  # 4 columns (extra field)
        f.write("200.0 2100.0\n")  # 2 columns (missing Z) - should warn
        f.write("250.0 2150.0 3.12\n")  # 3 columns

    output_file = Path("src/profcalc/data/temp/test_varying_output.csv")

    # Should pass validation (first line has 3 columns) but warn about line 3
    try:
        convert_format(
            input_file=str(test_file),
            output_file=str(output_file),
            from_format="xyz",
            to_format="csv",
        )
        print(
            "✅ File with varying column counts handled (warns about short lines)"
        )
    except ValueError as e:
        print(f"❌ Test failed: {e}")
        assert False, f"Unexpected error: {e}"


if __name__ == "__main__":
    print("Testing XYZ column count validation...\n")
    print("=" * 70)

    try:
        test_insufficient_columns_with_column_order()
    except AssertionError as e:
        print(f"\n❌ Test 1 assertion failed: {e}")

    print("\n" + "=" * 70)

    try:
        test_sufficient_columns_passes()
    except AssertionError as e:
        print(f"\n❌ Test 2 assertion failed: {e}")

    print("\n" + "=" * 70)

    try:
        test_default_column_order_with_3_columns()
    except AssertionError as e:
        print(f"\n❌ Test 3 assertion failed: {e}")

    print("\n" + "=" * 70)

    try:
        test_varying_column_counts()
    except AssertionError as e:
        print(f"\n❌ Test 4 assertion failed: {e}")

    print("\n" + "=" * 70)
    print("\nAll column validation tests completed!")

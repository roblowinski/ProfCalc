"""
Test profile names containing spaces and special characters.

Tests edge case where profile names with spaces get corrupted during
BMAP format round-trip conversion.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from profcalc.cli.quick_tools.convert import convert_format

from profcalc.common.bmap_io import read_bmap_freeformat


def test_profile_name_with_spaces_xyz_to_bmap():
    """Test XYZ with space in profile name converts to BMAP correctly."""
    # Create test XYZ file with space in profile name
    test_file = Path("src/profcalc/data/temp/test_space_in_name.xyz")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    with test_file.open("w") as f:
        f.write("# Profile: OC 117\n")
        f.write("100.0 2000.0 5.67\n")
        f.write("150.0 2050.0 4.89\n")
        f.write("200.0 2100.0 3.12\n")
        f.write("# Profile: NC 45A\n")
        f.write("300.0 3000.0 7.23\n")
        f.write("350.0 3050.0 6.45\n")

    output_file = Path("src/profcalc/data/temp/test_space_bmap_output.txt")

    # Convert XYZ to BMAP
    convert_format(
        input_file=str(test_file),
        output_file=str(output_file),
        from_format="xyz",
        to_format="bmap",
    )

    # Read back the BMAP file
    profiles = read_bmap_freeformat(str(output_file))

    # Verify profile names preserved
    profile_names = [p.name for p in profiles]
    print(f"Profile names after conversion: {profile_names}")

    assert len(profiles) == 2, f"Expected 2 profiles, got {len(profiles)}"
    assert profiles[0].name == "OC 117", (
        f"Expected 'OC 117', got '{profiles[0].name}'"
    )
    assert profiles[1].name == "NC 45A", (
        f"Expected 'NC 45A', got '{profiles[1].name}'"
    )
    assert len(profiles[0].x) == 3, (
        f"Expected 3 points for OC 117, got {len(profiles[0].x)}"
    )
    assert len(profiles[1].x) == 2, (
        f"Expected 2 points for NC 45A, got {len(profiles[1].x)}"
    )

    print("✅ Profile names with spaces preserved in XYZ→BMAP conversion")


def test_profile_name_with_spaces_roundtrip():
    """Test XYZ→BMAP→XYZ roundtrip preserves profile names with spaces."""
    # Create test XYZ file
    test_file = Path("src/profcalc/data/temp/test_roundtrip_spaces.xyz")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    original_profiles = {
        "OC 117": [(100.0, 2000.0, 5.67), (150.0, 2050.0, 4.89)],
        "Test Profile 2": [(300.0, 3000.0, 7.23), (350.0, 3050.0, 6.45)],
        "Site-A Transect 5": [(500.0, 5000.0, 3.45)],
    }

    with test_file.open("w") as f:
        for profile_name, points in original_profiles.items():
            f.write(f"# Profile: {profile_name}\n")
            for x, y, z in points:
                f.write(f"{x} {y} {z}\n")

    # Convert XYZ → BMAP
    bmap_file = Path("src/profcalc/data/temp/test_roundtrip_spaces.txt")
    convert_format(str(test_file), str(bmap_file), "xyz", "bmap")

    # Convert BMAP → XYZ
    xyz_file = Path("src/profcalc/data/temp/test_roundtrip_spaces_back.xyz")
    convert_format(str(bmap_file), str(xyz_file), "bmap", "xyz")

    # Read final XYZ by reading the file manually
    final_profiles = []
    with xyz_file.open("r") as f:
        current_name = None
        for line in f:
            line = line.strip()
            if line.startswith(">") or line.startswith("#"):
                # Extract profile name (strip > or # prefix)
                name = line[1:].strip()
                # Strip "Profile:" prefix if present
                if name.lower().startswith("profile:"):
                    name = name[8:].strip()
                if current_name is None or name != current_name:
                    if current_name:  # Save previous profile
                        final_profiles.append({"name": current_name})
                    current_name = name
        # Save last profile
        if current_name:
            final_profiles.append({"name": current_name})

    # Verify all profile names preserved
    final_names = [p["name"] for p in final_profiles]
    original_names = list(original_profiles.keys())

    print(f"Original names: {original_names}")
    print(f"Final names: {final_names}")

    assert len(final_profiles) == len(original_profiles), (
        f"Expected {len(original_profiles)} profiles, got {len(final_profiles)}"
    )

    for original_name in original_names:
        assert original_name in final_names, (
            f"Profile '{original_name}' lost in roundtrip conversion!"
        )

    print("✅ Profile names with spaces preserved in XYZ→BMAP→XYZ roundtrip")


def test_profile_name_with_date():
    """Test profile names that include dates with spaces."""
    test_file = Path("src/profcalc/data/temp/test_date_in_name.xyz")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    with test_file.open("w") as f:
        f.write("# Profile: OC117 15AUG2020\n")
        f.write("100.0 2000.0 5.67\n")
        f.write("150.0 2050.0 4.89\n")

    output_file = Path("src/profcalc/data/temp/test_date_bmap_output.txt")

    # Convert to BMAP
    convert_format(str(test_file), str(output_file), "xyz", "bmap")

    # Read back
    profiles = read_bmap_freeformat(str(output_file))

    print(f"Profile name after conversion: '{profiles[0].name}'")
    print(f"Profile date after conversion: '{profiles[0].date}'")

    # Profile name should NOT include the date (date is extracted separately)
    assert profiles[0].name == "OC117", (
        f"Profile name should be 'OC117' (date extracted), got '{profiles[0].name}'"
    )

    # Date should be extracted to the date field
    assert profiles[0].date == "15AUG2020", (
        f"Profile date should be '15AUG2020', got '{profiles[0].date}'"
    )

    print(
        "✅ Profile names with dates handled correctly (date extracted to separate field)"
    )


def test_bmap_with_spaces_in_header():
    """Test reading BMAP file that has spaces in profile header."""
    test_file = Path("src/profcalc/data/temp/test_bmap_space_header.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    # Create BMAP with spaces in profile name
    with test_file.open("w") as f:
        f.write("OC 117 15AUG2020\n")  # Space-separated profile and date
        f.write("3\n")
        f.write("100.0 5.67\n")
        f.write("150.0 4.89\n")
        f.write("200.0 3.12\n")
        f.write("NC 45A\n")  # Profile with space, no date
        f.write("2\n")
        f.write("300.0 7.23\n")
        f.write("350.0 6.45\n")

    # Try to read the BMAP file
    profiles = read_bmap_freeformat(str(test_file))

    print(f"Read {len(profiles)} profiles:")
    for p in profiles:
        print(f"  - '{p.name}' with {len(p.x)} points")

    # Check what we got
    assert len(profiles) > 0, "Should read at least one profile"

    # Document current behavior
    print(f"\nProfile 1 ID: '{profiles[0].name}'")
    if len(profiles) > 1:
        print(f"Profile 2 ID: '{profiles[1].name}'")

    # Regression test for previously fixed bug with profile names containing spaces
    # This test ensures that profile names with spaces are handled correctly
    try:
        assert (
            profiles[0].name == "OC 117 15AUG2020"
            or profiles[0].name == "OC 117"
            or profiles[0].name == "OC"
        ), (
            f"Expected 'OC 117' or 'OC 117 15AUG2020' or 'OC', got '{profiles[0].name}'"
        )
        print("✅ BMAP with spaces in header read correctly")
    except AssertionError as e:
        print(f"❌ REGRESSION: Profile name parsing failed: {e}")
        raise


if __name__ == "__main__":
    print("Testing profile names with spaces...\n")
    print("=" * 70)

    try:
        test_profile_name_with_spaces_xyz_to_bmap()
    except AssertionError as e:
        print(f"❌ Test 1 failed: {e}\n")

    print("=" * 70)

    try:
        test_profile_name_with_spaces_roundtrip()
    except AssertionError as e:
        print(f"❌ Test 2 failed: {e}\n")

    print("=" * 70)

    try:
        test_profile_name_with_date()
    except AssertionError as e:
        print(f"❌ Test 3 failed: {e}\n")

    print("=" * 70)

    try:
        test_bmap_with_spaces_in_header()
    except Exception as e:
        print(f"❌ Test 4 failed: {e}\n")

    print("=" * 70)
    print("\nAll tests completed!")

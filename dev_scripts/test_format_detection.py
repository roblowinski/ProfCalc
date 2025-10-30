"""
Test script to verify format detection and parsing functionality.

Run this to test the new centralized format detection and parsing modules.
"""

from pathlib import Path

from profcalc.common.file_parser import parse_file
from profcalc.common.format_detection import (
    detect_file_format,
    get_format_description,
)


def test_format_detection():
    """Test format detection on sample files."""
    test_files = [
        "Bmap_FreeFormat.txt",
        "Bmap_FreeFormat_JustID.txt",
        "3Col_NoHeader__NoID.csv",
        "4Col_WithHeader.csv",
        "4Col_WithHeader_YX.csv",
        "4Col_WithHeader_Spaces.txt",
        "9Col_WithHeader.csv",
        "9Col_NoHeader.csv",
        "9Col_Untouched.dat",
    ]

    input_dir = Path(r"C:\__PROJECTS\Scripts\Python\Coastal\Profile_Analysis\data\input_files")

    print("=" * 70)
    print("FORMAT DETECTION TEST")
    print("=" * 70)
    print()

    for filename in test_files:
        file_path = input_dir / filename
        if not file_path.exists():
            print(f"SKIP: {filename} (file not found)")
            continue

        try:
            format_type = detect_file_format(file_path)
            description = get_format_description(format_type)
            print(f"✓ {filename}")
            print(f"  Format: {format_type}")
            print(f"  Description: {description}")
            print()
        except Exception as e:
            print(f"✗ {filename}")
            print(f"  Error: {e}")
            print()


def test_file_parsing():
    """Test file parsing on sample files."""
    test_cases = [
        ("Bmap_FreeFormat.txt", "bmap"),
        ("4Col_WithHeader.csv", "csv_standard"),
        ("9Col_Untouched.dat", "csv_9col"),
    ]

    input_dir = Path(r"C:\__PROJECTS\Scripts\Python\Coastal\Profile_Analysis\data\input_files")

    print("=" * 70)
    print("FILE PARSING TEST")
    print("=" * 70)
    print()

    for filename, expected_format in test_cases:
        file_path = input_dir / filename
        if not file_path.exists():
            print(f"SKIP: {filename} (file not found)")
            continue

        try:
            parsed = parse_file(file_path)
            print(f"✓ {filename}")
            print(f"  Format: {parsed.format_type} (expected: {expected_format})")
            print(f"  Profiles: {len(parsed.profiles)}")
            print(f"  Has Header: {parsed.has_header}")

            if parsed.profiles:
                first_profile = parsed.profiles[0]
                print(f"  First Profile ID: {first_profile['profile_id']}")
                print(f"  First Profile Points: {first_profile['actual_point_count']}")

                if parsed.metadata:
                    print(f"  Metadata Keys: {list(parsed.metadata.keys())}")

            print()
        except Exception as e:
            print(f"✗ {filename}")
            print(f"  Error: {e}")
            print()


if __name__ == "__main__":
    test_format_detection()
    print()
    test_file_parsing()

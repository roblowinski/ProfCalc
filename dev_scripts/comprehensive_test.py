"""
Comprehensive testing of fix_bmap integration with format detection.

Tests all sample files in data/input_files to verify:
1. Format detection works correctly
2. Files can be parsed without errors
3. Point count corrections are identified
4. Output files are generated correctly
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from profcalc.common.file_parser import parse_file
from profcalc.common.format_detection import detect_file_format_detailed


def test_format_detection_all_files():
    """Test format detection on all sample files."""
    print("=" * 80)
    print("COMPREHENSIVE FORMAT DETECTION TEST")
    print("=" * 80)
    print()

    input_dir = Path("data/input_files")

    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return

    test_files = sorted(input_dir.glob("*"))

    results = []

    for file_path in test_files:
        if not file_path.is_file():
            continue

        print(f"\n{'=' * 80}")
        print(f"FILE: {file_path.name}")
        print('=' * 80)

        try:
            # Detect format
            detection = detect_file_format_detailed(file_path)

            print(detection.get_summary())

            results.append({
                'file': file_path.name,
                'format': detection.format_type,
                'confidence': detection.confidence,
                'success': True,
                'error': None
            })

        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                'file': file_path.name,
                'format': 'unknown',
                'confidence': 'N/A',
                'success': False,
                'error': str(e)
            })

    # Summary table
    print("\n" + "=" * 80)
    print("DETECTION SUMMARY")
    print("=" * 80)
    print(f"{'File':<30} | {'Format':<15} | {'Confidence':<10} | {'Status':<10}")
    print("-" * 80)

    for result in results:
        status = '✓ Pass' if result['success'] else '✗ Fail'
        print(f"{result['file']:<30} | {result['format']:<15} | {result['confidence']:<10} | {status:<10}")

    print("-" * 80)
    print(f"Total: {len(results)} files | Pass: {sum(1 for r in results if r['success'])} | Fail: {sum(1 for r in results if not r['success'])}")
    print("=" * 80)


def test_parsing_all_files():
    """Test parsing on all sample files."""
    print("\n\n")
    print("=" * 80)
    print("COMPREHENSIVE FILE PARSING TEST")
    print("=" * 80)
    print()

    input_dir = Path("data/input_files")

    test_files = sorted(input_dir.glob("*"))

    results = []

    for file_path in test_files:
        if not file_path.is_file():
            continue

        print(f"\n{'=' * 80}")
        print(f"PARSING: {file_path.name}")
        print('=' * 80)

        try:
            # Parse file (skip confirmation for automated testing)
            parsed = parse_file(file_path, skip_confirmation=True)

            print(f"Format: {parsed.format_type}")
            print(f"Profiles found: {len(parsed.profiles)}")
            print(f"Has header: {parsed.has_header}")

            if parsed.profiles:
                first_profile = parsed.profiles[0]
                print("\nFirst profile:")
                print(f"  - ID: {first_profile['profile_id']}")
                print(f"  - Points: {first_profile['actual_point_count']}")

                # Check for point count discrepancies
                discrepancies = []
                for profile in parsed.profiles:
                    declared = profile.get('point_count', 0)
                    actual = profile['actual_point_count']
                    if declared != actual:
                        discrepancies.append({
                            'id': profile['profile_id'],
                            'declared': declared,
                            'actual': actual
                        })

                if discrepancies:
                    print(f"\n⚠️  Point count discrepancies found: {len(discrepancies)}")
                    for i, disc in enumerate(discrepancies[:5]):  # Show first 5
                        print(f"  - {disc['id']}: {disc['declared']} → {disc['actual']}")
                    if len(discrepancies) > 5:
                        print(f"  ... and {len(discrepancies) - 5} more")
                else:
                    print("\n✓ All point counts accurate")

            print("\n✓ Parsing successful")

            results.append({
                'file': file_path.name,
                'format': parsed.format_type,
                'profiles': len(parsed.profiles),
                'success': True,
                'error': None
            })

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'file': file_path.name,
                'format': 'unknown',
                'profiles': 0,
                'success': False,
                'error': str(e)
            })

    # Summary table
    print("\n" + "=" * 80)
    print("PARSING SUMMARY")
    print("=" * 80)
    print(f"{'File':<30} | {'Format':<15} | {'Profiles':<10} | {'Status':<10}")
    print("-" * 80)

    for result in results:
        status = '✓ Pass' if result['success'] else '✗ Fail'
        print(f"{result['file']:<30} | {result['format']:<15} | {result['profiles']:<10} | {status:<10}")

    print("-" * 80)
    print(f"Total: {len(results)} files | Pass: {sum(1 for r in results if r['success'])} | Fail: {sum(1 for r in results if not r['success'])}")
    print("=" * 80)

    return results


def test_fix_bmap_on_sample():
    """Test fix_bmap integration on a BMAP sample file."""
    print("\n\n")
    print("=" * 80)
    print("FIX_BMAP INTEGRATION TEST")
    print("=" * 80)
    print()

    from profcalc.cli.quick_tools.fix_bmap import fix_bmap_point_counts

    input_file = Path("data/input_files/Bmap_FreeFormat.txt")
    output_dir = Path("data/temp")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "test_bmap_fixed.txt"

    if not input_file.exists():
        print(f"❌ Test file not found: {input_file}")
        return

    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print()

    try:
        # Run fix_bmap with skip_confirmation for automated testing
        corrections = fix_bmap_point_counts(
            str(input_file),
            str(output_file),
            verbose=True,
            skip_confirmation=True
        )

        if corrections:
            print(f"\n✓ Corrections made: {len(corrections)}")
            print(f"✓ Output written to: {output_file}")

            # Verify output file exists
            if output_file.exists():
                print(f"✓ Output file verified (size: {output_file.stat().st_size} bytes)")
            else:
                print("⚠️  Output file not found!")
        else:
            print("\n✓ No corrections needed (all counts accurate)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run all tests
    test_format_detection_all_files()
    parsing_results = test_parsing_all_files()
    test_fix_bmap_on_sample()

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)

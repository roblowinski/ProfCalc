"""Test command-line --columns argument parsing."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from profcalc.cli.quick_tools.convert import _parse_column_order

print("=" * 80)
print("Testing _parse_column_order() function")
print("=" * 80)

# Test cases
test_cases = [
    ("Y X Z", {"x": 1, "y": 0, "z": 2}, "Letter order: Y X Z"),
    ("X Y Z", {"x": 0, "y": 1, "z": 2}, "Letter order: X Y Z (default)"),
    ("Z Y X", {"x": 2, "y": 1, "z": 0}, "Letter order: Z Y X"),
    ("1 0 2", {"x": 1, "y": 0, "z": 2}, "Numeric indices: 1 0 2"),
    ("0 1 2", {"x": 0, "y": 1, "z": 2}, "Numeric indices: 0 1 2 (default)"),
    ("2 1 0", {"x": 2, "y": 1, "z": 0}, "Numeric indices: 2 1 0"),
    ("y x z", {"x": 1, "y": 0, "z": 2}, "Lowercase: y x z"),
]

print("\n✅ Valid test cases:")
for input_str, expected, description in test_cases:
    result = _parse_column_order(input_str)
    status = "✓" if result == expected else "✗"
    print(f"  {status} {description:40} → {result}")
    if result != expected:
        print(f"     Expected: {expected}")
        print(f"     Got:      {result}")

print("\n❌ Invalid test cases (should raise ValueError):")
invalid_cases = [
    ("X Y", "Too few columns"),
    ("X Y Z W", "Too many columns"),
    ("X X Z", "Duplicate coordinate"),
    ("1 1 2", "Duplicate index"),
    ("X Y A", "Invalid coordinate letter"),
    ("3 0 1", "Index out of range"),
    ("X 0 Z", "Mixed letters and numbers"),
]

for input_str, description in invalid_cases:
    try:
        result = _parse_column_order(input_str)
        print(f"  ✗ {description:40} → FAILED (should have raised error)")
    except ValueError as e:
        print(f"  ✓ {description:40} → ValueError: {e}")

print("\n" + "=" * 80)
print("All _parse_column_order() tests complete!")
print("=" * 80)

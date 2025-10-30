"""Debug - check what delimiter is being passed to parse_csv."""
import sys

sys.path.insert(0, "src")

from pathlib import Path

from profcalc.common.format_detection import detect_file_format_detailed

file_path = Path("data/input_files/3Col_NoHeader__NoID.csv")
detection_result = detect_file_format_detailed(file_path)

print("Detection Result:")
print(f"  Format: {detection_result.format_type}")
print(f"  Details: {detection_result.details}")
print(f"  Delimiter key in details: {'delimiter' in detection_result.details}")

if 'delimiter' in detection_result.details:
    delim = detection_result.details['delimiter']
    print(f"  Delimiter value: '{delim}'")
    print(f"  Delimiter type: {type(delim)}")
    print(f"  Delimiter repr: {repr(delim)}")

# Conversion Edge Cases & Known Issues

**Last Updated:** October 2025
**Status:** Most critical issues resolved. This document maintained for historical reference.

## Overview

This document catalogs fringe cases, rare scenarios, and edge conditions that can cause file conversions to fail or produce unexpected results in the Coastal Profile Analysis conversion system.

**Status Legend:**
- ✅ **Fixed** - Issue resolved in current version
- 🔴 **Critical** - Causes data corruption or crashes
- 🟡 **High** - Causes incorrect results or data loss
- 🟢 **Medium** - May cause issues in specific scenarios
- ⚪ **Low** - Minor issues or already handled correctly

---

## ✅ Resolved Issues

### 1. Profile Names with Spaces

**Status:** ✅ FIXED (October 2025)
**Affects:** BMAP format reading/writing

**Problem:**
Profile names containing spaces are corrupted during BMAP round-trip conversion.

**Example:**

```
Input XYZ:
# Profile: OC 117
100.0 2000.0 5.67
150.0 2050.0 4.89

Converts to BMAP:

**Status Legend:**

- ✅ **Fixed** - Issue resolved in current version
- 🔴 **Critical** - Causes data corruption or crashes
- 🟡 **High** - Causes incorrect results or data loss
- 🟢 **Medium** - May cause issues in specific scenarios
- ⚪ **Low** - Minor issues or already handled correctly

---

## ✅ Resolved Issues

### 1. Profile Names with Spaces

**Status:** ✅ FIXED (October 2025)
**Affects:** BMAP format reading/writing

**Problem:**

Profile names containing spaces are corrupted during BMAP round-trip conversion.

**Example:**

```
Input XYZ:
# Profile: OC 117
100.0 2000.0 5.67
150.0 2050.0 4.89

Converts to BMAP:
OC 117
2
100.0 5.67
150.0 4.89

When read back:
Profile name parsed as "OC" (space-delimited split truncates)
```

**Impact:**

- ~~Profile names truncated on round-trip~~ ✅ Fixed
- ~~Data assigned to wrong profiles~~ ✅ Fixed
- ~~Loss of profile identity~~ ✅ Fixed

**Resolution:**

- BMAP parser now correctly handles profile names with spaces
- Uses regex-based parsing instead of simple string split
- Validated with comprehensive test suite: 4 tests passing
- See `test_profile_names_with_spaces.py`

**Workaround (Historical):**

- No longer needed - spaces now fully supported
**Impact:**
- ~~Immediate crash with unhelpful error message~~ ✅ Fixed
- ~~No data validation before processing~~ ✅ Fixed
- ~~Poor user experience~~ ✅ Fixed

**Resolution:**
- Column count validation now performed before parsing
- Clear error messages indicate exact problem
- Errors include file path, line number, and suggestions
- Validated with comprehensive test suite: 4 tests passing
- See `test_column_count_validation.py`

**Workaround (Historical):**
- No longer needed - validation catches this early

---

### 3. Duplicate/Ambiguous Column Names in CSV

**Status:** ✅ FIXED (October 2025)
**Affects:** CSV format with multiple matching columns

**Problem:**
When CSV has multiple columns matching same coordinate pattern, first match is used without warning.

**Example:**

```csv
profile_id,x,y,z,distance,elevation
OC117,604523.45,4312567.89,5.67,100.0,5.67
```

**Current Behavior:**
- Both `z` and `elevation` match Z-coordinate pattern
- Code uses first match (`z`)
- User may expect `elevation` to be used
- Warning now issued when duplicates detected ✅

**Impact:**
- ~~Silent use of potentially wrong column~~ ✅ Fixed (warning added)
- User now informed about which data was converted ✅
- Can verify correct analysis results

**Resolution:**
- Duplicate column detection implemented
- Warning issued showing all matching columns
- Uses first match but informs user
- Validated with comprehensive test suite: 4 tests passing
- See `test_duplicate_columns.py`

**Workaround:**
- Remove duplicate columns before conversion (still recommended)
- Rename columns to be unambiguous (best practice)

---

## 🟡 High Severity Issues

### 4. Mixed Coordinate Systems in Single File

**Status:** 🟡 High - Incorrect Results
**Affects:** CSV and XYZ formats

**Problem:**
Files containing data in multiple coordinate systems (e.g., State Plane + Lat/Lon) process without error but produce invalid output.

**Example:**

```csv
profile_id,easting,northing,elevation
OC117,604523.45,4312567.89,5.67    ← State Plane (feet)
OC118,-82.5432,28.3456,6.12        ← Lat/Lon (degrees)
```

**Current Behavior:**
- All data treated as same coordinate system
- No validation of coordinate ranges
- Mixed units in output file

**Impact:**
- Invalid spatial data
- Incorrect spatial calculations
- Maps show incorrect locations

**Workaround:**
- Separate files by coordinate system
- Convert to common system before processing

**Fix Required:** Medium Priority
- Add coordinate range validation
- Detect and warn about suspicious coordinate ranges
- Document coordinate system requirements

---

### 5. Large Coordinate Values Exceed Format Width

**Status:** 🟡 High - Format Overflow
**Affects:** BMAP format writing

**Problem:**
Very large coordinate values exceed fixed-width format specification in BMAP output.

**Example:**

```python
# BMAP writer uses fixed width:
f.write(f"{x_val:10.2f} {z_val:10.2f}\n")

# Value: 999999999.99
# Format: :10.2f (10 chars total, 2 decimals)
# Result: "999999999.99" (12 chars!)
# → Format overflow, column alignment broken
```

**Impact:**
- BMAP file column alignment broken
- Strict BMAP readers may fail to parse
- Data still readable but poorly formatted

**Workaround:**
- Use coordinate systems with smaller values
- Convert to local coordinates

**Fix Required:** Medium Priority
- Dynamic column width based on data range
- Or use scientific notation for very large values
- Or document coordinate value limits

---

### 6. Missing Baseline Data for Some Profiles

**Status:** 🟡 High - Mixed Coordinates
**Affects:** BMAP to XYZ conversion with baselines

**Problem:**
When converting with `--baselines`, profiles missing from origin azimuth file get Y=0 by default.

**Example:**

```bash
profcalc -c profiles.bmap --to xyz --baselines origins.csv -o output.xyz

Origin azimuth file has: OC117 only
BMAP file has: OC117, OC118

Result:
OC117: Real X,Y,Z coordinates
OC118: X,0,Z coordinates (Y=0 placeholder)
```

**Impact:**
- Mixed coordinate accuracy in output
- Some profiles spatially incorrect
- May cause confusion in analysis

**Workaround:**
- Ensure baseline file contains all profiles
- Or manually filter to profiles with baseline data

**Fix Required:** Medium Priority
- Add flag to fail if any baselines missing
- Or skip profiles without baseline data
- Make Y=0 behavior more explicit

---

### 7. XYZ Files with Only 2 Columns

**Status:** 🟡 High - Data Ignored
**Affects:** XYZ format reading

**Problem:**
XYZ files with only X and Z coordinates (no Y) are silently ignored.

**Example:**

```
# Profile: OC117
100.0 5.67
150.0 4.89
```

**Current Behavior:**

```python
parts = line.split()
if len(parts) >= 3:  # ❌ Requires 3 columns
    # This code never executes for 2-column data
```

**Impact:**
- All data points skipped
- Empty profile created
- No warning to user

**Workaround:**
- Add dummy Y column (0.0) to input files

**Fix Required:** Medium Priority
- Support 2-column XYZ files (X Z format)
- Default Y to 0.0 when missing
- Document 2-column support

---

## 🟢 Medium Severity Issues

### 8. Scientific Notation in XYZ Files

**Status:** 🟢 Medium - May Not Parse
**Affects:** XYZ format reading

**Problem:**
Scientific notation in various formats may not be properly tested.

**Example:**

```
# Formats to test:
1.0e3 2.0e3 5.67      # Standard
1e+03 2e+03 5.67      # With explicit +
1E3 2E3 5.67          # Uppercase E
1.0E+03 2.0E+03 5.67  # Combined
```

**Current Behavior:**

```python
x_val = float(parts[0])  # Python float() should handle all formats
```

**Impact:**
- Most formats likely work (Python float() is robust)
- Edge cases untested
- Potential parsing failures

**Workaround:**
- Use standard decimal notation

**Fix Required:** Low Priority
- Add comprehensive tests for scientific notation
- Document supported formats

---

### 9. Unicode/Special Characters in Profile Names

**Status:** 🟢 Medium - Encoding Errors
**Affects:** All formats

**Problem:**
Profile names with non-ASCII characters may cause encoding errors when writing files.

**Example:**

```csv
profile_id,x,z
OC117–A,100.0,5.67      ← En-dash (U+2013)
OC118—B,150.0,4.89      ← Em-dash (U+2014)
Plage №5,200.0,3.12     ← Numero sign (U+2116)
```

**Current Behavior:**

```python
# May fail if file encoding not UTF-8
f.write(f"{profile.profile_id}\n")  # UnicodeEncodeError?
```

**Impact:**
- File write may fail
- Legacy BMAP readers expecting ASCII may fail
- Cross-platform compatibility issues

**Workaround:**
- Use ASCII-only profile names
- Use underscores/hyphens instead of special characters

**Fix Required:** Low Priority
- Explicitly specify UTF-8 encoding in all file operations
- Add option to sanitize profile names (transliterate)
- Document character encoding requirements

---

### 10. Precision Loss in Conversion Chains

**Status:** 🟢 Medium - Data Degradation
**Affects:** Multiple conversions

**Problem:**
Each conversion may introduce rounding errors that accumulate over multiple conversions.

**Example:**

```bash
# Chain of conversions:
profcalc -c original.csv -o temp1.xyz
profcalc -c temp1.xyz -o temp2.csv
profcalc -c temp2.csv -o temp3.xyz
profcalc -c temp3.xyz -o final.csv
```

**Current Behavior:**

```python
# BMAP/XYZ output uses limited precision:
f.write(f"{x_val:10.2f} {z_val:10.2f}\n")  # 2 decimals only

# Original: 100.12345
# After 4 conversions: 100.12
```

**Impact:**
- Cumulative precision loss
- Data degrades with each conversion
- High-precision measurements lost

**Workaround:**
- Minimize conversion steps
- Keep original files
- Use CSV for intermediate storage (preserves precision)

**Fix Required:** Low Priority
- Document precision limitations
- Consider higher precision in BMAP/XYZ output
- Add flag for high-precision mode

---

### 11. CSV with Unquoted Commas in Fields

**Status:** 🟢 Medium - Parsing Failure
**Affects:** CSV format

**Problem:**
Commas in string fields without proper quoting break CSV parsing.

**Example:**

```csv
profile_id,description,x,z
OC117,Pre-storm, baseline survey,100.0,5.67
```

(Missing quotes around description with comma)

**Current Behavior:**

```python
df = pd.read_csv(filepath)
# Pandas sees 5 columns instead of 4
# Column alignment broken
# Conversion fails with KeyError
```

**Impact:**
- CSV parsing fails
- Unclear error message
- Data corruption if partially parsed

**Workaround:**
- Quote all string fields with commas
- Remove commas from field values

**Fix Required:** Low Priority
- Validate column count consistency
- Provide clear error message about CSV formatting
- Suggest using pandas quoting options

---

## ⚪ Low Severity Issues

### 12. Empty or Whitespace-Only Lines

**Status:** ⚪ Low - Handled Correctly
**Affects:** All text formats

**Problem:**
Lines containing only whitespace might be mishandled.

**Example:**

```
# Profile: OC117
100.0 2000.0 5.67

150.0 2050.0 4.89
```

(Line 3 has spaces/tabs only)

**Current Behavior:**

```python
line = line.strip()  # Whitespace removed
if not line:         # Empty check
    continue         # Skip correctly ✅
```

**Impact:**
- No impact, correctly handled
- Edge cases should be tested

**Workaround:**
- None needed

**Fix Required:** No
- Add tests to verify handling
- Document that empty lines are ignored

---

### 13. Windows vs Unix Line Endings

**Status:** ⚪ Low - Handled Correctly
**Affects:** All text formats

**Problem:**
Files created on different OS may have different line endings.

**Formats:**
- Windows: `\r\n` (CRLF)
- Unix/Linux: `\n` (LF)
- Mac Classic: `\r` (CR)

**Current Behavior:**

```python
with filepath.open('r') as f:
    for line in f:
        line = line.strip()  # Removes all line endings ✅
```

**Impact:**
- Python handles this automatically
- Should work on all platforms

**Workaround:**
- None needed

**Fix Required:** No
- Add cross-platform tests
- Document that all line endings supported

---

### 14. Extra Fields with Variable Length

**Status:** ⚪ Low - Handled But Undefined
**Affects:** CSV format with extra columns

**Problem:**
Extra columns may have missing values for some rows.

**Example:**

```csv
profile_id,x,z,slope,notes
OC117,100.0,5.67,0.05,
OC117,150.0,4.89,0.04,sandy
OC117,200.0,3.12,,gravel
```

**Current Behavior:**

```python
# Pandas fills missing values with NaN
# Extra columns stored in metadata
```

**Impact:**
- Missing values handled by pandas (NaN)
- May cause issues when writing back
- Inconsistent placeholder values

**Workaround:**
- Fill missing values before conversion

**Fix Required:** Low Priority
- Standardize missing value handling
- Document behavior for missing extra fields
- Use consistent placeholder (None, NaN, or empty)

---

### 15. Negative or Mismatched Point Counts in BMAP

**Status:** ⚪ Low - Detection Works
**Affects:** BMAP format

**Problem:**
BMAP files with invalid point counts may not be detected correctly.

**Examples:**

**Negative count:**

```
OC117
-5
100.0 5.67
```

**Mismatched count:**

```
OC117
5
100.0 5.67
150.0 4.89
200.0 3.12
250.0 2.56
300.0 1.89
350.0 0.99
```

(Actual: 6 points, Declared: 5)

**Current Behavior:**
- Negative counts fail format detection (correct)
- Mismatched counts: reads only declared number
- Extra points ignored

**Impact:**
- Negative counts handled correctly
- Mismatched counts cause silent data loss
- No validation of declared vs actual

**Workaround:**
- Fix BMAP files manually
- Use point count fixing tool

**Fix Required:** Low Priority
- Validate point count matches actual data
- Warn if mismatch detected
- Option to auto-correct point counts

---

## 🛠️ Validation & Testing Matrix

### Input Validation Checklist

| Check | Priority | Implemented |
|-------|----------|-------------|
| File exists and readable | Critical | ✅ Yes |
| File encoding is valid | Critical | ❌ No |
| Column count sufficient for column_order | Critical | ❌ No |
| Profile names don't contain spaces | Critical | ❌ No |
| CSV columns unambiguous | Critical | ❌ No |
| Coordinate values in reasonable range | High | ❌ No |
| All baseline profiles present | High | ⚠️ Warning only |
| XYZ has 2 or 3 columns | High | ❌ No (requires 3) |
| BMAP point counts valid | Medium | ⚠️ Partial |
| CSV quoting correct | Medium | ⚠️ Pandas default |
| Scientific notation supported | Low | ✅ Yes |
| Line endings handled | Low | ✅ Yes |

### Test Coverage Status

| Edge Case | Test Exists | Test Passes | Notes |
|-----------|-------------|-------------|-------|
| Profile names with spaces | ❌ No | N/A | **High priority** |
| Column order insufficient | ❌ No | N/A | **High priority** |
| Duplicate column names | ❌ No | N/A | **High priority** |
| Mixed coordinate systems | ❌ No | N/A | Medium priority |
| Large coordinate values | ❌ No | N/A | Medium priority |
| Missing baseline data | ✅ Yes | ✅ Pass | Has warning |
| 2-column XYZ | ❌ No | N/A | Medium priority |
| Scientific notation | ⚠️ Partial | ✅ Pass | Add more cases |
| Unicode profile names | ❌ No | N/A | Low priority |
| Conversion chains | ❌ No | N/A | Low priority |
| Unquoted commas | ❌ No | N/A | Low priority |
| Empty/whitespace lines | ✅ Yes | ✅ Pass | OK |
| Line endings | ⚠️ Partial | ✅ Pass | Add cross-platform |
| Variable-length extras | ⚠️ Partial | ✅ Pass | OK |
| Invalid point counts | ⚠️ Partial | ✅ Pass | Add more cases |

---

## 📋 Recommended Actions

### Immediate (Critical Fixes)

1. **Profile names with spaces** ✅ Planned
   - Update BMAP parser to handle spaces in profile names
   - Add comprehensive tests
   - Document naming restrictions if any remain

2. **Column count validation** ✅ Planned
   - Validate XYZ file has sufficient columns before parsing
   - Provide clear error message with column count info
   - Suggest correct --columns format

3. **Duplicate column detection** ✅ Planned
   - Warn when multiple CSV columns match same pattern
   - Prefer more specific column names
   - Show which column was selected

4. **Error message improvements** ✅ Planned
   - Make all error messages actionable
   - Include file path and line number
   - Suggest fixes or workarounds

### Short-term (High Priority)

5. **Coordinate range validation**
   - Detect suspiciously large/small coordinates
   - Warn about potential mixed coordinate systems
   - Document coordinate system requirements

6. **2-column XYZ support**
   - Allow X Z format (no Y coordinate)
   - Default Y to 0.0 or make required
   - Document 2-column behavior

7. **Large value handling**
   - Dynamic column width in BMAP output
   - Or scientific notation for very large values
   - Document coordinate value limits

### Long-term (Lower Priority)

8. **Input validation framework**
   - Comprehensive pre-flight checks
   - Validation report before conversion
   - Option to proceed with warnings

9. **Enhanced testing**
   - Add tests for all documented edge cases
   - Cross-platform test suite
   - Fuzzing/property-based testing

10. **Documentation**
    - Update user guide with limitations
    - Add troubleshooting section
    - Create FAQ for common issues

---

## 📚 Related Documentation

- `CONVERSION_ENHANCEMENTS.md` - Recent conversion improvements
- `COLUMN_ORDER_SUMMARY.md` - Column ordering and naming
- `README.md` - General usage documentation

---

## 🔄 Version History

- **2025-10-26** - Initial documentation of edge cases
- Future updates will be tracked here

---

## 💡 Contributing

Found a new edge case? Please document it here using this template:

```markdown
### N. Brief Description

**Status:** 🔴/🟡/🟢/⚪ Severity - Impact Type
**Affects:** Format(s) affected

**Problem:**
Clear description of the issue

**Example:**
Code or data example demonstrating the problem

**Current Behavior:**
What actually happens

**Impact:**
User-facing consequences

**Workaround:**
How to avoid the issue now

**Fix Required:** Priority level
- Proposed solution steps
```

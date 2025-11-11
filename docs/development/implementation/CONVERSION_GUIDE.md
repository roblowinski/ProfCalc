# File Conversion Guide

**Last Updated:** October 26, 2025

## Overview

The Coastal Profile Analysis toolkit converts between multiple beach profile data formats with comprehensive validation and error handling.

## Supported Formats

| Format | Extension | Description | Use Case |
|--------|-----------|-------------|----------|
| BMAP | `.txt` | Legacy free-format text | Historical data, BMAP compatibility |
| CSV | `.csv` | Comma-separated values | Spreadsheet analysis, data exchange |
| XYZ | `.xyz`, `.txt` | Space-separated coordinates | GIS import, point clouds |
| Shapefile | `.shp` | ESRI shapefile with 3D geometry | ArcGIS, QGIS, spatial analysis |

## Quick Start

### Basic Conversion

```bash
# Auto-detect formats from extensions
profcalc -c input.txt -o output.csv

# Specify input/output formats explicitly
profcalc -c survey.txt --from bmap --to xyz -o survey.xyz
```

### With Options

```bash
# Custom column order
profcalc -c data.xyz --columns "Y X Z" -o data.csv

# Add baselines for real-world coordinates
profcalc -c survey.bmap --to csv --baselines ProfileOriginAzimuths.csv -o survey.csv

# Export to shapefile
profcalc -c profiles.csv --to shp-points -o points.shp --crs EPSG:6347
```

## Format Details

### BMAP Format

**Structure:**

```
<Profile Name> [Date] [Description]
<Number of Points>
<X1> <Z1>
<X2> <Z2>
...
```

**Example:**

```
OC 117 15AUG2020
5
0.0 5.67
50.0 5.12
100.0 4.89
150.0 4.56
200.0 4.23
```

**Features:**
- Profile name can include spaces (e.g., "OC 117")
- Optional date in DDMMMYYYY format
- Optional description text
- Cross-shore distance (X) and elevation (Z) only
- No Y coordinates (use baselines to calculate)

**Limitations:**
- No metadata beyond name/date/description
- Text-based format (larger file size)
- Limited to 2D cross-shore profiles

### CSV Format

**Structure:**

```csv
profile_id,x,y,z,survey_date,[optional_columns]
<name>,<distance>,<northing>,<elevation>,<date>,...
```

**Example:**

```csv
profile_id,x,y,z,survey_date,slope,sediment
OC117,0.0,2000.0,5.67,2024-10-26,0.05,sand
OC117,50.0,2000.0,5.12,2024-10-26,0.04,sand
```

**Features:**
- Flexible column names (auto-detected)
- Supports extra metadata columns
- Standard spreadsheet format
- Preserves dates, descriptions, and custom fields

**Column Name Detection:**
- X: `x`, `distance`, `cross_shore`, `chainage`
- Y: `y`, `northing`, `easting`, `y_coordinate`
- Z: `z`, `elevation`, `elev`, `height`
- Profile: `profile`, `profile_id`, `profile_name`, `transect`
- Date: `date`, `survey_date`, `survey_date_time`

### XYZ Format

**Structure:**

```
# Profile: <name>
# Date: <date>
# [Optional comment lines]
<X> <Y> <Z>
<X> <Y> <Z>
...
```

**Example:**

```
# Profile: OC 117
# Date: 2024-10-26
0.0 2000.0 5.67
50.0 2000.0 5.12
100.0 2000.0 4.89
```

**Features:**
- Simple space-separated format
- Comment lines start with `#`
- Profile metadata in header comments
- Compatible with GIS point import

**Column Order Customization:**

Default order is `X Y Z`, but you can specify different orders:

```bash
# Easting-Northing-Elevation file
coastal -c survey.xyz --columns "Y X Z" -o survey.csv

# Using column indices (0-indexed)
coastal -c data.txt --columns "1 0 2" -o data.csv
```

### Shapefile Format

See [SHAPEFILE_EXPORT.md](SHAPEFILE_EXPORT.md) for complete documentation.

**Point Shapefile:**
- PointZ geometry (3D points)
- Actual surveyed X, Y, Z coordinates
- All attributes preserved

**Line Shapefile:**
- LineStringZ geometry (3D lines)
- Represents theoretical profile transect
- Requires origin azimuth file

**Requirements:**

```bash
pip install profile-analysis[gis]
```

## Conversion Matrix

| From ↓ To → | BMAP | CSV | XYZ | Shapefile |
|-------------|------|-----|-----|-----------|
| **BMAP** | ✅ | ✅¹ | ✅¹ | ✅¹ |
| **CSV** | ✅ | ✅ | ✅ | ✅² |
| **XYZ** | ✅ | ✅ | ✅ | ✅² |
| **Shapefile** | ❌³ | ❌³ | ❌³ | ➖ |

¹ Requires `--baselines` for Y coordinates
² Point shapefile requires Y coordinates; line shapefile requires baselines
³ Shapefile import not yet implemented

## Common Workflows

### 1. BMAP to CSV with Real-World Coordinates

```bash
# Convert BMAP to CSV with Y coordinates calculated from baselines
profcalc -c survey_2024-10-26.txt \
    --from bmap \
    --to csv \
    --baselines ProfileOriginAzimuths.csv \
    -o survey_2024-10-26.csv
```

**Origin Azimuth File Format:**

```csv
Profile,Origin_X,Origin_Y,Azimuth
OC117,622294.69,461620.86,104.38
NC45A,621947.03,460264.71,104.38
```

### 2. CSV to Shapefile for GIS

```bash
# Export points
profcalc -c profiles.csv \
    --to shp-points \
    -o survey_points.shp \
    --crs EPSG:6347

# Export lines
profcalc -c profiles.csv \
    --to shp-lines \
    --baselines ProfileOriginAzimuths.csv \
    -o survey_lines.shp \
    --crs EPSG:6347
```

### 3. XYZ with Non-Standard Column Order

```bash
# File has: Northing Easting Elevation
profcalc -c survey.xyz \
    --columns "Y X Z" \
    -o survey.csv
```

### 4. Round-Trip Conversion Validation

```bash
# Original → BMAP → CSV → XYZ → BMAP → Validate
profcalc -c original.csv --to bmap -o step1.txt
profcalc -c step1.txt --to csv -o step2.csv --baselines baselines.csv
profcalc -c step2.csv --to xyz -o step3.xyz
profcalc -c step3.xyz --to bmap -o step4.txt

# Compare original.csv with step4.txt (should match)
```

## Validation & Error Handling

### ✅ Automatic Validations

1. **Profile Names with Spaces**
   - Correctly preserved: "OC 117", "Test Profile 2"
   - No truncation or corruption

2. **Column Count Validation**
   - XYZ files verified to have sufficient columns
   - Clear error if `--columns` specifies non-existent columns

3. **Duplicate Column Detection**
   - Warns if CSV has ambiguous columns (e.g., both 'z' and 'elevation')
   - Shows which columns matched
   - Uses first match found

4. **Missing Data**
   - Detects missing Y coordinates
   - Validates origin azimuth file format
   - Checks profile name matches

5. **Coordinate Range Validation**
   - Warns about unusual coordinate values
   - Detects potential coordinate system issues

### Error Messages

All errors include:
- File path and line number
- Actual problematic data
- Explanation of the issue
- Suggested fixes

**Example:**

```
❌ Error in file survey.xyz, line 15:
   Insufficient columns. Expected at least 3 columns (X Y Z), got 2.
   Line content: "100.0 5.67"

   Suggestion: Check if file has Y coordinates or use --columns to specify order.
```

## Troubleshooting

### Issue: "Profile names truncated"

**Symptom:** Profile "OC 117" becomes "OC"

**Solution:** This was fixed in recent updates. Update to latest version.

### Issue: "Column index out of range"

**Symptom:** Crash when using `--columns "Y X Z"` on 2-column file

**Solution:** Verify file has enough columns. The validation now catches this early with a clear error.

### Issue: "Duplicate column 'z' detected"

**Symptom:** Warning about ambiguous columns in CSV

**Solution:** Rename one of the duplicate columns. The tool will use the first match but warns you.

### Issue: "Missing Y coordinates for shapefile export"

**Symptom:** Cannot export to point shapefile

**Solution:**
- For BMAP files: Use `--baselines` to calculate Y from origin and azimuth
- For CSV/XYZ: Ensure file contains Y coordinate column

### Issue: "Profile not found in origin azimuth file"

**Symptom:** Profile skipped during conversion with baselines

**Solution:**
- Check profile name spelling (case-sensitive)
- Verify origin azimuth file has matching profile names
- Check for extra spaces in names

## Advanced Features

### Date Extraction

Dates automatically extracted from:
1. BMAP headers: `OC117 15AUG2020`
2. Filenames: `survey_2024-10-26.xyz` or `survey_20241026.txt`
3. CSV date columns
4. XYZ comment headers: `# Date: 2024-10-26`

### Coordinate Transformations

When using baselines, real-world coordinates calculated as:

```
real_x = origin_x + cross_shore_distance * cos(azimuth_radians)
real_y = origin_y + cross_shore_distance * sin(azimuth_radians)
```

This projects cross-shore measurements onto the theoretical baseline azimuth.

### Extra Field Preservation

CSV and XYZ formats can include extra columns beyond X, Y, Z:
- Slope
- Sediment type
- Quality codes
- Measurement notes

These are:
- ✅ Preserved in CSV ↔ CSV conversions
- ✅ Preserved in XYZ ↔ XYZ conversions
- ✅ Included in shapefile point exports
- ❌ Lost in BMAP conversions (format limitation)

## Performance

**Typical Conversion Times:**

| Operation | File Size | Time |
|-----------|-----------|------|
| BMAP → CSV | 100 profiles | < 1 sec |
| CSV → Shapefile (points) | 50,000 points | 2-3 sec |
| CSV → Shapefile (lines) | 1,000 profiles | 1-2 sec |
| XYZ → BMAP | 500 profiles | < 1 sec |

**Memory Usage:**
- Processes files in memory (not streamed)
- Typical: < 100 MB for large datasets
- Shapefiles: Additional overhead for geopandas

## See Also

- [SHAPEFILE_EXPORT.md](SHAPEFILE_EXPORT.md) - Complete shapefile documentation
- [COLUMN_ORDER_SUMMARY.md](COLUMN_ORDER_SUMMARY.md) - Column order customization
- [VALIDATION_IMPLEMENTATION_SUMMARY.md](VALIDATION_IMPLEMENTATION_SUMMARY.md) - Recent validation fixes
- [FEATURES.md](FEATURES.md) - All features overview

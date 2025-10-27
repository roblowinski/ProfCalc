# Coastal Profile Analysis - Features

**Version:** 1.0
**Last Updated:** October 26, 2025

## Overview

Coastal Profile Analysis is a Python toolkit for working with beach profile survey data. It provides format conversion, validation, GIS export, and analysis capabilities.

## Core Features

### 1. Format Conversion ✅

Convert between multiple beach profile data formats:

**Supported Formats:**

- **BMAP** - Free format text files (legacy format)
- **CSV** - Comma-separated values with flexible column detection
- **XYZ** - Space-separated coordinate files
- **Shapefile** - ESRI shapefiles with 3D geometry (requires geopandas)

**Key Capabilities:**

- Automatic format detection
- Flexible column ordering for XYZ files
- Preserves metadata (dates, descriptions)
- Handles real-world coordinates with baseline transformations

**Usage:**

```bash
# Auto-detect formats
profcalc -c input.txt -o output.csv

# Specify input/output formats explicitly
profcalc -c survey.txt --from bmap --to xyz -o survey.xyz

# Custom column order
profcalc -c data.xyz --columns "Y X Z" -o output.csv

# Add baselines for real-world coordinates
profcalc -c survey.bmap --to csv --baselines ProfileOriginAzimuths.csv -o survey.csv
```

### 2. Shapefile Export ✅

Export beach profile data to ESRI shapefiles for GIS integration.

**Point Shapefiles:**

- PointZ geometry with actual surveyed X, Y, Z coordinates
- Preserves all attribute data
- 3D elevation in geometry

**Line Shapefiles:**

- LineStringZ geometry representing profile transects
- N vertices (N = number of survey points)
- Projected onto theoretical baseline azimuth
- 3D elevation profile for visualization

**Supported Coordinate Systems:**

- EPSG:6347 - NAD83(2011) State Plane New Jersey (feet)
- EPSG:6348 - NAD83(2011) State Plane Delaware (feet)
- EPSG:2272 - NAD83 State Plane Pennsylvania South (feet)
- EPSG:2252 - NAD83 State Plane Maryland (meters)

**Usage:**

```bash
# Export points
profcalc -c profiles.csv --to shp-points -o points.shp --crs EPSG:6347

# Export lines
profcalc -c profiles.csv --to shp-lines -o lines.shp --baselines baselines.csv
```

### 3. Input Validation ✅

Comprehensive validation prevents data corruption and crashes:

**Validations:**

- Profile names with spaces preserved correctly
- Column count verification for XYZ files
- Duplicate column detection in CSV files
- Missing data handling
- Coordinate range validation

**Error Messages:**

- Clear, actionable error messages
- File and line number context
- Suggestions for fixing issues

### 4. Column Order Customization ✅

Flexible column ordering for XYZ files that don't follow standard X Y Z format:

**Options:**

- Named order: `--columns "Y X Z"`
- Index order: `--columns "1 0 2"`
- Supports any permutation of X, Y, Z columns

**Examples:**

```bash
# File has: Northing Easting Elevation
profcalc -c survey.xyz --columns "Y X Z" -o survey.csv

# Using column indices (0-indexed)
profcalc -c data.txt --columns "2 1 0" -o data.csv
```

### 5. Date Handling ✅

Intelligent date parsing and preservation:

**Supported Date Formats:**

- BMAP format: `15AUG2020` (DDMMMYYYY)
- Filename dates: `survey_20241026.xyz`
- CSV date columns
- ISO format: `2024-10-26`

**Features:**

- Automatic date extraction from filenames
- Date preservation across format conversions
- Flexible date format parsing

### 6. Baseline Transformations ✅

Calculate real-world coordinates from cross-shore distances:

**Requirements:**

- Origin azimuth file with origin_x, origin_y, azimuth
- Profile names must match

**Calculation:**

```
real_x = origin_x + distance * cos(azimuth)
real_y = origin_y + distance * sin(azimuth)
```

**Usage:**

```bash
# Convert BMAP to CSV with Y coordinates calculated from baselines
profcalc -c survey.bmap --to csv --baselines ProfileOriginAzimuths.csv -o survey.csv
```

## Command-Line Interface

### Interactive Menu Mode

Launch the interactive menu by running without arguments:

```bash
coastal
```

Features:

- Format conversion
- File inventory
- Point count fixing
- Common bounds detection
- XYZ point assignment

### Quick Command Mode

Run specific operations directly:

```bash
# Convert formats
profcalc -c <input> --to <format> -o <output>

# Find common bounds
profcalc -b <files...> -o <output>

# File inventory
profcalc -i <file> -o <output>

# Assign XYZ points to profiles
profcalc -a <xyz_file> --baselines <baselines> -o <output>

# Fix BMAP point counts
profcalc -f <input> -o <output>
```

## Testing

Comprehensive test suite with 18+ tests:

**Test Coverage:**

- Profile names with spaces
- Column count validation
- Duplicate column detection
- Format conversion roundtrips
- Shapefile export (points and lines)
- Date parsing
- Baseline transformations

**Run Tests:**

```bash
pytest src/profcalc/tests/ -v
```

## Data Formats

### BMAP Format

```
OC 117
5
0.0 5.67
50.0 5.12
100.0 4.89
150.0 4.56
200.0 4.23
```

### CSV Format

```csv
profile_id,x,y,z,survey_date
OC117,0.0,2000.0,5.67,2024-10-26
OC117,50.0,2000.0,5.12,2024-10-26
```

### XYZ Format

```
# Profile: OC 117
# Date: 2024-10-26
0.0 2000.0 5.67
50.0 2000.0 5.12
100.0 2000.0 4.89
```

## Performance

- Handles large datasets (1000+ profiles)
- Fast format conversion (< 1 second for typical files)
- Efficient shapefile export (50,000 points in ~2-3 seconds)

## Limitations

### Known Limitations

1. **Shapefile field names** - Limited to 10 characters (DBF format)
2. **Date precision** - Dates stored as text in shapefiles
3. **BMAP format** - Limited metadata support
4. **2D only** - Currently no 3D surface generation

### Future Enhancements

See [FUTURE_DEVELOPMENT.md](FUTURE_DEVELOPMENT.md) for planned features:

- Volume calculations
- Statistical analysis
- Temporal comparisons
- Additional export formats (GeoJSON, GeoPackage)

## Dependencies

### Core Dependencies

- Python >= 3.10
- numpy
- pandas

### Optional Dependencies

- geopandas >= 0.14.0 (for shapefile export)
- shapely >= 2.0.0
- fiona >= 1.9.0
- pyproj >= 3.6.0

## Platform Support

- ✅ Windows 10/11
- ✅ Linux
- ✅ macOS

## License

See project root for license information.

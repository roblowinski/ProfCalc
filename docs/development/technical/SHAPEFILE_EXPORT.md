# Shapefile Export Feature

## Overview

The coastal profile conversion tool now supports exporting profile data to ESRI shapefiles with 3D geometry support. This enables direct integration with GIS software like ArcGIS Pro, QGIS, and other geospatial tools.

## Installation

Shapefile export requires additional geospatial dependencies. Install with:

```bash
# Option 1: Install with GIS extras
pip install profile-analysis[gis]

# Option 2: Install dependencies manually
pip install geopandas>=0.14.0 shapely>=2.0.0 fiona>=1.9.0 pyproj>=3.6.0
```

## Export Formats

### Point Shapefile (`--to shp-points`)

Creates a **PointZ** shapefile with actual surveyed locations.

**Geometry:**

- Type: PointZ (3D points)
- Coordinates: Actual X, Y, Z from survey data
- Requires Y coordinates in input data

**Attributes:**

- `profile_id`: Profile identifier
- `survey_dat`: Survey date (if available)
- `point_num`: Point number within profile
- `distance_f`: Cross-shore distance in feet
- `z`: Elevation (also stored in geometry)
- Additional fields from CSV (slope, sediment type, etc.)

**Example:**

```bash
# Convert CSV to point shapefile
profcalc -c input.csv --to shp-points -o output.shp

# With coordinate reference system
profcalc -c input.csv --to shp-points -o output.shp --crs EPSG:6348
```

### Line Shapefile (`--to shp-lines`)

Creates a **LineStringZ** shapefile representing the theoretical profile line with 3D elevation data.

**Geometry:**

- Type: LineStringZ (3D polyline)
- Vertices: N vertices where N = number of survey points
- Each vertex located at cross-shore distance of corresponding survey point
- Projected onto theoretical baseline azimuth (ignores GPS drift)
- Z values from actual survey elevations

**Vertex Calculation:**

```
For each survey point at distance X with elevation Z:
  real_x = origin_x + X * cos(azimuth_radians)
  real_y = origin_y + X * sin(azimuth_radians)
  vertex = (real_x, real_y, Z)
```

**Attributes:**

- `profile_id`: Profile identifier
- `survey_dat`: Survey date (if available)
- `azimuth`: Baseline azimuth in degrees
- `length_ft`: Profile length in feet
- `num_vertic`: Number of vertices (equals number of survey points)
- `z_min`: Minimum elevation along profile
- `z_max`: Maximum elevation along profile

**Requirements:**

- Origin azimuth file with `origin_x`, `origin_y`, `azimuth` columns
- Profile names must match between input data and origin azimuth file

**Example:**

```bash
# Convert CSV to line shapefile with baselines
profcalc -c input.csv --to shp-lines -o profiles.shp --baselines ProfileOriginAzimuths.csv

# With coordinate reference system
profcalc -c survey.txt --to shp-lines -o profiles.shp --baselines baselines.csv --crs EPSG:6347
```

## Coordinate Reference Systems

Default CRS: **EPSG:6347** (NAD83(2011) State Plane New Jersey, US Feet)

### Supported CRS Options

| EPSG Code | Description | State | Units |
|-----------|-------------|-------|-------|
| EPSG:6347 | NAD83(2011) State Plane | New Jersey | US Feet |
| EPSG:6348 | NAD83(2011) State Plane | Delaware | US Feet |
| EPSG:2272 | NAD83 State Plane | Pennsylvania South | US Feet |
| EPSG:2252 | NAD83 State Plane | Maryland | Meters |

Specify CRS with `--crs` argument:

```bash
profcalc -c input.csv --to shp-points -o output.shp --crs EPSG:6348
```

## Origin Azimuth File Format

For line shapefile export, an origin azimuth file is required with profile origin coordinates and azimuths.

**Required columns:**

- `profile_id`: Must match profile names in input data
- `origin_x`: X coordinate of profile origin (State Plane)
- `origin_y`: Y coordinate of profile origin (State Plane)
- `azimuth`: Baseline azimuth in degrees (0-360)

**Example origin azimuth file:**

```csv
profile_id,origin_x,origin_y,azimuth
OC117,622294.69,461620.86,104.38
NC45A,621947.03,460264.71,104.38
```

**Coordinate Format:**

- Can include commas in coordinates: `"622,294.69"`
- Automatically parsed and cleaned

## Supported Conversions

All input formats can be converted to shapefiles:

```bash
# BMAP → Shapefile
profcalc -c survey.txt --to shp-points -o points.shp
profcalc -c survey.txt --to shp-lines -o lines.shp --baselines baselines.csv

# CSV → Shapefile
profcalc -c profiles.csv --to shp-points -o points.shp
profcalc -c profiles.csv --to shp-lines -o lines.shp --baselines baselines.csv

# XYZ → Shapefile
profcalc -c survey.xyz --to shp-points -o points.shp
profcalc -c survey.xyz --to shp-lines -o lines.shp --baselines baselines.csv
```

## 3D Geometry Visualization

Both point and line shapefiles contain **true 3D geometry** (Z coordinate in geometry, not just attributes).

**In ArcGIS Pro:**

1. Open shapefile in 3D scene
2. Enable "Elevation from feature" option
3. Z values automatically displayed
4. Use for 3D profile visualization

**In QGIS:**

1. Open shapefile
2. Enable 3D view (View → 3D Map Views)
3. Layer properties → 3D View → Enable terrain following
4. Use "Qgis2threejs" plugin for web-based 3D visualization

## Error Handling

### Missing geopandas

```
❌ Error: Shapefile export requires geopandas.
   Install with: pip install profile-analysis[gis]
   Or: pip install geopandas>=0.14.0
```

**Solution:** Install geopandas using one of the methods shown

### Missing Y coordinates (points)

```
❌ Error: Profile 'OC117' missing Y coordinates.
   Point shapefile export requires Y coordinates in metadata.
```

**Solution:**

- For CSV: Ensure `y` column exists
- For BMAP: Provide baselines with `--baselines` to calculate Y from X and azimuth

### Missing baseline data (lines)

```
❌ Error: Line shapefile export requires an origin azimuth file with origin_x, origin_y, and azimuth.
   Provide with --baselines <file>
```

**Solution:** Provide origin azimuth file using `--baselines` argument

### Profile not in baselines

```
⚠️  Warning: Profile 'TEST123' not found in origin azimuth file - skipping.
```

**Solution:** Add profile to origin azimuth file or check profile name spelling

## Implementation Details

### Point Shapefile

**Module:** `src/profcalc/common/shapefile_io.py`

**Function:** `write_survey_points_shapefile()`

**Logic:**

1. Extract Y coordinates from `profile.metadata['y']`
2. Create PointZ geometry for each (X, Y, Z) triple
3. Build GeoDataFrame with attributes
4. Write to shapefile with specified CRS

**Extra Fields:**

- Automatically included from CSV input
- Example: `slope`, `sediment`, `quality_code`
- Field names truncated to 10 chars (shapefile limitation)

### Line Shapefile

**Module:** `src/profcalc/common/shapefile_io.py`

**Function:** `write_profile_lines_shapefile()`

**Logic:**

1. Extract origin_x, origin_y, azimuth from `profile.metadata`
2. For each survey point at distance X with elevation Z:
   - Calculate real_x = origin_x + X * cos(azimuth)
   - Calculate real_y = origin_y + X * sin(azimuth)
   - Create 3D coordinate (real_x, real_y, Z)
3. Create LineStringZ from all vertices
4. Build GeoDataFrame with profile attributes
5. Write to shapefile with specified CRS

**Vertex Placement:**

- Number of vertices = number of survey points
- Each vertex at cross-shore distance of survey point
- Projected onto theoretical azimuth (straight line)
- Ignores GPS drift in actual Y coordinates
- Preserves elevation profile for 3D visualization

## Use Cases

### 1. GIS Integration

Export coastal profiles directly to ArcGIS or QGIS for:

- Overlay with aerial imagery
- Integration with other GIS layers
- Spatial analysis and queries
- Map production and visualization

### 2. 3D Profile Visualization

Use LineStringZ shapefiles for:

- 3D terrain visualization
- Beach profile evolution animations
- Cross-shore transect analysis
- Elevation change detection

### 3. Spatial Analysis

Point shapefiles enable:

- Buffer analysis around survey points
- Proximity queries
- Spatial joins with other datasets
- Point density analysis

### 4. Data Sharing

Shapefiles are widely supported:

- Universal GIS format
- No specialized software required
- Direct import to web mapping platforms
- Compatible with mobile GIS apps

## Performance

**Point Shapefile:**

- 1000 profiles × 50 points = 50,000 points
- Export time: ~2-3 seconds
- File size: ~5-8 MB

**Line Shapefile:**

- 1000 profiles × 50 vertices = 1000 lines
- Export time: ~1-2 seconds
- File size: ~3-5 MB

## Testing

Test suite: `test_shapefile_conversion.py`

**Tests:**

1. Point shapefile export from CSV
2. Line shapefile export with baselines
3. Integration with convert tool
4. Error handling (missing dependencies, baselines)
5. CRS parameter validation
6. 3D geometry verification

**Run tests:**

```bash
pytest test_shapefile_conversion.py -v
```

## Limitations

1. **Shapefile field names:** Limited to 10 characters (DBF format)
2. **Attribute types:** Limited to string, integer, float (no complex types)
3. **File size:** Shapefiles have 2GB limit (rarely an issue for profile data)
4. **Multi-part features:** Each profile = one feature (not multi-part)
5. **Date format:** Dates stored as text (YYYYMMDD) due to DBF limitations

## Future Enhancements

Potential future additions:

- GeoPackage export (modern alternative to shapefile)
- GeoJSON export (web-friendly format)
- Direct WMS/WFS publishing
- Automatic CRS detection from input coordinates
- Profile attribution from external databases
- Time-series animations (multiple surveys)

## Examples

### Complete Workflow

```bash
# 1. Convert BMAP to CSV (calculate real-world Y coords)
profcalc -c survey_2024-10-26.txt --to csv -o survey.csv --baselines ProfileOriginAzimuths.csv

# 2. Export to point shapefile
profcalc -c survey.csv --to shp-points -o survey_points.shp --crs EPSG:6347

# 3. Export to line shapefile
profcalc -c survey.csv --to shp-lines -o survey_lines.shp --baselines ProfileOriginAzimuths.csv --crs EPSG:6347

# 4. Open in QGIS or ArcGIS Pro
```

### Batch Processing

```bash
# Export all BMAP files to shapefiles
for file in *.txt; do
    profcalc -c "$file" --to shp-lines -o "${file%.txt}_lines.shp" --baselines baselines.csv
done
```

## Troubleshooting

### Issue: "geopandas import error"

**Solution:** Install geopandas: `pip install geopandas>=0.14.0`

### Issue: "CRS not recognized"

**Solution:** Use EPSG code format: `--crs EPSG:6347`

### Issue: "Missing Y coordinates"

**Solution:** For CSV, ensure `y` column exists. For BMAP, provide `--baselines`.

### Issue: "Profile not in origin azimuth file"

**Solution:** Check profile name spelling matches between files (case-sensitive).

### Issue: "Shapefile field names truncated"

**Solution:** Normal behavior - DBF format limits field names to 10 chars.

## References

- [EPSG.io](https://epsg.io/) - CRS reference database
- [GeoPandas Documentation](https://geopandas.org/)
- [Shapely Geometry](https://shapely.readthedocs.io/)
- [ESRI Shapefile Specification](https://www.esri.com/content/dam/esrisites/sitecore-archive/Files/Pdfs/library/whitepapers/pdfs/shapefile.pdf)

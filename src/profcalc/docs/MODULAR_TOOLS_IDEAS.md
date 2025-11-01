# Modular Tools Specification

## Overview

This document defines the generic, reusable calculation tools needed for coastal monitoring analysis. These tools are designed to be:

- **Generic**: Not tied to specific project names, formats, or locations
- **Modular**: Small, focused functions that can be combined
- **Configurable**: Accept parameters for different use cases
- **Composable**: Can be chained together for complex workflows
- **Validated**: Include comparison utilities against manual methods

---

## Tool Categories
### 1. Cross-Sectional Analysis Tools
### 2. Volumetric Calculation Tools
### 3. Shoreline Analysis Tools
### 4. Temporal Comparison Tools
### 5. Statistical Analysis Tools
### 6. Export and Reporting Tools

---

## 1. Cross-Sectional Analysis Tools

### Tool 1.1: `calculate_cross_sectional_area()`

**Purpose:** Calculate area between two elevation bounds using trapezoidal integration

**Function Signature:**

```python
def calculate_cross_sectional_area(
    profile: Profile,
    lower_bound: float,
    upper_bound: float,
    method: str = "trapezoidal"
) -> float:
    """Calculate cross-sectional area between elevation bounds.

    Args:
        profile: Profile object with x (cross-shore) and z (elevation) arrays
        lower_bound: Lower elevation limit (e.g., closure depth)
        upper_bound: Upper elevation limit (e.g., top of berm)
        method: Integration method ("trapezoidal" or "simpson")

    Returns:
        Cross-sectional area in square units (same as input coordinates)

    Raises:
        BeachProfileError: If bounds are invalid or profile insufficient
    """
```

**Algorithm:**
- Clip profile data to elevation bounds
- Apply trapezoidal rule: `A = Σ[(z[i] + z[i+1])/2 * (x[i+1] - x[i])]`
- Handle irregular spacing and missing data

**Usage Example:**

```python
# Area above MHW
area_mhw = calculate_cross_sectional_area(
    profile=surveyed_profile,
    lower_bound=1.58,  # MHW elevation
    upper_bound=15.0   # Top of profile
)

# Area above closure depth
area_closure = calculate_cross_sectional_area(
    profile=surveyed_profile,
    lower_bound=-15.0,  # Closure depth
    upper_bound=15.0    # Top of profile
)
```

---

### Tool 1.2: `compare_profile_areas()`

**Purpose:** Compare cross-sectional areas between two profiles (surveyed vs. template, or temporal)

**Function Signature:**

```python
def compare_profile_areas(
    profile1: Profile,
    profile2: Profile,
    bounds: Dict[str, float]
) -> Dict[str, float]:
    """Compare cross-sectional areas between two profiles.

    Args:
        profile1: First profile (e.g., surveyed condition)
        profile2: Second profile (e.g., design template or previous survey)
        bounds: Dictionary with elevation bounds:
            - 'mhw_elevation': Mean high water
            - 'closure_depth': Depth of closure

    Returns:
        Dictionary with comparison results:
            - 'area1_above_mhw': float
            - 'area2_above_mhw': float
            - 'diff_above_mhw': float (area1 - area2)
            - 'area1_above_closure': float
            - 'area2_above_closure': float
            - 'diff_above_closure': float
            - 'deficit_area': float (if area1 < area2)
            - 'excess_area': float (if area1 > area2)
    """
```

**Usage Example:**

```python
comparison = compare_profile_areas(
    profile1=surveyed_2020,
    profile2=design_template,
    bounds={'mhw_elevation': 1.58, 'closure_depth': -15.0}
)

print(f"Deficit: {comparison['deficit_area']:.0f} sq ft")
print(f"% of Template: {(comparison['area1_above_mhw'] / comparison['area2_above_mhw']) * 100:.1f}%")
```

---

### Tool 1.3: `extract_profile_morphology()`

**Purpose:** Extract key morphological parameters from beach profile

**Function Signature:**

```python
def extract_profile_morphology(
    profile: Profile,
    bounds: Dict[str, float]
) -> Dict[str, Optional[float]]:
    """Extract morphological parameters from beach profile.

    Args:
        profile: Profile object
        bounds: Analysis bounds dictionary

    Returns:
        Dictionary with morphological metrics:
            - 'berm_elevation': float (if identifiable)
            - 'berm_width': float
            - 'beach_face_slope': float (foreshore slope)
            - 'nearshore_slope': float (offshore slope)
            - 'dune_toe_elevation': float
            - 'shoreline_position': float (at reference elevation)
    """
```

---

## 2. Volumetric Calculation Tools

### Tool 2.1: `calculate_volume_between_profiles()`

**Purpose:** Calculate volume between two adjacent profile lines using average-end-area method

**Function Signature:**

```python
def calculate_volume_between_profiles(
    profile1: Profile,
    profile2: Profile,
    alongshore_spacing: float,
    bounds: Dict[str, float],
    apply_wedge_correction: bool = True
) -> Dict[str, float]:
    """Calculate volume between two profiles using average-end-area method.

    Args:
        profile1: First profile
        profile2: Second profile (adjacent alongshore)
        alongshore_spacing: Distance between profiles (ft or m)
        bounds: Elevation bounds for area calculation
        apply_wedge_correction: Apply correction for non-parallel profiles

    Returns:
        Dictionary with volume results:
            - 'volume_above_mhw': float
            - 'volume_above_closure': float
            - 'alongshore_distance': float
            - 'wedge_correction': float (if applied)

    Formula:
        V = [(A₁ + A₂) / 2] × L
        where A₁, A₂ are cross-sectional areas and L is spacing
    """
```

**Usage Example:**

```python
volume = calculate_volume_between_profiles(
    profile1=profiles[0],
    profile2=profiles[1],
    alongshore_spacing=100.0,  # feet
    bounds={'mhw_elevation': 1.58, 'closure_depth': -15.0}
)

print(f"Volume: {volume['volume_above_mhw']:.0f} cu ft")
print(f"         {volume['volume_above_mhw'] / 27:.0f} cu yd")
```

---

### Tool 2.2: `calculate_project_volumes()`

**Purpose:** Calculate total volumes across entire project extent

**Function Signature:**

```python
def calculate_project_volumes(
    profiles: List[Profile],
    profile_spacings: List[float],
    bounds: Dict[str, float]
) -> Dict[str, Any]:
    """Calculate total project volumes by summing profile-to-profile volumes.

    Args:
        profiles: List of profiles in alongshore order
        profile_spacings: List of distances between adjacent profiles
        bounds: Elevation bounds dictionary

    Returns:
        Dictionary with project-wide results:
            - 'total_volume_above_mhw': float (cu ft)
            - 'total_volume_above_closure': float (cu ft)
            - 'total_volume_above_mhw_cuyd': float (cu yd)
            - 'alongshore_extent': float (total distance)
            - 'average_area_per_profile': float
            - 'per_profile_volumes': List[Dict] (detailed results)
    """
```

---

### Tool 2.3: `calculate_template_deficit_volume()`

**Purpose:** Calculate total volume needed to meet design template

**Function Signature:**

```python
def calculate_template_deficit_volume(
    surveyed_profiles: List[Profile],
    template_profiles: Dict[str, Profile],
    profile_spacings: List[float],
    bounds: Dict[str, float]
) -> Dict[str, Any]:
    """Calculate deficit/excess volumes relative to design template.

    Args:
        surveyed_profiles: Current survey profiles
        template_profiles: Design templates keyed by profile name
        profile_spacings: Alongshore distances
        bounds: Elevation bounds

    Returns:
        Dictionary with template comparison results:
            - 'total_deficit_volume': float (cu yd)
            - 'total_excess_volume': float (cu yd)
            - 'net_volume_needed': float (deficit - excess)
            - 'profiles_below_template': int (count)
            - 'profiles_above_template': int (count)
            - 'per_profile_results': List[Dict]
    """
```

---

## 3. Shoreline Analysis Tools

### Tool 3.1: `extract_shoreline_position()`

**Purpose:** Find cross-shore distance where profile crosses target elevation

**Function Signature:**

```python
def extract_shoreline_position(
    profile: Profile,
    target_elevation: float,
    baseline_offset: float = 0.0,
    interpolate: bool = True
) -> Optional[float]:
    """Extract shoreline position at target elevation contour.

    Args:
        profile: Profile object
        target_elevation: Elevation to find (e.g., +4.0 ft NAVD88)
        baseline_offset: Offset from profile origin (default 0.0)
        interpolate: Use linear interpolation between points

    Returns:
        Cross-shore distance from baseline at target elevation,
        or None if elevation not found in profile

    Method:
        - Linear interpolation between bracketing points
        - Handles multiple crossings (returns seaward-most)
    """
```

**Usage Example:**

```python
shoreline_pos = extract_shoreline_position(
    profile=surveyed_profile,
    target_elevation=4.0,  # +4.0 ft NAVD88
    interpolate=True
)

if shoreline_pos:
    print(f"Shoreline at {shoreline_pos:.1f} ft from baseline")
else:
    print("Target elevation not found in profile")
```

---

### Tool 3.2: `calculate_shoreline_metrics()`

**Purpose:** Extract shoreline positions for all profiles and compare to templates

**Function Signature:**

```python
def calculate_shoreline_metrics(
    surveyed_profiles: List[Profile],
    template_profiles: Dict[str, Profile],
    reference_elevation: float
) -> pd.DataFrame:
    """Calculate shoreline positions and offsets for multiple profiles.

    Args:
        surveyed_profiles: List of surveyed profiles
        template_profiles: Design templates keyed by profile name
        reference_elevation: Elevation for shoreline definition

    Returns:
        DataFrame with columns:
            - profile_name: str
            - survey_date: str
            - surveyed_position: float
            - template_position: float
            - offset_from_template: float (positive = seaward)
            - meets_design: bool
            - surveyor: str (from metadata)
    """
```

---

### Tool 3.3: `calculate_shoreline_change_rates()`

**Purpose:** Calculate annual shoreline movement rates from multi-year data

**Function Signature:**

```python
def calculate_shoreline_change_rates(
    shoreline_data: pd.DataFrame,
    date_column: str = 'survey_date',
    position_column: str = 'surveyed_position'
) -> pd.DataFrame:
    """Calculate linear regression rates of shoreline change.

    Args:
        shoreline_data: DataFrame with shoreline positions over time
        date_column: Name of date column
        position_column: Name of position column

    Returns:
        DataFrame with per-profile results:
            - profile_name: str
            - start_position: float
            - end_position: float
            - total_change: float
            - annual_rate: float (ft/year or m/year)
            - trend: str ('erosion', 'accretion', 'stable')
            - r_squared: float (linear fit quality)
            - years_of_data: int
    """
```

---

## 4. Temporal Comparison Tools

### Tool 4.1: `calculate_temporal_area_changes()`

**Purpose:** Calculate cross-sectional area changes between survey dates

**Function Signature:**

```python
def calculate_temporal_area_changes(
    current_profiles: List[Profile],
    previous_profiles: List[Profile],
    bounds: Dict[str, float]
) -> pd.DataFrame:
    """Calculate area changes between two survey dates.

    Args:
        current_profiles: Later survey
        previous_profiles: Earlier survey
        bounds: Elevation bounds

    Returns:
        DataFrame with per-profile changes:
            - profile_name: str
            - current_area_mhw: float
            - previous_area_mhw: float
            - area_change_mhw: float
            - percent_change_mhw: float
            - trend: str ('erosion', 'accretion', 'stable')
            - current_date: str
            - previous_date: str
    """
```

---

### Tool 4.2: `calculate_temporal_volume_changes()`

**Purpose:** Calculate volumetric changes between survey dates

**Function Signature:**

```python
def calculate_temporal_volume_changes(
    current_profiles: List[Profile],
    previous_profiles: List[Profile],
    profile_spacings: List[float],
    bounds: Dict[str, float]
) -> Dict[str, Any]:
    """Calculate project-wide volume changes between surveys.

    Args:
        current_profiles: Later survey
        previous_profiles: Earlier survey
        profile_spacings: Alongshore distances
        bounds: Elevation bounds

    Returns:
        Dictionary with volume change results:
            - 'total_volume_change_mhw': float (cu yd)
            - 'total_volume_change_closure': float (cu yd)
            - 'annual_rate': float (if dates available)
            - 'erosion_volume': float (negative changes)
            - 'accretion_volume': float (positive changes)
            - 'per_profile_changes': List[Dict]
    """
```

---

### Tool 4.3: `calculate_annualized_rates()`

**Purpose:** Calculate annual erosion/accretion rates from multi-year data

**Function Signature:**

```python
def calculate_annualized_rates(
    surveys: Dict[str, List[Profile]],
    profile_spacings: List[float],
    bounds: Dict[str, float]
) -> pd.DataFrame:
    """Calculate annualized volume change rates.

    Args:
        surveys: Dictionary mapping dates to profile lists
            e.g., {'2020-09-01': profiles_2020, '2019-09-01': profiles_2019}
        profile_spacings: Alongshore distances
        bounds: Elevation bounds

    Returns:
        DataFrame with annual rates:
            - period: str (e.g., "2019-2020")
            - start_date: str
            - end_date: str
            - volume_change: float (cu yd)
            - annual_rate: float (cu yd/year)
            - cumulative_change: float (from baseline)
    """
```

---

## 5. Statistical Analysis Tools

### Tool 5.1: `generate_summary_statistics()`

**Purpose:** Calculate summary statistics for reporting

**Function Signature:**

```python
def generate_summary_statistics(
    comparison_results: pd.DataFrame,
    volume_results: Dict[str, Any],
    shoreline_results: pd.DataFrame
) -> Dict[str, Any]:
    """Generate summary statistics for monitoring reports.

    Args:
        comparison_results: Profile-to-template comparison DataFrame
        volume_results: Volumetric analysis results
        shoreline_results: Shoreline metrics DataFrame

    Returns:
        Dictionary with summary metrics:
            - 'pct_meeting_design': float
            - 'avg_deficit_area': float
            - 'max_deficit_profile': str
            - 'total_fill_volume': float
            - 'avg_shoreline_offset': float
            - 'max_erosion_profile': str
            - 'max_erosion_rate': float
            - 'stable_profile_count': int
    """
```

---

### Tool 5.2: `identify_hotspots()`

**Purpose:** Identify erosion or accretion hotspots

**Function Signature:**

```python
def identify_hotspots(
    temporal_changes: pd.DataFrame,
    threshold_percentile: float = 90.0,
    metric: str = 'area_change'
) -> pd.DataFrame:
    """Identify profiles with extreme changes (hotspots).

    Args:
        temporal_changes: DataFrame with change metrics
        threshold_percentile: Percentile for classification (default 90th)
        metric: Column to use for hotspot detection

    Returns:
        DataFrame with hotspot profiles:
            - profile_name: str
            - metric_value: float
            - percentile_rank: float
            - classification: str ('severe_erosion', 'moderate_erosion', etc.)
    """
```

---

## 6. Export and Reporting Tools

### Tool 6.1: `export_shapefile()`

**Purpose:** Export spatial data to ESRI shapefile format for ArcGIS

**Function Signature:**

```python
def export_shapefile(
    data: pd.DataFrame,
    output_path: str,
    geometry_type: str,
    crs: str,
    attribute_mapping: Dict[str, str]
) -> None:
    """Export data to ESRI shapefile with attributes.

    Args:
        data: DataFrame with spatial and attribute data
        output_path: Output shapefile path (e.g., "shorelines.shp")
        geometry_type: "Point", "LineString", or "Polygon"
        crs: Coordinate reference system (e.g., "EPSG:2900")
        attribute_mapping: Map DataFrame columns to shapefile fields
            (handles field name length limits, type conversions)

    Raises:
        BeachProfileError: If export fails
    """
```

**Usage Example:**

```python
export_shapefile(
    data=shoreline_df,
    output_path="output/shapefiles/shoreline_2020.shp",
    geometry_type="Point",
    crs="EPSG:2900",
    attribute_mapping={
        'profile_name': 'PROFILE_ID',
        'survey_date': 'SURVEY_DT',
        'shoreline_position': 'SHORE_POS',
        'offset_from_template': 'TMPL_OFF'
    }
)
```

---

### Tool 6.2: `export_to_excel()`

**Purpose:** Export results to formatted Excel workbook

**Function Signature:**

```python
def export_to_excel(
    data_dict: Dict[str, pd.DataFrame],
    output_path: str,
    sheet_names: Optional[Dict[str, str]] = None,
    formatting: Optional[Dict[str, Any]] = None
) -> None:
    """Export multiple DataFrames to Excel workbook.

    Args:
        data_dict: Dictionary mapping names to DataFrames
        output_path: Output Excel file path
        sheet_names: Optional custom sheet names
        formatting: Optional formatting specifications
            (column widths, number formats, conditional formatting)
    """
```

---

### Tool 6.3: `populate_excel_template()`

**Purpose:** Populate pre-formatted Excel template with calculated results

**Function Signature:**

```python
def populate_excel_template(
    template_path: str,
    output_path: str,
    data_mappings: Dict[str, Union[pd.DataFrame, Dict]]
) -> None:
    """Populate existing Excel template with analysis results.

    Args:
        template_path: Path to formatted Excel template
        output_path: Path for output file
        data_mappings: Dictionary mapping sheet names/ranges to data
            e.g., {'CrossSectional': df1, 'Volumetric': df2}

    Notes:
        - Preserves existing formatting
        - Handles named ranges
        - Updates formulas and charts automatically
    """
```

---

## Tool Composition Examples

### Example 1: Complete Profile Analysis

```python
# Load data
profile = read_csv_profiles("data/R01_2020.csv")[0]
template = read_csv_profiles("data/R01_template.csv")[0]
bounds = {'mhw_elevation': 1.58, 'closure_depth': -15.0}

# Cross-sectional analysis
area_comparison = compare_profile_areas(profile, template, bounds)

# Morphology extraction
morphology = extract_profile_morphology(profile, bounds)

# Shoreline position
shoreline = extract_shoreline_position(profile, target_elevation=4.0)

# Combine results
results = {
    **area_comparison,
    **morphology,
    'shoreline_position': shoreline
}
```

### Example 2: Multi-Year Temporal Analysis

```python
# Load multiple years
surveys = {
    '2020': read_csv_profiles("data/2020_profiles.csv"),
    '2019': read_csv_profiles("data/2019_profiles.csv"),
    '2018': read_csv_profiles("data/2018_profiles.csv")
}

# Calculate temporal changes
area_changes = calculate_temporal_area_changes(
    surveys['2020'], surveys['2019'], bounds
)

volume_changes = calculate_temporal_volume_changes(
    surveys['2020'], surveys['2019'], spacings, bounds
)

# Calculate rates
annual_rates = calculate_annualized_rates(surveys, spacings, bounds)

# Identify hotspots
hotspots = identify_hotspots(area_changes, threshold_percentile=90)
```

### Example 3: Complete Workflow with Export

```python
# Analysis
template_deficit = calculate_template_deficit_volume(
    surveyed_profiles, templates, spacings, bounds
)

shoreline_metrics = calculate_shoreline_metrics(
    surveyed_profiles, templates, reference_elevation=4.0
)

summary_stats = generate_summary_statistics(
    comparison_df, volume_results, shoreline_metrics
)

# Export
export_shapefile(
    shoreline_metrics,
    "output/shorelines.shp",
    geometry_type="Point",
    crs="EPSG:2900",
    attribute_mapping=SHORELINE_ATTRS
)

export_to_excel(
    {
        'Areas': comparison_df,
        'Volumes': volume_df,
        'Shorelines': shoreline_metrics
    },
    output_path="output/monitoring_results.xlsx"
)
```

---

## Implementation Notes

### Code Organization
- Place all tools in `src/profcalc/tools/monitoring/`
- Group related functions into modules:
  - `cross_sectional.py` - Area calculations
  - `volumetric.py` - Volume calculations
  - `shoreline.py` - Shoreline extraction and analysis
  - `temporal.py` - Temporal comparison functions
  - `statistics.py` - Summary statistics and hotspot detection
  - `export.py` - Data export utilities

### Dependencies
- **NumPy**: Numerical calculations and array operations
- **Pandas**: Tabular data manipulation
- **SciPy**: Statistical functions (linear regression)
- **GeoPandas**: Shapefile export
- **OpenPyXL**: Excel file manipulation

### Error Handling
- All functions use `BeachProfileError` with appropriate categories
- Validate inputs before processing
- Log warnings for edge cases (e.g., shoreline not found)
- Provide helpful error messages for debugging

### Performance
- Use vectorized NumPy operations where possible
- Consider parallel processing for profile-to-profile calculations
- Cache intermediate results for repeated analyses

### Testing
- Unit tests for each tool with known inputs/outputs
- Integration tests for composed workflows
- Comparison tests against manual BMAP/Excel calculations
1. Implement core cross-sectional tools first (foundation)
3. Implement shoreline analysis (parallel development)
See `src/profcalc/modules/` for existing tools.
5. Develop export utilities
6. Create validation framework (compare against manual methods)

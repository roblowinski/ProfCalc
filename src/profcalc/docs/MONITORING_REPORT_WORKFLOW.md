# Monitoring Report Analysis Workflow

## Overview

This document outlines the sequential steps needed to replicate the analysis results presented in coastal monitoring reports (e.g., Ocean City/Peck Beach Annual Monitoring Report). The workflow is designed to be generic and applicable to beach nourishment monitoring projects.

## Workflow Architecture

```menu
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 1: DATA INGESTION                  │
│  • Import survey data (CSV, BMAP, 9-column, XYZ)            │
│  • Load design templates                                    │
│  • Load analysis configuration (bounds, parameters)         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              PHASE 2: CROSS-SECTIONAL ANALYSIS              │
│  • Calculate areas (above MHW, above closure depth)         │
│  • Compare surveyed vs. template profiles                   │
│  • Compare year-to-year profile changes                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌───────────────────────────┐     ┌───────────────────────────┐
│ PHASE 3: VOLUMETRIC       │     │ PHASE 4: SHORELINE        │
│         ANALYSIS          │     │         ANALYSIS          │
│  • Profile-to-profile     │     │  • Extract positions      │
│    volume calculations    │     │  • Calculate offsets      │
│  • Average-end-area       │     │  • Generate shapefiles    │
│    method                 │     │  • Attribute tables       │
│  • Project totals         │     │                           │
│  • Template comparison    │     │                           │
└───────────────────────────┘     └───────────────────────────┘
        │                                       │
        └───────────────────┬───────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               PHASE 5: REPORT GENERATION                    │
│  • Summary tables (volumetric changes, template deficit)    │
│  • Spatial data export (shapefiles for ArcGIS)              │
│  • Statistical summaries                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Data Ingestion

### Step 1.1: Import Survey Data

**Input Files:**

- Annual beach profile surveys (CSV, BMAP, 9-column, or XYZ format)
- Multiple years for temporal analysis

**Actions:**

```python
from profcalc.common import (
    read_csv_profiles,
    read_bmap_profiles,
    read_9col_profiles,
    read_xyz_profiles
)

# Load survey data for multiple years
survey_2020 = read_csv_profiles("src/profcalc/data/surveys/2020_beach_profiles.csv")
survey_2019 = read_csv_profiles("src/profcalc/data/surveys/2019_beach_profiles.csv")
survey_2018 = read_csv_profiles("src/profcalc/data/surveys/2018_beach_profiles.csv")
```

**Validation:**

- Verify all expected profile lines are present
- Check coordinate validity and coverage
- Confirm data completeness (no missing sections)

### Step 1.2: Load Design Templates

**Input Files:**

- Design template profiles (same format as survey data)
- Templates define target beach configuration

**Actions:**

```python
# Load pre-defined design templates
templates = read_csv_profiles("src/profcalc/data/templates/design_profiles.csv")

# Create lookup dictionary
template_dict = {profile.name: profile for profile in templates}
```

**Notes:**

- Templates are user-provided (not generated by code)
- One template per profile line
- Templates should match profile naming convention

### Step 1.3: Load Analysis Configuration

**Input Files:**

- `config/analysis_bounds.json` - Analysis elevation bounds and parameters

**Configuration Structure:**

```json
{
  "project_name": "Ocean City/Peck Beach",
  "mhw_elevation": 1.58,
  "closure_depth": -15.0,
  "reference_shoreline_elevation": 4.0,
  "units": "feet",
  "vertical_datum": "NAVD88",
  "horizontal_datum": "NAD83",
  "coordinate_system": "NJ State Plane"
}
```

**Actions:**

```python
from profcalc.common import load_analysis_bounds

bounds = load_analysis_bounds("config/analysis_bounds.json")
```

### Step 1.4: Load Profile Metadata

**Input Files:**

-- `src/profcalc/data/profile_spacings.csv` - Alongshore distances between profiles
-- `src/profcalc/data/required_inputs/ProfileOriginAzimuths.csv` - Profile baseline coordinates and orientations

**Profile Spacings Format:**

```csv
profile_from,profile_to,alongshore_distance_ft
R01,R02,100.0
R02,R03,100.0
R03,R04,150.0
```

**Actions:**

```python
import pandas as pd

# Load profile spacing data
spacings_df = pd.read_csv("src/profcalc/data/profile_spacings.csv")
spacings = spacings_df['alongshore_distance_ft'].values
```

---

## Phase 2: Cross-Sectional Analysis

### Step 2.1: Calculate Cross-Sectional Areas

**Objective:** Calculate area between elevation bounds using existing BMAP integration tools

**Key Calculations:**

1. **Area above MHW** (subaerial beach)
2. **Area above closure depth** (entire active profile)

**Actions:**

```python
from profcalc.tools.bmap import calculate_cross_sectional_area

# For each surveyed profile
for profile in survey_2020:
    # Area above MHW
    area_mhw = calculate_cross_sectional_area(
        profile,
        lower_bound=bounds['mhw_elevation'],
        upper_bound=max(profile.z)  # Top of profile
    )

    # Area above closure depth
    area_closure = calculate_cross_sectional_area(
        profile,
        lower_bound=bounds['closure_depth'],
        upper_bound=max(profile.z)
    )
```

**Integration Method:**

- Trapezoidal rule for area under curve
- Handle irregular spacing between points
- Account for profile endpoints

### Step 2.2: Compare Surveyed vs. Template Profiles

**Objective:** Calculate deficit/excess areas relative to design template

**Actions:**

```python
from profcalc.tools.monitoring import compare_profile_to_template

results = []
for profile in survey_2020:
    template = template_dict[profile.name]

    comparison = compare_profile_to_template(
        surveyed=profile,
        template=template,
        bounds=bounds
    )

    results.append({
        'profile_name': profile.name,
        'area_surveyed_above_mhw': comparison['area_surveyed_above_mhw'],
        'area_template_above_mhw': comparison['area_template_above_mhw'],
        'deficit_area': comparison['deficit_area'],
        'excess_area': comparison['excess_area']
    })

# Convert to DataFrame for analysis
import pandas as pd
comparison_df = pd.DataFrame(results)
```

**Output Table Format:**

```
Profile | Surveyed Area | Template Area | Deficit | Excess | % of Template
--------|---------------|---------------|---------|--------|---------------
R01     | 1250.5        | 1500.0        | 249.5   | 0.0    | 83.4%
R02     | 1550.2        | 1500.0        | 0.0     | 50.2   | 103.3%
...
```

### Step 2.3: Year-to-Year Profile Comparison

**Objective:** Calculate cross-sectional area changes between surveys

**Actions:**

```python
from profcalc.tools.monitoring import calculate_temporal_changes

# Compare 2020 vs 2019
changes_df = calculate_temporal_changes(
    current_survey=survey_2020,
    previous_survey=survey_2019,
    bounds=bounds
)
```

**Output Table Format:**

```
Profile | Area 2020 | Area 2019 | Change (sq ft) | Change (%) | Trend
--------|-----------|-----------|----------------|------------|----------
R01     | 1250.5    | 1300.2    | -49.7          | -3.8%      | Erosion
R02     | 1550.2    | 1480.5    | +69.7          | +4.7%      | Accretion
...
```

---

## Phase 3: Volumetric Analysis

### Step 3.1: Profile-to-Profile Volume Calculation

**Objective:** Convert cross-sectional areas to volumes using average-end-area method

**Method:**

```
Volume = (Area₁ + Area₂) / 2 × Distance
```

**Actions:**

```python
from profcalc.tools.monitoring import calculate_volume_between_profiles

volumes = []
for i in range(len(survey_2020) - 1):
    profile1 = survey_2020[i]
    profile2 = survey_2020[i + 1]
    spacing = spacings[i]

    vol_result = calculate_volume_between_profiles(
        profile1=profile1,
        profile2=profile2,
        alongshore_spacing=spacing,
        bounds=bounds
    )

    volumes.append({
        'profile_pair': f"{profile1.name}-{profile2.name}",
        'volume_above_mhw': vol_result['volume_above_mhw'],
        'volume_above_closure': vol_result['volume_above_closure'],
        'alongshore_distance': spacing
    })

volumes_df = pd.DataFrame(volumes)
```

### Step 3.2: Project-Wide Volume Totals

**Objective:** Sum volumes across entire project extent

**Actions:**

```python
from profcalc.tools.monitoring import calculate_project_totals

project_results = calculate_project_totals(
    surveyed_profiles=survey_2020,
    template_profiles=template_dict,
    profile_spacings=spacings,
    bounds=bounds
)

print(f"Total Volume Above MHW: {project_results['total_surveyed_volume_above_mhw']:,.0f} cu yd")
print(f"Template Volume: {project_results['total_template_volume_above_mhw']:,.0f} cu yd")
print(f"Deficit Volume: {project_results['total_deficit_volume']:,.0f} cu yd")
print(f"Alongshore Extent: {project_results['alongshore_extent_ft']:,.0f} ft")
```

### Step 3.3: Temporal Volume Changes

**Objective:** Calculate volumetric changes between survey years

**Actions:**

```python
# Calculate volume changes between years
vol_change_2020_2019 = calculate_volume_changes(
    current_survey=survey_2020,
    previous_survey=survey_2019,
    profile_spacings=spacings,
    bounds=bounds
)

# Calculate annualized rates
surveys = {
    '2020-09-01': survey_2020,
    '2019-09-01': survey_2019,
    '2018-09-01': survey_2018
}

annual_rates = calculate_annualized_rates(surveys, spacings, bounds)
```

**Output Table Format:**

```
Period        | Volume Change | Annual Rate | Cumulative Since Baseline
              | (cu yd)       | (cu yd/yr)  | (cu yd)
--------------|---------------|-------------|---------------------------
2019-2020     | -12,500       | -12,500     | -45,000
2018-2019     | -15,200       | -15,200     | -32,500
2017-2018     | -17,300       | -17,300     | -17,300
```

---

## Phase 4: Shoreline Analysis (Parallel Track)

### Step 4.1: Extract Shoreline Positions

**Objective:** Find cross-shore distance where profile crosses reference elevation (+4.0 ft NAVD88)

**Actions:**

```python
from profcalc.tools.monitoring import extract_shoreline_position

shoreline_data = []
for profile in survey_2020:
    position = extract_shoreline_position(
        profile=profile,
        target_elevation=bounds['reference_shoreline_elevation']
    )

    if position is not None:
        shoreline_data.append({
            'profile_name': profile.name,
            'survey_date': profile.date,
            'shoreline_position': position,
            'baseline_x': 0.0  # Profile baseline
        })

shoreline_df = pd.DataFrame(shoreline_data)
```

### Step 4.2: Calculate Shoreline Offsets from Template

**Objective:** Compare surveyed shoreline to design template shoreline

**Actions:**

```python
from profcalc.tools.monitoring import calculate_shoreline_metrics

shoreline_metrics = calculate_shoreline_metrics(
    surveyed_profiles=survey_2020,
    template_profiles=template_dict,
    reference_elevation=bounds['reference_shoreline_elevation']
)
```

**Output Table Format:**

```
Profile | Surveyed Pos | Template Pos | Offset   | Direction | Meets Design
--------|--------------|--------------|----------|-----------|-------------
R01     | 245.5        | 275.0        | -29.5    | Landward  | No
R02     | 285.2        | 275.0        | +10.2    | Seaward   | Yes
...
```

### Step 4.3: Generate Shoreline Shapefiles for ArcGIS

**Objective:** Create spatial data files with attributes for GIS visualization

**Actions:**

```python
from profcalc.tools.monitoring import export_shoreline_shapefile

# Export shoreline positions as point shapefile
export_shoreline_shapefile(
    shoreline_df=shoreline_metrics,
    output_path="output/shapefiles/shoreline_2020.shp",
    crs="EPSG:2900",  # NJ State Plane
    attributes=[
        'profile_name',
        'survey_date',
        'shoreline_position',
        'template_position',
        'offset_from_template',
        'meets_design',
        'surveyor',
        'project_name'
    ]
)
```

**Shapefile Attributes:**

- `profile_id` (TEXT) - Profile line identifier
- `survey_dt` (DATE) - Survey date
- `shore_pos` (FLOAT) - Shoreline position (ft from baseline)
- `tmpl_pos` (FLOAT) - Template shoreline position
- `offset` (FLOAT) - Offset from template (ft)
- `design_ok` (INTEGER) - Meets design criteria (1=Yes, 0=No)
- `surveyor` (TEXT) - Surveying organization
- `proj_name` (TEXT) - Project name

### Step 4.4: Multi-Year Shoreline Change Analysis

**Objective:** Track shoreline movement over time

**Actions:**

```python
# Combine multiple years
all_shorelines = pd.concat([
    shoreline_df_2020,
    shoreline_df_2019,
    shoreline_df_2018
])

# Calculate change rates
from profcalc.tools.monitoring import calculate_shoreline_change_rates

change_rates = calculate_shoreline_change_rates(
    shoreline_data=all_shorelines,
    profile_names=['R01', 'R02', 'R03', ...]
)
```

**Output Table Format:**

```
Profile | 2018 Pos | 2019 Pos | 2020 Pos | Annual Rate | Trend     | R²
--------|----------|----------|----------|-------------|-----------|------
R01     | 265.5    | 255.2    | 245.5    | -10.0 ft/yr | Erosion   | 0.98
R02     | 270.3    | 278.5    | 285.2    | +7.5 ft/yr  | Accretion | 0.95
...
```

---

## Phase 5: Report Generation

### Step 5.1: Summary Tables

**Tables to Generate:**

1. **Cross-Sectional Area Summary**

```python
from profcalc.tools.monitoring import generate_area_summary_table

area_table = generate_area_summary_table(
    comparison_df=comparison_df,
    output_format='excel'
)
area_table.to_excel("output/tables/cross_sectional_areas_2020.xlsx", index=False)
```

2. **Volumetric Change Summary**

```python
volume_table = generate_volume_summary_table(
    volumes_df=volumes_df,
    temporal_changes=vol_change_2020_2019,
    output_format='excel'
)
volume_table.to_excel("output/tables/volumetric_changes_2020.xlsx", index=False)
```

3. **Project Totals Summary**

```python
totals_table = generate_project_totals_table(
    project_results=project_results,
    output_format='excel'
)
totals_table.to_excel("output/tables/project_totals_2020.xlsx", index=False)
```

### Step 5.2: Export to Formatted Excel Templates

**Objective:** Populate pre-formatted Excel workbooks with calculated results

**Actions:**

```python
from profcalc.tools.monitoring import populate_excel_template

# Load existing formatted template
template_wb = "templates/monitoring_report_template.xlsx"

# Populate with results
populate_excel_template(
    template_path=template_wb,
    output_path="output/reports/OC_Peck_Monitoring_2020.xlsx",
    data_mappings={
        'CrossSectional': comparison_df,
        'Volumetric': volumes_df,
        'Shoreline': shoreline_metrics,
        'ProjectTotals': project_results
    }
)
```

### Step 5.3: Statistical Summaries

**Objective:** Calculate summary statistics for report text

**Actions:**

```python
from profcalc.tools.monitoring import generate_summary_statistics

stats = generate_summary_statistics(
    comparison_df=comparison_df,
    volumes_df=volumes_df,
    shoreline_df=shoreline_metrics
)

# Example outputs:
print(f"Profiles meeting design criteria: {stats['pct_meeting_design']:.1f}%")
print(f"Average deficit per profile: {stats['avg_deficit_area']:.0f} sq ft")
print(f"Total nourishment needed: {stats['total_fill_volume']:.0f} cu yd")
print(f"Erosion hot spot: {stats['max_erosion_profile']} ({stats['max_erosion_rate']:.1f} ft/yr)")
```

---

## Data Flow Summary

### Inputs Required

1. ✅ Survey data files (multiple years)
2. ✅ Design template profiles
3. ✅ Analysis configuration (bounds, parameters)
4. ✅ Profile metadata (spacings, baselines)
5. ✅ Formatted Excel templates (optional)

### Intermediate Outputs

- Cross-sectional area calculations
- Profile comparison results
- Shoreline position data

### Final Outputs

1. 📊 **Excel Tables:**
   - Cross-sectional area summary
   - Volumetric change summary
   - Shoreline position summary
   - Project totals and statistics

2. 🗺️ **Shapefiles for ArcGIS:**
   - Shoreline positions (points)
   - Profile lines (polylines) with attributes
   - Volume change polygons (optional)

3. 📈 **Summary Statistics:**
   - Formatted text for report
   - Key performance indicators
   - Trend analysis results

---

## Workflow Execution

### Single-Year Analysis

```python
# Step 1: Load data
survey = read_csv_profiles("src/profcalc/data/2020_profiles.csv")
templates = read_csv_profiles("src/profcalc/data/templates.csv")
bounds = load_analysis_bounds("config/bounds.json")

# Step 2: Cross-sectional analysis
comparison_df = analyze_profiles_vs_templates(survey, templates, bounds)

# Step 3: Volumetric analysis
volumes_df = calculate_project_volumes(survey, templates, spacings, bounds)

# Step 4: Shoreline analysis
shoreline_df = extract_shoreline_data(survey, templates, bounds)

# Step 5: Generate outputs
export_results(comparison_df, volumes_df, shoreline_df, output_dir="output/2020")
```

### Multi-Year Temporal Analysis

```python
# Load multiple years
surveys = {
    '2020': read_csv_profiles("src/profcalc/data/2020_profiles.csv"),
    '2019': read_csv_profiles("src/profcalc/data/2019_profiles.csv"),
    '2018': read_csv_profiles("src/profcalc/data/2018_profiles.csv")
}

# Temporal comparison
temporal_results = analyze_temporal_changes(surveys, templates, spacings, bounds)

# Export trends and rates
export_temporal_analysis(temporal_results, output_dir="output/trends")
```

---

## Notes and Considerations

### Data Quality

- Validate survey data completeness before analysis
- Check for profile gaps or missing sections
- Verify elevation datum consistency across surveys

### Computational Efficiency

- Profile-to-profile calculations can be parallelized
- Consider caching intermediate results for large datasets
- Use vectorized operations where possible (NumPy)

### Flexibility

- All elevation bounds are configurable (not hard-coded)
- Profile spacings can vary along the project
- Analysis methods can be swapped (e.g., different integration rules)

### Validation

- Compare code results against manual BMAP/Excel calculations
- Check volumetric totals for conservation of mass
- Verify shoreline positions visually in GIS

---

## Next Steps

1. Review this workflow for completeness and accuracy
2. Implement modular calculation tools (see `modular_tools_specification.md`)
3. Develop validation framework (see `validation_strategy.md`)
4. Test with sample data to verify results
5. Expand functionality after validation confirms accuracy

"""
Input File Summaries for Coastal Profile Analysis Scripts:

1. Project_Data_Input.csv (9 fields):
   - Project: Project name (e.g., "Manasquan to Barnegat").
   - Reach: Sub-division within the project (e.g., "Point Pleasant") for different geometries/templates.
   - Sta_From: Starting station for the reach.
   - Sta_To: Ending station for the reach.
   - MHW_Elev: Mean High Water elevation (ft NAVD88).
   - MLW_Elev: Mean Low Water elevation (ft NAVD88).
   - LastNourish_Date: Date of last beach nourishment.
   - NextNoursh_Date: Date of next scheduled nourishment.
   - Nourish_Cycle: Nourishment cycle length in years.

   Purpose: Provides project-level constants, elevations, and nourishment scheduling. Projects can have multiple reaches with different station ranges.

2. ProfileLine_Data_Input.csv (10 fields):
   - Project: Project name (matches DProject).
   - Profile_ID: Unique profile identifier (e.g., "MA001").
   - Station: Station number along the project.
   - Origin_X: X-coordinate of profile origin (easting).
   - Origin_Y: Y-coordinate of profile origin (northing).
   - Azimuth: Profile baseline orientation in degrees.
   - Town: Associated town/location.
   - Xon: Landward X-bound for volume calculations.
   - Xoff: Seaward X-bound for volume calculations.
   - Closure: Closure depth for the profile.

   Purpose: Defines spatial geometry and bounds for each profile line.

3. DesignTemplate_Data_Input.csv (9 fields):
   - Project: Project name.
   - Profile_ID: Profile identifier.
   - Station: Station number.
   - Dune_Elev: Target dune elevation in design template.
   - Berm_Elev: Target berm elevation.
   - Shoreline_Elev: Target shoreline elevation.
   - Dune_Width: Dune width in feet.
   - Berm_Width: Berm width in feet.
   - Nearshore_Slope: Nearshore slope.

   Purpose: Specifies ideal profile shapes for nourishment design and comparison.

Note: The 9Column_Data_Input.csv is a sample of raw survey data with fields:
- PROFILE ID, DATE, TIME (EST), POINT #, EASTING (X), NORTHING (Y), ELEVATION (Z), TYPE, DESCRIPTION.
This is used for parsing actual survey profiles.
"""

import math
import os
from typing import Dict, Optional

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point


def extract_seaward_most_position(profile: pd.DataFrame, target_elevation: float) -> Optional[Dict[str, float]]:
    """
    Extract the seaward-most cross-shore distance and real-world coordinates where the profile crosses a target elevation.

    Args:
        profile: DataFrame with columns 'X' (distance) and 'Z' (elevation).
        target_elevation: Elevation to find (e.g., 4.0).

    Returns:
        A dictionary containing the elevation, cross-shore distance, easting, northing, and elevation.
    """
    x = profile['X'].values
    z = profile['Z'].values

    seaward_most = None

    for i in range(len(x) - 1):
        if (z[i] - target_elevation) * (z[i + 1] - target_elevation) <= 0:
            # Linear interpolation to find the crossing point
            frac = (target_elevation - z[i]) / (z[i + 1] - z[i])
            cross_shore_x = x[i] + frac * (x[i + 1] - x[i])
            seaward_most = {
                "Elevation": target_elevation,
                "CrossShoreX": cross_shore_x,
                "Z": target_elevation  # Elevation remains the same
            }

    return seaward_most


def calculate_real_world_coordinates(point: Dict[str, float], origin_easting: float, origin_northing: float, azimuth: float) -> Dict[str, float]:
    """
    Convert a cross-shore distance to real-world coordinates (Easting, Northing).

    Args:
        point: A point with 'CrossShoreX' and 'Z'.
        origin_easting: Easting of the profile origin.
        origin_northing: Northing of the profile origin.
        azimuth: Azimuth of the profile in degrees.

    Returns:
        The point with added 'Easting' and 'Northing'.
    """
    azimuth_rad = math.radians(azimuth)
    cross_shore_x = point['CrossShoreX']
    point['Easting'] = origin_easting + cross_shore_x * math.cos(azimuth_rad)
    point['Northing'] = origin_northing + cross_shore_x * math.sin(azimuth_rad)
    return point


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract seaward-most shoreline positions at multiple target elevations.")
    parser.add_argument("--input", default="Input_Files/9Column_Data_Input.csv", help="Path to input survey CSV file (9Column format with PROFILE ID, EASTING, NORTHING, ELEVATION).")
    parser.add_argument("--project-metadata", default="Input_Files/Project_Data_Input.csv", help="Path to project metadata CSV file.")
    parser.add_argument("--profile-metadata", default="Input_Files/ProfileLine_Data_Input.csv", help="Path to profile metadata CSV file.")
    parser.add_argument("--profile-id", required=True, help="Profile ID to process (e.g., MA063).")
    parser.add_argument("--output-csv", required=True, help="Path to output CSV file.")
    parser.add_argument("--output-shapefile", required=True, help="Path to output shapefile.")

    args = parser.parse_args()

    # Define paths for the mandatory input files
    project_metadata_path = "Input_Files/Project_Data_Input.csv"
    profile_metadata_path = "Input_Files/ProfileLine_Data_Input.csv"
    survey_file_path = "Input_Files/9Column_Data_Input.csv"

    # Check if the mandatory input files exist
    for file_path, description in [
        (project_metadata_path, "Project Metadata CSV File"),
        (profile_metadata_path, "Profile Metadata CSV File"),
        (survey_file_path, "9-Column Survey File")
    ]:
        if not os.path.isfile(file_path):
            print(f"{description} not found at {file_path}.")
            while True:
                file_path = input(f"Enter the path to the {description}: ")
                if os.path.isfile(file_path):
                    print(f"{description} found.")
                    break
                else:
                    print("Invalid file path. Please try again.")

    # Update the paths with user-provided values if necessary
    project_metadata_path = project_metadata_path
    profile_metadata_path = profile_metadata_path
    survey_file_path = survey_file_path

    # Read the project CSV to get elevation constants
    # Source: Project_Data_Input.csv - contains project-level elevations and nourishment data
    project_data = pd.read_csv(args.project_metadata)
    required_project_columns = ['MHW_Elev', 'MLW_Elev', 'Shoreline_Elev', 'Berm_Elev']
    if not all(col in project_data.columns for col in required_project_columns):
        raise ValueError(f"The project CSV file must contain the following columns: {', '.join(required_project_columns)}")

    # Extract target elevations
    target_elevations = [
        project_data['MHW_Elev'].iloc[0],
        project_data['MLW_Elev'].iloc[0],
        project_data['Shoreline_Elev'].iloc[0],
        project_data['Berm_Elev'].iloc[0]
    ]

    # Read the profile metadata CSV to get origin values for the specified profile
    # Source: ProfileLine_Data_Input.csv - contains profile geometry and bounds
    profile_metadata = pd.read_csv(args.profile_metadata)
    required_profile_columns = ['Project', 'Profile_ID', 'Origin_X', 'Origin_Y', 'Azimuth']
    if not all(col in profile_metadata.columns for col in required_profile_columns):
        raise ValueError(f"The profile metadata CSV file must contain the following columns: {', '.join(required_profile_columns)}")

    # Filter for the specified profile
    profile_row = profile_metadata[profile_metadata['Profile_ID'] == args.profile_id]
    if profile_row.empty:
        raise ValueError(f"Profile ID '{args.profile_id}' not found in profile metadata.")

    # Extract origin and azimuth
    origin_easting = profile_row['Origin_X'].iloc[0]
    origin_northing = profile_row['Origin_Y'].iloc[0]
    azimuth = profile_row['Azimuth'].iloc[0]

    # Read the survey data CSV and filter for the profile
    # Source: 9Column_Data_Input.csv - contains raw survey points with elevations
    survey_data = pd.read_csv(args.input)
    required_survey_columns = ['PROFILE ID', 'ELEVATION']
    if not all(col in survey_data.columns for col in required_survey_columns):
        raise ValueError(f"The survey CSV file must contain the following columns: {', '.join(required_survey_columns)}")

    # Filter survey data for the profile
    profile_survey = survey_data[survey_data['PROFILE ID'] == args.profile_id]
    if profile_survey.empty:
        raise ValueError(f"No survey data found for profile ID '{args.profile_id}'.")

    # Assume EASTING is X (cross-shore), ELEVATION is Z
    # Note: This assumes EASTING represents cross-shore distance; adjust if needed
    profile_df = profile_survey[['ELEVATION']].rename(columns={'ELEVATION': 'Z'})
    # For simplicity, create X as index or assume sequential; in real data, may need to calculate X from coordinates
    profile_df['X'] = range(len(profile_df))  # Placeholder; replace with actual cross-shore calculation

    # Extract the seaward-most shoreline positions
    shoreline_positions = []
    for elevation in target_elevations:
        point = extract_seaward_most_position(profile_df, elevation)
        if point:
            point = calculate_real_world_coordinates(point, origin_easting, origin_northing, azimuth)
            shoreline_positions.append(point)

    # Write the results to the output CSV file
    pd.DataFrame(shoreline_positions).to_csv(args.output_csv, index=False)

    # Write the results to a shapefile
    gdf = gpd.GeoDataFrame(
        shoreline_positions,
        geometry=[Point(p['Easting'], p['Northing']) for p in shoreline_positions],
        crs="EPSG:4326"  # Default to WGS84; adjust as needed
    )
    gdf.to_file(args.output_shapefile, driver="ESRI Shapefile")

    print("Seaward-most shoreline positions saved to CSV and shapefile.")

# =============================================================================
# Shoreline Position Extraction Module
# =============================================================================
#
# FILE: src/profcalc/ref_code/modules/extract_shoreline.py
#
# PURPOSE:
# This module provides functionality for extracting shoreline positions from
# beach profile survey data. It calculates the seaward-most cross-shore
# positions where profiles intersect target elevations (typically MHW, MLW,
# shoreline, and berm elevations) and converts these to real-world coordinates.
#
# WHAT IT'S FOR:
# - Extracts shoreline positions at multiple target elevations
# - Converts cross-shore distances to real-world coordinates (Easting/Northing)
# - Processes 9-column survey data format with profile metadata
# - Generates CSV and shapefile outputs for GIS analysis
# - Supports command-line interface for batch processing
# - Handles profile geometry transformations using azimuth and origin coordinates
#
# WORKFLOW POSITION:
# This module is used in coastal engineering analysis workflows to determine
# shoreline positions from survey data. It's typically used after profile
# data has been collected and before volume calculations or shoreline change
# analysis. The extracted positions can be used for erosion monitoring,
# nourishment design, and coastal management planning.
#
# LIMITATIONS:
# - Requires specific input file formats (9-column survey, project metadata, profile metadata)
# - Assumes linear interpolation between survey points for elevation crossing
# - Coordinate transformations depend on accurate azimuth and origin data
# - Processing is profile-by-profile (not optimized for large datasets)
#
# ASSUMPTIONS:
# - Survey data contains valid elevation profiles with X (distance) and Z (elevation) columns
# - Profile metadata includes accurate origin coordinates and azimuth angles
# - Target elevations are appropriate for the coastal environment being analyzed
# - Input files follow the expected CSV format conventions
# - Coordinate system is consistent across all input data
#
# =============================================================================

import math
import os
from typing import Dict, Optional

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point


def extract_seaward_most_position(
    profile: pd.DataFrame, target_elevation: float
) -> Optional[Dict[str, float]]:
    """
    Extract the seaward-most cross-shore distance and real-world coordinates where the profile crosses a target elevation.

    Args:
        profile: DataFrame with columns 'X' (distance) and 'Z' (elevation).
        target_elevation: Elevation to find (e.g., 4.0).

    Returns:
        A dictionary containing the elevation, cross-shore distance, easting, northing, and elevation.
    """
    x = profile["X"].values
    z = profile["Z"].values

    seaward_most = None

    for i in range(len(x) - 1):
        if (z[i] - target_elevation) * (z[i + 1] - target_elevation) <= 0:
            # Linear interpolation to find the crossing point
            frac = (target_elevation - z[i]) / (z[i + 1] - z[i])
            cross_shore_x = x[i] + frac * (x[i + 1] - x[i])
            seaward_most = {
                "Elevation": target_elevation,
                "CrossShoreX": cross_shore_x,
                "Z": target_elevation,  # Elevation remains the same
            }

    return seaward_most


def calculate_real_world_coordinates(
    point: Dict[str, float],
    origin_easting: float,
    origin_northing: float,
    azimuth: float,
) -> Dict[str, float]:
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
    cross_shore_x = point["CrossShoreX"]
    point["Easting"] = origin_easting + cross_shore_x * math.cos(azimuth_rad)
    point["Northing"] = origin_northing + cross_shore_x * math.sin(azimuth_rad)
    return point


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract seaward-most shoreline positions at multiple target elevations."
    )
    parser.add_argument(
        "--input",
        default="Input_Files/9Column_Data_Input.csv",
        help="Path to input survey CSV file (9Column format with PROFILE ID, EASTING, NORTHING, ELEVATION).",
    )
    parser.add_argument(
        "--project-metadata",
        default="Input_Files/Project_Data_Input.csv",
        help="Path to project metadata CSV file.",
    )
    parser.add_argument(
        "--profile-metadata",
        default="Input_Files/ProfileLine_Data_Input.csv",
        help="Path to profile metadata CSV file.",
    )
    parser.add_argument(
        "--profile-id", required=True, help="Profile ID to process (e.g., MA063)."
    )
    parser.add_argument("--output-csv", required=True, help="Path to output CSV file.")
    parser.add_argument(
        "--output-shapefile", required=True, help="Path to output shapefile."
    )

    args = parser.parse_args()

    # Define paths for the mandatory input files
    project_metadata_path = "Input_Files/Project_Data_Input.csv"
    profile_metadata_path = "Input_Files/ProfileLine_Data_Input.csv"
    survey_file_path = "Input_Files/9Column_Data_Input.csv"

    # Check if the mandatory input files exist
    for file_path, description in [
        (project_metadata_path, "Project Metadata CSV File"),
        (profile_metadata_path, "Profile Metadata CSV File"),
        (survey_file_path, "9-Column Survey File"),
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
    required_project_columns = ["MHW_Elev", "MLW_Elev", "Shoreline_Elev", "Berm_Elev"]
    if not all(col in project_data.columns for col in required_project_columns):
        raise ValueError(
            f"The project CSV file must contain the following columns: {', '.join(required_project_columns)}"
        )

    # Extract target elevations
    target_elevations = [
        project_data["MHW_Elev"].iloc[0],
        project_data["MLW_Elev"].iloc[0],
        project_data["Shoreline_Elev"].iloc[0],
        project_data["Berm_Elev"].iloc[0],
    ]

    # Read the profile metadata CSV to get origin values for the specified profile
    # Source: ProfileLine_Data_Input.csv - contains profile geometry and bounds
    profile_metadata = pd.read_csv(args.profile_metadata)
    required_profile_columns = [
        "Project",
        "Profile_ID",
        "Origin_X",
        "Origin_Y",
        "Azimuth",
    ]
    if not all(col in profile_metadata.columns for col in required_profile_columns):
        raise ValueError(
            f"The profile metadata CSV file must contain the following columns: {', '.join(required_profile_columns)}"
        )

    # Filter for the specified profile
    profile_row = profile_metadata[profile_metadata["Profile_ID"] == args.profile_id]
    if profile_row.empty:
        raise ValueError(
            f"Profile ID '{args.profile_id}' not found in profile metadata."
        )

    # Extract origin and azimuth
    origin_easting = profile_row["Origin_X"].iloc[0]
    origin_northing = profile_row["Origin_Y"].iloc[0]
    azimuth = profile_row["Azimuth"].iloc[0]

    # Read the survey data CSV and filter for the profile
    # Source: 9Column_Data_Input.csv - contains raw survey points with elevations
    survey_data = pd.read_csv(args.input)
    required_survey_columns = ["PROFILE ID", "ELEVATION"]
    if not all(col in survey_data.columns for col in required_survey_columns):
        raise ValueError(
            f"The survey CSV file must contain the following columns: {', '.join(required_survey_columns)}"
        )

    # Filter survey data for the profile
    profile_survey = survey_data[survey_data["PROFILE ID"] == args.profile_id]
    if profile_survey.empty:
        raise ValueError(f"No survey data found for profile ID '{args.profile_id}'.")

    # Assume EASTING is X (cross-shore), ELEVATION is Z
    # Note: This assumes EASTING represents cross-shore distance; adjust if needed
    profile_df = profile_survey[["ELEVATION"]].rename(columns={"ELEVATION": "Z"})
    # For simplicity, create X as index or assume sequential; in real data, may need to calculate X from coordinates
    profile_df["X"] = range(
        len(profile_df)
    )  # Placeholder; replace with actual cross-shore calculation

    # Extract the seaward-most shoreline positions
    shoreline_positions = []
    for elevation in target_elevations:
        point = extract_seaward_most_position(profile_df, elevation)
        if point:
            point = calculate_real_world_coordinates(
                point, origin_easting, origin_northing, azimuth
            )
            shoreline_positions.append(point)

    # Write the results to the output CSV file
    pd.DataFrame(shoreline_positions).to_csv(args.output_csv, index=False)

    # Write the results to a shapefile
    gdf = gpd.GeoDataFrame(
        shoreline_positions,
        geometry=[Point(p["Easting"], p["Northing"]) for p in shoreline_positions],
        crs="EPSG:4326",  # Default to WGS84; adjust as needed
    )
    gdf.to_file(args.output_shapefile, driver="ESRI Shapefile")

    print("Seaward-most shoreline positions saved to CSV and shapefile.")

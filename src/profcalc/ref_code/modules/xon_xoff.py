# =============================================================================
# Xon/Xoff Boundary Volume Calculation Module
# =============================================================================
#
# FILE: src/profcalc/ref_code/modules/xon_xoff.py
#
# PURPOSE:
# This module provides specialized functionality for calculating sediment
# volumes within defined cross-shore boundaries (Xon/Xoff limits). It
# computes volumes above specified cut elevations between landward and
# seaward bounds, supporting detailed coastal engineering analysis for
# volume change assessment and nourishment planning.
#
# WHAT IT'S FOR:
# - Calculates sediment volumes between Xon (landward) and Xoff (seaward) boundaries
# - Computes volumes above specified cut elevations (e.g., MHW, MLW)
# - Processes profile survey data with uniform grid interpolation
# - Supports command-line interface for batch processing
# - Generates volume reports in cubic yards per foot
# - Handles profile metadata and survey data integration
#
# WORKFLOW POSITION:
# This module is used in coastal volume analysis workflows where spatial
# boundaries are critical for meaningful sediment budget calculations.
# It's typically applied when analyzing specific beach segments or
# nourishment project areas with well-defined cross-shore limits.
#
# LIMITATIONS:
# - Requires accurate Xon/Xoff boundary definitions for each profile
# - Volume calculations use linear interpolation between survey points
# - Assumes uniform grid spacing for trapezoidal integration
# - Processing is profile-by-profile (not optimized for large datasets)
#
# ASSUMPTIONS:
# - Xon/Xoff boundaries are appropriately defined for volume analysis objectives
# - Survey data contains sufficient point density for accurate interpolation
# - Cut elevations are meaningful for the coastal environment being analyzed
# - Profile data includes consistent X (distance) and Z (elevation) coordinates
# - Coordinate systems and units are consistent across input data
#
# =============================================================================

import argparse
from typing import Dict

import numpy as np
import pandas as pd


def compute_volume_xon_xoff(
    profile: pd.DataFrame, xon: float, xoff: float, cut_elev: float
) -> Dict[str, float]:
    """
    Compute the volume above a cut elevation between Xon and Xoff.

    Args:
        profile: DataFrame with columns 'X' (distance) and 'Z' (elevation).
        xon: Landward limit (Xon).
        xoff: Seaward limit (Xoff).
        cut_elev: Cut elevation (e.g., MHW).

    Returns:
        A dictionary with the computed volume and other metrics.
    """
    # Interpolate profile data to a uniform grid between Xon and Xoff
    # Ensure we have plain numpy arrays (avoid pandas ExtensionArray types)
    x = np.asarray(profile["X"])
    z = np.asarray(profile["Z"])
    x_uniform = np.linspace(xon, xoff, num=500)  # Uniform grid with 500 points
    z_uniform = np.interp(x_uniform, x, z)

    # Clip elevations below the cut elevation
    z_clipped = np.maximum(0.0, z_uniform - cut_elev)

    # Compute volume using the trapezoidal rule and ensure float results
    volume_ft3_per_ft = float(np.trapz(z_clipped, x_uniform))
    volume_cuyd_per_ft = volume_ft3_per_ft / 27.0  # Convert to cubic yards per foot

    return {
        "Xon": xon,
        "Xoff": xoff,
        "CutElevation": cut_elev,
        "VolumeCubicYardsPerFoot": volume_cuyd_per_ft,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute volume above a cut elevation between Xon and Xoff."
    )
    parser.add_argument(
        "--profile-csv",
        default="Input_Files/ProfileLine_Data_Input.csv",
        help="Path to profile metadata CSV file.",
    )
    parser.add_argument(
        "--project-csv",
        default="Input_Files/Project_Data_Input.csv",
        help="Path to project metadata CSV file.",
    )
    parser.add_argument(
        "--survey-csv",
        default="Input_Files/9Column_Data_Input.csv",
        help="Path to survey data CSV file.",
    )
    parser.add_argument("--profile-id", required=True, help="Profile ID to process.")
    parser.add_argument("--output-csv", required=True, help="Path to output CSV file.")

    args = parser.parse_args()

    # Read the profile metadata CSV to get Xon and Xoff
    # Source: ProfileLine_Data_Input.csv - contains profile bounds and geometry
    profile_data = pd.read_csv(args.profile_csv)
    required_profile_columns = ["Profile_ID", "Xon", "Xoff"]
    if not all(col in profile_data.columns for col in required_profile_columns):
        raise ValueError(
            f"The profile CSV file must contain the following columns: {', '.join(required_profile_columns)}"
        )

    # Filter for the profile
    profile_row = profile_data[profile_data["Profile_ID"] == args.profile_id]
    if profile_row.empty:
        raise ValueError(f"Profile ID '{args.profile_id}' not found.")

    xon = profile_row["Xon"].iloc[0]
    xoff = profile_row["Xoff"].iloc[0]

    # Read the project CSV to get the cut elevation
    # Source: Project_Data_Input.csv - contains project elevations
    project_data = pd.read_csv(args.project_csv)
    required_project_columns = ["MHW_Elev"]
    if not all(col in project_data.columns for col in required_project_columns):
        raise ValueError(
            f"The project CSV file must contain the following columns: {', '.join(required_project_columns)}"
        )

    cut_elev = project_data["MHW_Elev"].iloc[0]

    # Read survey data for X and Z
    # Source: 9Column_Data_Input.csv - contains survey elevations
    survey_data = pd.read_csv(args.survey_csv)
    required_survey_columns = ["PROFILE ID", "ELEVATION"]
    if not all(col in survey_data.columns for col in required_survey_columns):
        raise ValueError(
            f"The survey CSV file must contain the following columns: {', '.join(required_survey_columns)}"
        )

    profile_survey = survey_data[survey_data["PROFILE ID"] == args.profile_id]
    if profile_survey.empty:
        raise ValueError(f"No survey data for profile '{args.profile_id}'.")

    # Create profile DataFrame with X and Z
    profile_df = pd.DataFrame(
        {
            "X": range(len(profile_survey)),  # Placeholder for cross-shore X
            "Z": profile_survey["ELEVATION"],
        }
    )

    # Compute the volume
    result = compute_volume_xon_xoff(profile_df, xon, xoff, cut_elev)

    # Save the result to the output CSV file
    pd.DataFrame([result]).to_csv(args.output_csv, index=False)

    print(f"Volume calculation complete. Results saved to {args.output_csv}.")


if __name__ == "__main__":
    main()

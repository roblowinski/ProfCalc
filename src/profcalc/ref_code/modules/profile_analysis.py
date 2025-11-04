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

# Import the package-local parsers from the profcalc package
from profcalc.common.csv_io import CSVParser
from profcalc.common.ninecol_io import NineColumnParser

# Initialize the NineColumnParser
nine_col_parser = NineColumnParser()

# Placeholder for azimuth calculation logic
def calculate_azimuths(data):
    """
    Calculate orthogonal and average azimuths.
    This function mimics the MATLAB `orthogonalangle` logic.

    Args:
        data (list): List of profile data (e.g., coordinates).

    Returns:
        dict: Calculated azimuths and related metrics.
    """
    # Example implementation (replace with actual logic):
    azimuths = []
    orthogonals = []
    avg_azimuth = 0.0
    diff_angles = []

    # Iterate through data to calculate azimuths (placeholder logic)
    for i in range(len(data) - 1):
        # Calculate azimuth between two points (example logic)
        dx = data[i+1][0] - data[i][0]
        dy = data[i+1][1] - data[i][1]
        azimuth = math.atan2(dy, dx) * (180 / math.pi)  # Convert to degrees
        azimuths.append(azimuth)

    # Calculate orthogonal angles and average azimuth (example logic)
    orthogonals = [(az + 90) % 360 for az in azimuths]
    avg_azimuth = sum(azimuths) / len(azimuths) if azimuths else 0
    diff_angles = [abs(az - avg_azimuth) for az in azimuths]

    return {
        "azimuths": azimuths,
        "orthogonals": orthogonals,
        "avg_azimuth": avg_azimuth,
        "diff_angles": diff_angles
    }

def main():
    """Run the profile analysis CLI/main routine.

    This function wraps the previous top-level script behavior so the module can be
    imported without side effects. It will parse static input files and process the
    optional 9-column survey file when executed as a script.
    """

    # Define paths for the three static files
    bmap_free_format_path = "Input_Files/Bmap_FreeFormat.txt"  # BMAP Free Format File
    project_data_csv_path = "Input_Files/Project_Data_Input.csv"  # Project Data CSV File
    profile_line_data_csv_path = "Input_Files/ProfileLine_Data_Input.csv"  # Profile Line Data CSV File

    # Check if the three static files exist
    for file_path, description in [
        (bmap_free_format_path, "BMAP Free Format File"),
        (project_data_csv_path, "Project Data CSV File"),
        (profile_line_data_csv_path, "Profile Line Data CSV File"),
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

    # Initialize the CSVParser for the profile metadata file
    static_csv_path = "Input_Files/ProfileLine_Data_Input.csv"

    # Parse the profile metadata CSV file
    try:
        parser = CSVParser()
        static_profiles = parser.parse_file(static_csv_path)
        # static_profiles intentionally parsed here for downstream processing in full applications
        _ = static_profiles
        print("Profile metadata loaded successfully.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error parsing profile metadata CSV file: {e}")
        exit(1)

    # Parse the Project Data CSV File
    try:
        project_parser = CSVParser()
        project_data = project_parser.parse_file(project_data_csv_path)
        # project_data intentionally parsed for completeness; may be used in fuller workflows
        _ = project_data
        print("Project data loaded successfully.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error parsing Project Data CSV File: {e}")
        exit(1)

    # Parse the Profile Line Data CSV File
    try:
        profile_parser = CSVParser()
        profile_line_data = profile_parser.parse_file(profile_line_data_csv_path)
        # profile_line_data intentionally parsed for completeness
        _ = profile_line_data
        print("Profile line data loaded successfully.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error parsing Profile Line Data CSV File: {e}")
        exit(1)

    # Check if the dynamic 9-column survey file exists
    survey_file_path = "Input_Files/9Column_Data_Input.csv"

    # Enhanced error handling and input validation for 9-column file parsing
    try:
        # Validate the file path
        if not os.path.isfile(survey_file_path):
            raise FileNotFoundError(f"The specified 9-column file does not exist: {survey_file_path}")

        # Parse the 9-column file
        profiles = nine_col_parser.parse_file(survey_file_path)
        if not profiles:
            raise ValueError("No profiles were found in the 9-column file. Please check the file content.")

        print("9-column file parsed successfully.")

        # Extract coordinates for azimuth calculation
        for profile in profiles:
            if not profile.x or not profile.metadata.get("y_coordinates"):
                raise ValueError(f"Profile {profile.name} is missing coordinate data.")

            profile_data = list(zip(profile.x, profile.metadata.get("y_coordinates", [])))
            azimuth_results = calculate_azimuths(profile_data)
            print(f"Azimuth results for profile {profile.name}: {azimuth_results}")

    except FileNotFoundError as fnf_error:
        print(f"Error: {fnf_error}")
    except ValueError as val_error:
        print(f"Validation Error: {val_error}")


if __name__ == "__main__":
    main()

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

import argparse
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Field name aliases for handling different naming conventions in input files
FIELD_ALIASES = {
    # Profile metadata fields
    'Profile_ID': ['Profile_ID', 'PROFILE ID', 'PROFILEID', 'ProfileID', 'profile_id'],
    'Xon': ['Xon', 'XON', 'xon'],
    'Xoff': ['Xoff', 'XOFF', 'xoff'],

    # Survey data fields
    'PROFILE ID': ['PROFILE ID', 'Profile_ID', 'PROFILEID', 'ProfileID', 'profile_id'],
    'ELEVATION (Z)': ['ELEVATION (Z)', 'ELEVATION', 'Z', 'Elevation', 'elevation', 'ELEVATION(Z)'],
}


def normalize_column_names(df: pd.DataFrame, required_fields: List[str]) -> pd.DataFrame:
    """
    Normalize column names in a DataFrame to match expected field names using aliases.

    Parameters:
        df: DataFrame with potentially different column names
        required_fields: List of expected field names

    Returns:
        DataFrame with normalized column names
    """
    df_normalized = df.copy()
    df_normalized.columns = df_normalized.columns.str.strip()

    # Create mapping from actual columns to expected fields
    column_mapping = {}
    for expected_field in required_fields:
        if expected_field in df_normalized.columns:
            column_mapping[expected_field] = expected_field
        else:
            # Check aliases
            for alias in FIELD_ALIASES.get(expected_field, []):
                if alias in df_normalized.columns:
                    column_mapping[expected_field] = alias
                    break

    # Check if all required fields are found
    missing_fields = [field for field in required_fields if field not in column_mapping]
    if missing_fields:
        available_aliases = []
        for field in missing_fields:
            available_aliases.extend(FIELD_ALIASES.get(field, []))
        raise ValueError(f"Required fields {missing_fields} not found. Available columns: {list(df_normalized.columns)}. Tried aliases: {available_aliases}")

    # Rename columns
    df_normalized = df_normalized.rename(columns={v: k for k, v in column_mapping.items()})

    return df_normalized


# Copied functions from external dependencies to make this standalone


@dataclass
class Profile:
    """Represents a single beach profile from a BMAP free format file."""

    name: str
    date: Optional[str]
    description: Optional[str]
    x: np.ndarray
    z: np.ndarray
    metadata: Optional[Dict[str, Any]] = None


class BMAPParser:
    """Parser for BMAP free format files.

    Handles the parsing of BMAP format files containing beach profile
    survey data. BMAP files have header lines followed by point count
    and coordinate pairs.
    """

    PURPOSE_BD = "BD"
    PURPOSE_AD = "AD"
    PURPOSE_TEMPLATE = "T"
    PURPOSE_OTHER = "O"
    PURPOSE_STUDY = "S"
    PURPOSE_PRECON_PS = "PP"
    PURPOSE_PRECON_INFO = "PI"
    PURPOSE_PREPLACE = "PR"
    PURPOSE_PRESTORM = "PS"
    PURPOSE_POSTPLACE = "PO"
    PURPOSE_POSTSTORM = "PT"
    PURPOSE_POSTPLACE2 = "PX"
    PURPOSE_ANNUAL = "A"
    PURPOSE_PRESTORM2 = "P2"
    PURPOSE_POSTSTORM2 = "PT2"
    PURPOSE_DESIGN = "D"

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the BMAP parser.

        Args:
            config: Optional configuration dictionary for parsing options
        """
        self.config = config or {}

    def parse_header(
        self, header: str
    ) -> tuple[str, Optional[datetime], str, str]:
        """Parse a BMAP header line.

        Args:
            header: Header line from BMAP file

        Returns:
            Tuple of (profile_name, date, description, purpose)

        Notes:
            This parser now handles profile names with spaces by:
            1. First extracting known components (date, purpose codes)
            2. Then treating the remainder as the profile name
            3. Supporting formats like "OC 117 15AUG2020" or "Site Name 01/01/2020"
        """
        header = (header or "").strip()
        if not header:
            return "", None, "", self.PURPOSE_OTHER

        # First, find and extract the date (if present)
        date = None
        date_match = None
        for pat, fmt in [
            (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
            (r"\d{2}/\d{2}/\d{4}", "%m/%d/%Y"),
            (r"\d{2}[A-Za-z]{3}\d{4}", "%d%b%Y"),
            (r"\d{4}_\d{2}_\d{2}", "%Y_%m_%d"),  # Handle underscore format
        ]:
            m = re.search(pat, header)
            if m:
                try:
                    date = datetime.strptime(m.group(0), fmt)
                    date_match = m
                except ValueError:
                    date = None
                    date_match = None
                break

        # Find purpose code (if present)
        purpose = self.PURPOSE_OTHER
        purpose_match = None
        for tok in [
            self.PURPOSE_BD,
            self.PURPOSE_AD,
            self.PURPOSE_TEMPLATE,
            self.PURPOSE_STUDY,
            self.PURPOSE_DESIGN,
            self.PURPOSE_PRECON_PS,
            self.PURPOSE_PRECON_INFO,
            self.PURPOSE_PREPLACE,
            self.PURPOSE_PRESTORM,
            self.PURPOSE_POSTPLACE,
            self.PURPOSE_POSTSTORM,
            self.PURPOSE_POSTPLACE2,
            self.PURPOSE_ANNUAL,
            self.PURPOSE_PRESTORM2,
            self.PURPOSE_POSTSTORM2,
            "Preplacement",  # Add common purpose codes
            "Postplacement",
        ]:
            match = re.search(rf"\b{re.escape(tok)}\b", header, re.IGNORECASE)
            if match:
                purpose = tok
                purpose_match = match
                break

        # Extract profile name by removing known components
        remaining = header
        if date_match:
            remaining = remaining.replace(date_match.group(0), "")
        if purpose_match:
            remaining = remaining.replace(purpose_match.group(0), "")

        profile_name = remaining.strip()
        if not profile_name:
            profile_name = f"bmap_profile_{uuid.uuid4().hex[:8]}"

        # Extract description (anything after profile name and before date/purpose)
        description = ""
        if profile_name and profile_name != header:
            desc_start = header.find(profile_name) + len(profile_name)
            desc_end = len(header)
            if date_match and date_match.start() < desc_end:
                desc_end = date_match.start()
            if purpose_match and purpose_match.start() < desc_end:
                desc_end = purpose_match.start()
            description = header[desc_start:desc_end].strip()

        return profile_name, date, description, purpose

    def read_profiles(self, filepath: str | Path) -> List[dict[str, Any]]:
        """Read profiles from a BMAP file.

        Args:
            filepath: Path to the BMAP file

        Returns:
            List of profile dictionaries
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)

        with open(filepath, encoding="utf-8", errors="ignore") as fh:
            lines = [ln.strip() for ln in fh if ln.strip()]

        profiles = []
        i = 0
        while i < len(lines):
            header = lines[i]
            i += 1
            if i >= len(lines):
                break
            try:
                count = int(lines[i])
            except ValueError:
                continue
            i += 1
            data_pairs = []
            for _ in range(count):
                if i >= len(lines):
                    break
                try:
                    a, b = lines[i].split()[:2]
                    data_pairs.append((float(a), float(b)))
                except (ValueError, IndexError):
                    pass
                i += 1

            profile_name, date, desc, purpose = self.parse_header(header)
            profiles.append(
                {
                    "profile_name": profile_name,
                    "date": date,
                    "description": desc,
                    "purpose": purpose,
                    "data": data_pairs,
                    "original_header": header,
                    "source_format": "BMAP",
                }
            )

        return profiles

    def parse_file(self, file_path: str | Path) -> List[Profile]:
        """Parse a BMAP file and extract beach profile data.

        Args:
            file_path: Path to the BMAP file

        Returns:
            List of Profile objects
        """
        try:
            # Read profiles from BMAP file
            profile_data_list = self.read_profiles(file_path)

            profiles = []
            for profile_data in profile_data_list:
                profile = self._convert_to_profile(profile_data)
                if profile:
                    profiles.append(profile)

            return profiles

        except Exception as e:
            raise Exception(f"Failed to parse BMAP file: {e}") from e

    def _convert_to_profile(
        self, profile_data: dict[str, Any]
    ) -> Optional[Profile]:
        """Convert profile data dictionary to Profile object.

        Args:
            profile_data: Profile data from BMAP parser

        Returns:
            Profile object or None if invalid
        """
        try:
            profile_name = profile_data.get("profile_name", "").strip()
            if not profile_name:
                profile_name = f"bmap_profile_{uuid.uuid4().hex[:8]}"

            # Extract coordinates from data pairs (x, z)
            data_pairs = profile_data.get("data", [])
            if not data_pairs:
                return None

            x_coords = []
            z_coords = []
            for x, z in data_pairs:
                x_coords.append(x)
                z_coords.append(z)

            # Create arrays
            x_array = np.array(x_coords, dtype=float)
            z_array = np.array(z_coords, dtype=float)

            # Create metadata
            metadata: dict[str, Any] = {
                "source_format": "BMAP",
                "original_header": profile_data.get("original_header", ""),
                "purpose": profile_data.get("purpose", ""),
            }

            # Add date if available
            date = profile_data.get("date")
            date_str = None
            if date:
                date_str = date.strftime("%Y-%m-%d")
                metadata["survey_date"] = date_str

            # Create description from available info
            description_parts = []
            desc = profile_data.get("description", "").strip()
            if desc:
                description_parts.append(desc)
            purpose = profile_data.get("purpose", "")
            if purpose:
                description_parts.append(f"Purpose: {purpose}")

            description = (
                "; ".join(description_parts) if description_parts else None
            )

            profile = Profile(
                name=profile_name,
                date=date_str,
                description=description,
                x=x_array,
                z=z_array,
                metadata=metadata,
            )

            return profile

        except Exception:
            return None


def bmap_style_volume_above_contour(x: np.ndarray, z: np.ndarray, contour: float, dx: float = 10.0) -> float:
    """Compute volume above contour using BMAP-style integration."""
    x = np.asarray(x, dtype=float)
    z = np.asarray(z, dtype=float)
    idx = np.argsort(x)
    x, z = x[idx], z[idx]

    # Find all crossings
    crossings = []
    for i in range(1, len(x)):
        if (z[i-1] - contour) * (z[i] - z[i-1]) < 0:
            frac = (contour - z[i-1]) / (z[i] - z[i-1])
            x_cross = x[i-1] + frac * (x[i] - x[i-1])
            crossings.append(x_cross)
        elif (z[i-1] - contour) == 0:
            crossings.append(x[i-1])
        elif (z[i] - contour) == 0:
            crossings.append(x[i])
    xon = float(x[0])
    xoff = float(x[-1])
    # If odd number of crossings, prepend xon as a virtual wall
    if len(crossings) % 2 == 1:
        crossings = [xon] + crossings
    # If even but no crossings, treat whole profile as above contour if all z > contour
    if not crossings and np.all(z > contour):
        crossings = [xon, xoff]
    # Integrate above contour for each region
    total_area = 0.0
    for i in range(0, len(crossings), 2):
        x_start, x_end = float(crossings[i]), float(crossings[i + 1])
        mask = (x >= x_start) & (x <= x_end)
        if np.sum(mask) < 2:
            # Interpolate at boundaries if needed
            x_region = np.linspace(x_start, x_end, int(np.ceil((x_end - x_start) / dx)) + 1)
            z_region = np.interp(x_region, x, z)
        else:
            x_region = np.asarray(x[mask], dtype=float)
            z_region = np.asarray(z[mask], dtype=float)
        x_region = np.asarray(x_region, dtype=float)
        z_region = np.asarray(z_region, dtype=float)
        h = np.maximum(0.0, z_region - float(contour))
        area = float(np.trapz(h, x_region))
        total_area += area
    return float(total_area) / 27.0  # cu yd/ft


def split_trap_area(
    xa: float, xb: float, za: float, zb: float
) -> tuple[float, float]:
    """Return (area_above, area_below) for trapezoid between xa..xb with end elevations za, zb.
    Splits at z=0 when crossing the datum.
    """
    if za >= 0 and zb >= 0:
        return 0.5 * (za + zb) * (xb - xa), 0.0
    elif za <= 0 and zb <= 0:
        return 0.0, 0.5 * (za + zb) * (xb - xa)
    else:
        # Crosses datum, split at zero
        frac = -za / (zb - za)
        x_cross = xa + frac * (xb - xa)
        area1 = 0.5 * (za + 0) * (x_cross - xa)
        area2 = 0.5 * (0 + zb) * (xb - x_cross)
        if za > 0:
            return area1, area2
        else:
            return area2, area1


def compute_bounded_volume(x: np.ndarray, z: np.ndarray, x_bounds: Tuple[float, ...], z_bounds: Tuple[float, ...]) -> Dict[str, float]:
    """
    Compute the volume within specified x and z bounds.

    Parameters:
        x (list or np.ndarray): x-coordinates of the profile.
        z (list or np.ndarray): z-coordinates of the profile.
        x_bounds (tuple): (x_min, x_max) bounds for the x-coordinates.
        z_bounds (tuple): (z_min, z_max) bounds for the z-coordinates.

    Returns:
        dict: A dictionary with 'volume_above' and 'volume_below'.
    """
    x_min, x_max = float(x_bounds[0]), float(x_bounds[1])
    z_min, z_max = float(z_bounds[0]), float(z_bounds[1])

    # Clip the profile to the x bounds
    x = np.asarray(x, dtype=float)
    z = np.asarray(z, dtype=float)
    mask = (x >= x_min) & (x <= x_max)
    x_clipped = x[mask]
    z_clipped = z[mask]

    volume_above = 0.0
    volume_below = 0.0

    for i in range(len(x_clipped) - 1):
        xa, xb = x_clipped[i], x_clipped[i + 1]
        za, zb = z_clipped[i], z_clipped[i + 1]

        # Clip elevations to z bounds
        za = max(min(za, z_max), z_min)
        zb = max(min(zb, z_max), z_min)

        # Use split_trap_area to calculate areas above and below the datum
        area_above, area_below = split_trap_area(xa, xb, za, zb)
        volume_above += area_above
        volume_below += area_below

    return {
        'volume_above': float(volume_above),
        'volume_below': float(volume_below),
    }

def compute_volume_change(profile1, profile2, elevation, xon, xoff):
    """
    Compute the volume change between two surveys above a specified elevation
    and within common x-bounds.

    Parameters:
        profile1 (pd.DataFrame): First survey profile with columns 'x' and 'z'.
        profile2 (pd.DataFrame): Second survey profile with columns 'x' and 'z'.
        elevation (float): Elevation threshold (e.g., MHW).
        xon (float): Landward x-bound.
        xoff (float): Seaward x-bound.

    Returns:
        dict: Volume change and metadata.
    """
    # Restrict to common x bounds
    mask1 = (profile1['x'] >= xon) & (profile1['x'] <= xoff)
    mask2 = (profile2['x'] >= xon) & (profile2['x'] <= xoff)

    x1 = np.asarray(profile1.loc[mask1, 'x'].values, dtype=float)
    z1 = np.asarray(profile1.loc[mask1, 'z'].values, dtype=float)
    x2 = np.asarray(profile2.loc[mask2, 'x'].values, dtype=float)
    z2 = np.asarray(profile2.loc[mask2, 'z'].values, dtype=float)

    if len(x1) < 2 or len(x2) < 2:
        raise ValueError("Not enough points in common bounds to compute volume.")

    # Interpolate to a common grid
    x_common = np.linspace(max(x1[0], x2[0]), min(x1[-1], x2[-1]), num=100)
    z1_interp = np.interp(x_common, x1, z1)
    z2_interp = np.interp(x_common, x2, z2)

    # Clip elevations below the threshold
    h1 = np.maximum(0.0, z1_interp - elevation)
    h2 = np.maximum(0.0, z2_interp - elevation)

    # Compute volumes using trapezoidal rule
    volume1_ft3_per_ft = float(np.trapz(h1, x_common))
    volume2_ft3_per_ft = float(np.trapz(h2, x_common))

    volume1_cuyd_per_ft = float(volume1_ft3_per_ft) / 27.0
    volume2_cuyd_per_ft = float(volume2_ft3_per_ft) / 27.0

    # Calculate volume change
    volume_change = volume2_cuyd_per_ft - volume1_cuyd_per_ft

    return {
        'xon': xon,
        'xoff': xoff,
        'elevation': elevation,
        'volume1_cuyd_per_ft': volume1_cuyd_per_ft,
        'volume2_cuyd_per_ft': volume2_cuyd_per_ft,
        'volume_change_cuyd_per_ft': volume_change
    }

def compute_volume_change_between_surveys(profile1, profile2, elevation_bands: List[Tuple[float, ...]], x_bounds: Tuple[float, ...]):
    """
    Compute volume changes between two surveys within elevation bands and x bounds.

    Parameters:
        profile1 (pd.DataFrame): First survey profile with columns 'x' and 'z'.
        profile2 (pd.DataFrame): Second survey profile with columns 'x' and 'z'.
        elevation_bands (list of tuples): List of (zmin, zmax) elevation bands.
        x_bounds (tuple): (xon, xoff) x-direction bounds.

    Returns:
        list: List of dictionaries with volume change results for each band.
    """
    results = []
    xon, xoff = x_bounds

    # Restrict profiles to common x bounds
    mask1 = (profile1['x'] >= xon) & (profile1['x'] <= xoff)
    mask2 = (profile2['x'] >= xon) & (profile2['x'] <= xoff)

    x1 = np.asarray(profile1.loc[mask1, 'x'].values, dtype=float)
    z1 = np.asarray(profile1.loc[mask1, 'z'].values, dtype=float)
    x2 = np.asarray(profile2.loc[mask2, 'x'].values, dtype=float)
    z2 = np.asarray(profile2.loc[mask2, 'z'].values, dtype=float)

    if len(x1) < 2 or len(x2) < 2:
        raise ValueError("Not enough points in common bounds to compute volume.")

    # Interpolate to a common grid
    x_common = np.linspace(max(x1[0], x2[0]), min(x1[-1], x2[-1]), num=100)
    z1_interp = np.interp(x_common, x1, z1)
    z2_interp = np.interp(x_common, x2, z2)

    for zmin, zmax in elevation_bands:
        # Clip elevations to the band
        h1 = np.clip(z1_interp, zmin, zmax) - zmin
        h2 = np.clip(z2_interp, zmin, zmax) - zmin

        # Compute volumes using trapezoidal rule
        volume1 = float(np.trapz(h1, x_common)) / 27.0  # Convert ft³ to yd³
        volume2 = float(np.trapz(h2, x_common)) / 27.0

        # Calculate volume change
        volume_change = volume2 - volume1

        results.append({
            'xon': xon,
            'xoff': xoff,
            'zmin': zmin,
            'zmax': zmax,
            'volume1_cuyd_per_ft': float(volume1),
            'volume2_cuyd_per_ft': float(volume2),
            'volume_change_cuyd_per_ft': float(volume_change),
        })

    return results

def compute_cross_sectional_area(x, z, x_bounds, z_bounds):
    """
    Compute the cross-sectional area within specified x and z bounds.

    Parameters:
        x (list or np.ndarray): x-coordinates of the profile.
        z (list or np.ndarray): z-coordinates of the profile.
        x_bounds (tuple): (x_min, x_max) bounds for the x-coordinates.
        z_bounds (tuple): (z_min, z_max) bounds for the z-coordinates.

    Returns:
        float: Cross-sectional area in square feet.
    """
    x_min, x_max = x_bounds
    z_min, z_max = z_bounds

    # Clip the profile to the x bounds
    mask = (x >= x_min) & (x <= x_max)
    x_clipped = x[mask]
    z_clipped = z[mask]

    area = 0.0

    for i in range(len(x_clipped) - 1):
        xa, xb = x_clipped[i], x_clipped[i + 1]
        za, zb = z_clipped[i], z_clipped[i + 1]

        # Clip elevations to z bounds
        za = max(min(za, z_max), z_min)
        zb = max(min(zb, z_max), z_min)

        # Compute trapezoidal area
        area += 0.5 * (xb - xa) * (za + zb)

    return area

def validate_x_bounds(profile, xon, xoff):
    """
    Validate that the profile extends to the specified x bounds.

    Parameters:
        profile (pd.DataFrame): DataFrame with columns 'x' and 'z'.
        xon (float): Landward x-bound.
        xoff (float): Seaward x-bound.

    Returns:
        str: User decision if bounds are out of range ('extend', 'clip', 'skip').
    """
    x_min, x_max = profile['x'].min(), profile['x'].max()

    if xon < x_min or xoff > x_max:
        print(f"Warning: Specified bounds (xon={xon}, xoff={xoff}) exceed profile range ({x_min}, {x_max}).")
        print("Options:")
        print("  1. Extend: Extrapolate profile to the specified bounds.")
        print("  2. Clip: Adjust bounds to fit within the profile range.")
        print("  3. Skip: Exclude this profile from analysis.")

        while True:
            choice = input("Enter your choice (1=Extend, 2=Clip, 3=Skip): ").strip()
            if choice == '1':
                return 'extend'
            elif choice == '2':
                return 'clip'
            elif choice == '3':
                return 'skip'
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

    return 'valid'

# Add functionality to compute volume above contour for design template comparison
def compute_volume_above_contour(profile, contour, x_bounds):
    """
    Compute the volume above a specified contour within x bounds.

    Parameters:
        profile (pd.DataFrame): Profile data with columns 'x' and 'z'.
        contour (float): Contour elevation.
        x_bounds (tuple): (xon, xoff) x-direction bounds.

    Returns:
        float: Volume above the contour in cubic yards per foot.
    """
    xon, xoff = x_bounds
    mask = (profile['x'] >= xon) & (profile['x'] <= xoff)
    x = profile.loc[mask, 'x'].values
    z = profile.loc[mask, 'z'].values

    if len(x) < 2:
        raise ValueError("Not enough points within x bounds to compute volume.")

    return bmap_style_volume_above_contour(x, z, contour)


def load_template_from_bmap(bmap_file, profile_id):
    """
    Load design template geometry for a specific profile from BMAP Free Format file.

    Parameters:
        bmap_file (str): Path to BMAP file.
        profile_id (str): Profile ID to extract.

    Returns:
        pd.DataFrame: Template profile with 'x' and 'z' columns.
    """
    # Source: BMAP Free Format file - contains design template cross-sections
    parser = BMAPParser()
    profiles = parser.parse_file(bmap_file)

    for profile in profiles:
        if profile.name == profile_id:
            return pd.DataFrame({'x': profile.x, 'z': profile.z})

    raise ValueError(f"Profile '{profile_id}' not found in template BMAP file.")

def main():
    parser = argparse.ArgumentParser(description="Compute volume and cross-sectional area within elevation bands and x bounds.")
    parser.add_argument("--menu", action="store_true", help="Open interactive menu")
    parser.add_argument("--survey-csv", default="Input_Files/9Column_Data_Input.csv", help="Survey data CSV file.")
    parser.add_argument("--profile-csv", default="Input_Files/ProfileLine_Data_Input.csv", help="Profile metadata CSV file.")
    parser.add_argument("--template-bmap", default="Input_Files/DesignTemplate.bmap", help="BMAP Free Format file for design template geometry.")
    parser.add_argument("--profile-id", required=True, help="Profile ID to process.")
    parser.add_argument("--input2", help="Second survey CSV file for volume change (optional).")
    parser.add_argument("--output", required=True, help="Output CSV file for results.")
    parser.add_argument("--elevation-bands", nargs='+', required=True, help="Elevation bands as 'zmin,zmax'.")
    parser.add_argument("--contour", type=float, help="Contour elevation for design template comparison.")
    args = parser.parse_args()

    # If interactive menu requested, open it and exit
    if args.menu:
        menu()
        return

    # Load profile metadata
    # Source: ProfileLine_Data_Input.csv - contains profile bounds and geometry
    profile_meta = pd.read_csv(args.profile_csv)
    required_meta_columns = ['Profile_ID', 'Xon', 'Xoff']
    profile_meta = normalize_column_names(profile_meta, required_meta_columns)
    if not set(required_meta_columns).issubset(profile_meta.columns):
        raise ValueError(f"Profile CSV must contain columns: {', '.join(required_meta_columns)}")

    profile_row = profile_meta[profile_meta['Profile_ID'] == args.profile_id]
    if profile_row.empty:
        raise ValueError(f"Profile '{args.profile_id}' not found in metadata.")

    xon, xoff = profile_row['Xon'].iloc[0], profile_row['Xoff'].iloc[0]

    # Load first survey data
    # Source: 9Column_Data_Input.csv - contains survey elevations
    survey_data = pd.read_csv(args.survey_csv)
    required_survey_columns = ['PROFILE ID', 'ELEVATION (Z)']
    survey_data = normalize_column_names(survey_data, required_survey_columns)
    if not set(required_survey_columns).issubset(survey_data.columns):
        raise ValueError(f"Survey CSV must contain columns: {', '.join(required_survey_columns)}")

    profile1_survey = survey_data[survey_data['PROFILE ID'] == args.profile_id]
    if profile1_survey.empty:
        raise ValueError(f"No survey data for profile '{args.profile_id}'.")

    profile1 = pd.DataFrame({
        'x': range(len(profile1_survey)),  # Placeholder X
        'z': profile1_survey['ELEVATION (Z)'],
        'xon': xon,
        'xoff': xoff
    })

    # Normalize column names
    profile1 = normalize_column_names(profile1, ['x', 'z', 'xon', 'xoff'])

    # Parse elevation bands
    elevation_bands = [tuple(map(float, band.split(','))) for band in args.elevation_bands]

    results = []

    if args.input2:
        # Load second survey data for volume change
        # Source: Second survey file - assumed same format as first
        survey2_data = pd.read_csv(args.input2)
        profile2_survey = survey2_data[survey2_data['PROFILE ID'] == args.profile_id]
        profile2 = pd.DataFrame({
            'x': range(len(profile2_survey)),
            'z': profile2_survey['ELEVATION (Z)'],
            'xon': xon,
            'xoff': xoff
        })

        # Normalize column names
        profile2 = normalize_column_names(profile2, ['x', 'z', 'xon', 'xoff'])

        # Compute volume changes
        results.extend(compute_volume_change_between_surveys(profile1, profile2, elevation_bands, (xon, xoff)))

    if args.contour is not None:
        # Load design template from BMAP file
        # Source: BMAP Free Format file - contains full template cross-sections
        template = load_template_from_bmap(args.template_bmap, args.profile_id)

        # Compute volume above contour for design template comparison
        shortfall = compute_volume_above_contour(profile1, args.contour, (xon, xoff))
        template_volume = compute_volume_above_contour(template, args.contour, (xon, xoff))

        results.append({
            'comparison_type': 'survey_vs_template',
            'xon': xon,
            'xoff': xoff,
            'contour': args.contour,
            'survey_volume_cuyd_per_ft': shortfall,
            'template_volume_cuyd_per_ft': template_volume,
            'shortfall_cuyd_per_ft': template_volume - shortfall
        })

    # Save results to output CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(args.output, index=False)

def menu():
    """
    Menu-driven CLI for standalone_volume_bounded.py.
    Allows users to interact with the script's functions.
    """
    import sys

    def print_menu():
        print("\n--- Main Menu ---")
        print("1. Load and Parse Data")
        print("2. Compute Volume Above Contour")
        print("3. Compute Bounded Volume")
        print("4. Exit")

    def load_and_parse_data():
        print("\nLoading and parsing data...")
        try:
            input_dir = Path('./Input_Files')
            files = {
                'DesignTemplate_Data_Input.csv': pd.read_csv(input_dir / 'DesignTemplate_Data_Input.csv'),
                'ProfileLine_Data_Input.csv': pd.read_csv(input_dir / 'ProfileLine_Data_Input.csv'),
                'Project_Data_Input.csv': pd.read_csv(input_dir / 'Project_Data_Input.csv')
            }
            bmap_parser = BMAPParser()
            bmap_profiles = bmap_parser.parse_file(input_dir / 'ManasquanDesignTemplates.dat')
            print("\nData Loaded Successfully:")
            for name, df in files.items():
                print(f"{name}: {len(df)} rows")
            print(f"BMAP Profiles Parsed: {len(bmap_profiles)} profiles")
        except Exception as e:
            print(f"Error loading data: {e}")

    def compute_volume_above_contour():
        print("\nComputing volume above contour...")
        try:
            contour = float(input("Enter contour elevation: "))
            x = np.array([0, 10, 20, 30, 40])  # Example x-coordinates
            z = np.array([5, 15, 10, 20, 25])  # Example z-coordinates
            volume = bmap_style_volume_above_contour(x, z, contour)
            print(f"Volume above contour {contour}: {volume:.2f} cubic yards per foot")
        except Exception as e:
            print(f"Error computing volume: {e}")

    def compute_bounded_volume_menu():
        print("\nComputing bounded volume...")
        try:
            x_bounds = tuple(map(float, input("Enter x bounds (x_min, x_max): ").split(',')))
            z_bounds = tuple(map(float, input("Enter z bounds (z_min, z_max): ").split(',')))
            x = np.array([0, 10, 20, 30, 40])  # Example x-coordinates
            z = np.array([5, 15, 10, 20, 25])  # Example z-coordinates
            result = compute_bounded_volume(x, z, x_bounds, z_bounds)
            print(f"Volume within bounds {x_bounds} and {z_bounds}:")
            print(f"  Volume Above: {result['volume_above']:.2f}")
            print(f"  Volume Below: {result['volume_below']:.2f}")
        except Exception as e:
            print(f"Error computing bounded volume: {e}")

    while True:
        print_menu()
        choice = input("Enter your choice: ")
        if choice == '1':
            load_and_parse_data()
        elif choice == '2':
            compute_volume_above_contour()
        elif choice == '3':
            compute_bounded_volume_menu()
        elif choice == '4':
            print("Exiting program. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    # Uncomment the following line to run the menu by default
    # menu()
    main()

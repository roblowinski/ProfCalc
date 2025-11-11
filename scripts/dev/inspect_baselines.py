# =============================================================================
# Baseline Data Inspection Script
# =============================================================================
#
# FILE: scripts/dev/inspect_baselines.py
#
# PURPOSE:
# This development script inspects and displays baseline profile data from the
# ProfileOriginAzimuths.csv file. It provides a quick way to examine the structure
# and content of baseline data during development and debugging.
#
# WHAT IT'S FOR:
# - Inspecting baseline profile data structure
# - Verifying data loading functionality
# - Debugging baseline data issues
# - Understanding baseline data format and content
#
# WORKFLOW POSITION:
# This script is used during development to examine baseline data files and
# verify that data loading functions work correctly. It helps troubleshoot
# issues with baseline data processing.
#
# LIMITATIONS:
# - Only displays first few rows of data
# - Basic inspection without detailed analysis
# - Hardcoded file path for specific baseline file
# - Limited to profile origin and azimuth data
#
# ASSUMPTIONS:
# - Baseline file exists at expected location
# - Data loading function works correctly
# - File format matches expected structure
# - Required dependencies are available
#
# =============================================================================

from profcalc.common.csv_io import _load_profile_origin_azimuths

p = "src/profcalc/data/required_inputs/ProfileOriginAzimuths.csv"
df = _load_profile_origin_azimuths(p)
print(df.head())
print(df.dtypes)

# =============================================================================
# Shapefile Inspection Script (Variant)
# =============================================================================
#
# FILE: scripts/dev/inspect_shp2.py
#
# PURPOSE:
# This development script inspects the structure and content of a specific
# shapefile (bounds_both_20251107_144019_xon_xoff.shp). It displays schema
# information, coordinate reference system, and sample features for debugging
# and development purposes.
#
# WHAT IT'S FOR:
# - Inspecting specific shapefile schema and structure
# - Examining coordinate reference system information
# - Viewing sample feature properties from a particular file
# - Debugging shapefile processing for specific outputs
# - Understanding shapefile data format for development
#
# WORKFLOW POSITION:
# This script is used during development to examine specific shapefile outputs
# and verify that shapefile generation works correctly for particular cases.
# It helps troubleshoot issues with geospatial data processing.
#
# LIMITATIONS:
# - Only displays first few features
# - Hardcoded filename for specific shapefile
# - Basic inspection without spatial analysis
# - Limited to property inspection
#
# ASSUMPTIONS:
# - Specified shapefile exists at expected location
# - Fiona library is available and working
# - Shapefile is valid and readable
# - File follows expected geospatial format
#
# =============================================================================

import fiona

p='bounds_both_20251107_144019_xon_xoff.shp'
with fiona.open(p) as src:
    print('SCHEMA:', src.schema)
    print('CRS:', src.crs)
    for i,f in enumerate(src):
        print('FEATURE', i, f['properties'])
        if i>3:
            break

# =============================================================================
# Shapefile Inspection Script
# =============================================================================
#
# FILE: scripts/dev/inspect_shp.py
#
# PURPOSE:
# This development script inspects the structure and content of shapefile data.
# It displays schema information, coordinate reference system, and sample features
# to help understand shapefile format and content during development.
#
# WHAT IT'S FOR:
# - Inspecting shapefile schema and structure
# - Examining coordinate reference system information
# - Viewing sample feature properties
# - Debugging shapefile processing issues
# - Understanding shapefile data format
#
# WORKFLOW POSITION:
# This script is used during development to examine shapefile outputs and
# verify that shapefile generation and processing work correctly. It helps
# troubleshoot issues with geospatial data handling.
#
# LIMITATIONS:
# - Only displays first few features
# - Hardcoded filename for specific shapefile
# - Basic inspection without spatial analysis
# - Limited to property inspection
#
# ASSUMPTIONS:
# - Shapefile exists at specified location
# - Fiona library is available and working
# - Shapefile is valid and readable
# - File follows expected geospatial format
#
# =============================================================================

import fiona

p='bounds_both_20251107_142742_xon_xoff.shp'
with fiona.open(p) as src:
    print('SCHEMA:', src.schema)
    print('CRS:', src.crs)
    for i,f in enumerate(src):
        print('FEATURE', i, f['properties'])
        if i>3:
            break

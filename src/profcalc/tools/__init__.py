# =============================================================================
# ProfCalc Analysis Tools Package
# =============================================================================
#
# FILE: src/profcalc/tools/__init__.py
#
# PURPOSE:
# This package organizes all core analysis tools in ProfCalc, grouping them by
# functional domain and analysis type. It provides the main interface to the
# computational engine of ProfCalc, containing both replicas of USACE BMAP tools
# and extended analysis capabilities for coastal engineering applications.
#
# WHAT IT'S FOR:
# - Organizes analysis tools by functional domain (BMAP, monitoring, construction, etc.)
# - Provides access to core computational algorithms and methodologies
# - Supports both standard USACE BMAP tool replicas and extended analyses
# - Enables programmatic access to all analysis capabilities
# - Serves as the bridge between data processing and results generation
#
# WORKFLOW POSITION:
# This package sits at the heart of ProfCalc's analytical capabilities. It's
# used by CLI tools, automated scripts, and other applications that need to
# perform beach profile analysis. The tools here implement the core algorithms
# that transform raw survey data into meaningful engineering insights.
#
# LIMITATIONS:
# - Some tools are direct replicas of USACE BMAP and may have legacy limitations
# - Requires properly formatted input data for accurate results
# - Computational complexity may vary significantly between tools
# - Some analyses assume specific coordinate systems or data characteristics
#
# ASSUMPTIONS:
# - Input data has been validated and is in the expected format
# - Coordinate systems and units are consistent and appropriate
# - Analysis parameters are physically meaningful and properly specified
# - Users understand the engineering context and limitations of each tool
# - Computational resources are adequate for the selected analysis
#
# =============================================================================

"""
Tools namespace for profcalc.

Contains submodules grouped by functional domain:
- bmap: 1:1 replicas of USACE BMAP tools
- monitoring: annual and long-term profile analyses
- construction: beachfill and construction-phase tools
- storm_eval: event-based impact and response analyses
"""

__all__ = ["bmap", "monitoring", "construction", "storm_eval"]

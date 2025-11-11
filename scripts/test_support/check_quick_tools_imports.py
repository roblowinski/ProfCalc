# =============================================================================
# Quick Tools Import Check Script
# =============================================================================
#
# FILE: scripts/test_support/check_quick_tools_imports.py
#
# PURPOSE:
# This test support script performs quick import checks for quick-tools modules
# in the profcalc package. It verifies that key tool modules can be imported
# successfully, helping identify import issues during development and testing.
#
# WHAT IT'S FOR:
# - Testing importability of quick-tools modules
# - Verifying module availability for testing
# - Identifying import failures in tool components
# - Supporting quick validation of tool functionality
# - Providing diagnostic information for tool imports
#
# WORKFLOW POSITION:
# This script is used during testing and development to quickly verify that
# quick-tools modules are importable. It helps catch import-related issues
# before running more comprehensive tests.
#
# LIMITATIONS:
# - Only tests basic importability
# - Does not test module functionality
# - Limited to specific quick-tools modules
# - Basic error reporting only
#
# ASSUMPTIONS:
# - Package structure follows expected layout
# - Source directory is correctly configured
# - Listed modules exist and should be importable
# - Python environment has necessary dependencies
#
# =============================================================================

"""Quick import check for quick-tools modules."""
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The package `profcalc` is located under the `src/` directory in the repo.
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

modules = [
    "profcalc.cli.tools.bounds",
    "profcalc.cli.tools.inventory",
    "profcalc.cli.tools.convert",
    "profcalc.cli.tools.assign",
]

for m in modules:
    try:
        importlib.import_module(m)
        print(f"{m} OK")
    except (ImportError, ModuleNotFoundError) as e:
        print(f"{m} ERR: {e}")

print("Done.")

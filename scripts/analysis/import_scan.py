# =============================================================================
# Import Scanning and Validation Script
# =============================================================================
#
# FILE: scripts/analysis/import_scan.py
#
# PURPOSE:
# This script performs comprehensive import testing of all modules within the
# profcalc package. It attempts to import each module and reports any failures,
# helping identify import issues, missing dependencies, or syntax errors.
#
# WHAT IT'S FOR:
# - Testing importability of all profcalc modules
# - Identifying modules with import failures
# - Detecting syntax errors or missing dependencies
# - Providing diagnostic information for import issues
# - Supporting package integrity validation
#
# WORKFLOW POSITION:
# This script is used during development and testing to validate that all
# package modules can be imported successfully. It helps catch import-related
# issues early in the development process.
#
# LIMITATIONS:
# - Only tests static imports, not runtime imports
# - Cannot detect issues that occur during module execution
# - Limited diagnostic information for complex failures
# - May miss issues in conditional import blocks
#
# ASSUMPTIONS:
# - Package structure follows standard Python conventions
# - All dependencies are properly installed
# - Source directory is correctly configured
# - Modules are syntactically correct Python
#
# =============================================================================

import importlib
import os
import pkgutil
import sys
import traceback

# Walk package directory for profcalc modules
src_dir = os.path.join(os.getcwd(), 'src')
base = os.path.join(src_dir, 'profcalc')

# Ensure package root (src) is on sys.path so 'profcalc' is importable
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
modules = []
for finder, name, ispkg in pkgutil.walk_packages([base], prefix='profcalc.'):
    modules.append((name, ispkg))

print(f"Found {len(modules)} modules under profcalc")
failed = []
for name, ispkg in modules:
    try:
        importlib.import_module(name)
    except Exception:
        # Capture full traceback for diagnostics
        failed.append((name, traceback.format_exc()))

if not failed:
    print('All modules imported successfully')
    sys.exit(0)

print(f"{len(failed)} modules failed to import:")
for nm, tb in failed:
    print('\n--- FAILED:', nm)
    print(tb)

sys.exit(2)

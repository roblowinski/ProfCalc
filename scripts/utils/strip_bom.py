# =============================================================================
# BOM Strip Utility Script
# =============================================================================
#
# FILE: scripts/utils/strip_bom.py
#
# PURPOSE:
# This utility script removes Byte Order Mark (BOM) characters from the beginning
# of text files. BOM characters can cause issues with Python source files and
# are often added by text editors when saving with UTF-8 encoding.
#
# WHAT IT'S FOR:
# - Removing UTF-8 BOM from source files
# - Fixing encoding issues in Python files
# - Cleaning up files saved with BOM by text editors
# - Ensuring consistent file encoding
# - Preventing import or syntax errors caused by BOM

# WORKFLOW POSITION:
# This script is used as a utility during development and maintenance to clean
# up files that have been inadvertently saved with BOM characters. It helps
# maintain consistent file encoding across the project.

# LIMITATIONS:
# - Only removes UTF-8 BOM (EF BB BF)
# - Processes only the specified file
# - No recursive directory processing
# - Basic BOM detection only

# ASSUMPTIONS:
# - File exists at specified path
# - BOM is standard UTF-8 BOM if present
# - File permissions allow writing
# - BOM removal is safe for the file type

# =============================================================================

from pathlib import Path

p=Path('src/profcalc/cli/menu_system.py')
if not p.exists():
    print('file missing')
    raise SystemExit(2)
b = p.read_bytes()
if b.startswith(b'\xef\xbb\xbf'):
    p.write_bytes(b[3:])
    print('BOM removed')
else:
    print('No BOM present')

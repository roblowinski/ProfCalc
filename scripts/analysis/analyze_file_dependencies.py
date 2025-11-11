# =============================================================================
# File Dependency Analysis Script
# =============================================================================
#
# FILE: scripts/analysis/analyze_file_dependencies.py
#
# PURPOSE:
# This script performs detailed analysis of file dependencies within the ProfCalc
# project, mapping which Python files reference which data files. It helps identify
# dependencies for safe file relocation and refactoring operations.
#
# WHAT IT'S FOR:
# - Mapping Python file dependencies on data files
# - Identifying files that need path updates during refactoring
# - Analyzing file reference patterns and usage
# - Supporting safe data file reorganization
# - Providing detailed dependency reports for maintenance
#
# WORKFLOW POSITION:
# This script is used during project maintenance and refactoring to understand
# file relationships before making organizational changes. It ensures that
# data file moves don't break existing code dependencies.
#
# LIMITATIONS:
# - Analysis based on string pattern matching in code
# - May miss dynamic file references or imports
# - Does not analyze runtime dependencies
# - Limited to explicit file path references in code
#
# ASSUMPTIONS:
# - File references are explicit in source code
# - Python files follow standard import/reference patterns
# - File paths are correctly specified in code
# - No dynamic file generation or complex path construction
#
# =============================================================================

"""
Detailed mapping of data file dependencies.
Shows which Python files require which data files, for safe relocation.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

EXCLUDE_DIRS = {'.venv', '.git', '__pycache__', '.pytest_cache', '.mypy_cache',
                '.ruff_cache', '.history', '.specstory', 'dist', 'build', 'profcalc.egg-info'}


def get_all_python_files(root_dir: Path) -> List[Path]:
    """Get all Python files in the project."""
    python_files = []
    for file_path in root_dir.rglob('*.py'):
        if any(excluded in file_path.parts for excluded in EXCLUDE_DIRS):
            continue
        python_files.append(file_path)
    return python_files


def extract_file_references_detailed(file_path: Path) -> List[Tuple[str, int, str]]:
    """
    Extract file references with line numbers and context.
    Returns: [(filename, line_number, line_content), ...]
    """
    references = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            # Skip comments (but keep docstrings as they might have examples)
            stripped = line.strip()
            if stripped.startswith('#'):
                continue

            # Pattern 1: Direct file references with extensions
            patterns = [
                r'["\']([^"\']*\.(csv|txt|json|ini|cfg|toml|yml|yaml|shp|shx|dbf|prj))["\']',
                r'Path\(["\']([^"\']+\.(csv|txt|json|ini|cfg|toml|yml|yaml|shp|shx|dbf|prj))["\']',
                r'open\(["\']([^"\']+\.(csv|txt|json|ini|cfg|toml|yml|yaml))["\']',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        filename = match[0]
                    else:
                        filename = match

                    # Clean up the filename
                    filename = filename.strip()
                    if filename and not filename.startswith('http'):
                        references.append((filename, line_num, line.strip()))

    except (OSError, UnicodeDecodeError):
        pass

    return references


def categorize_reference(ref: str) -> str:
    """Categorize a file reference."""
    ref_lower = ref.lower()

    if 'config' in ref_lower or ref_lower.endswith('.json'):
        return 'CONFIG'
    elif 'required' in ref_lower or 'data' in ref_lower:
        return 'DATA'
    elif 'test' in ref_lower or 'temp' in ref_lower:
        return 'TEST'
    elif ref_lower.endswith(('.ini', '.cfg', '.toml', '.yml')):
        return 'PROJECT_CONFIG'
    elif 'output' in ref_lower:
        return 'OUTPUT'
    elif ref_lower.endswith('.shp') or ref_lower.endswith(('.shx', '.dbf', '.prj')):
        return 'SHAPEFILE'
    else:
        return 'OTHER'


def analyze_dependencies():
    """Analyze file dependencies in detail."""
    root_dir = Path(__file__).parent

    print("="*80)
    print("DETAILED FILE DEPENDENCY ANALYSIS")
    print("="*80)
    print("\nThis analysis shows which Python files depend on which data files.")
    print("Use this information to safely relocate data files.\n")

    # Get all Python files
    python_files = get_all_python_files(root_dir)

    # Build dependency map
    dependencies: Dict[str, List[Tuple[Path, int, str]]] = {}

    for py_file in python_files:
        refs = extract_file_references_detailed(py_file)
        for filename, line_num, line_content in refs:
            if filename not in dependencies:
                dependencies[filename] = []
            dependencies[filename].append((py_file, line_num, line_content))

    # Categorize dependencies
    by_category: Dict[str, List[Tuple[str, List[Tuple[Path, int, str]]]]] = {
        'PROJECT_CONFIG': [],
        'CONFIG': [],
        'DATA': [],
        'TEST': [],
        'OUTPUT': [],
        'SHAPEFILE': [],
        'OTHER': [],
    }

    for filename, refs in dependencies.items():
        category = categorize_reference(filename)
        by_category[category].append((filename, refs))

    # Print results by category

    # 1. PROJECT CONFIGURATION FILES
    if by_category['PROJECT_CONFIG']:
        print("="*80)
        print("🔧 PROJECT CONFIGURATION FILES (DO NOT MOVE)")
        print("="*80)
        print("These are root-level config files required by Python tools:\n")

        for filename, refs in sorted(by_category['PROJECT_CONFIG']):
            print(f"📄 {filename}")
            print(f"   Used by {len(refs)} file(s):")

            for py_file, line_num, line_content in refs[:3]:
                rel_py = py_file.relative_to(root_dir)
                print(f"   • {rel_py}:{line_num}")
                print(f"     {line_content[:70]}...")

            if len(refs) > 3:
                print(f"   ... and {len(refs) - 3} more references")
            print()

    # 2. APPLICATION CONFIGURATION
    if by_category['CONFIG']:
        print("="*80)
        print("⚙️  APPLICATION CONFIGURATION (CAN RELOCATE WITH CODE CHANGES)")
        print("="*80)
        print("These config files are loaded by application code:\n")

        for filename, refs in sorted(by_category['CONFIG']):
            print(f"📄 {filename}")
            print(f"   Used by {len(refs)} file(s):")

            unique_files = set()
            for py_file, line_num, line_content in refs:
                unique_files.add(py_file)

            for py_file in sorted(unique_files):
                rel_py = py_file.relative_to(root_dir)
                # Get all references from this file
                file_refs = [(ln, lc) for pf, ln, lc in refs if pf == py_file]
                print(f"   • {rel_py} ({len(file_refs)} reference(s))")
                for line_num, line_content in file_refs[:2]:
                    print(f"     Line {line_num}: {line_content[:60]}...")
            print()

    # 3. DATA FILES
    if by_category['DATA']:
        print("="*80)
        print("📊 DATA FILES (CAN RELOCATE - UPDATE PATHS)")
        print("="*80)
        print("These are input data files referenced by the application:\n")

        for filename, refs in sorted(by_category['DATA']):
            print(f"📄 {filename}")

            # Check if file exists
            file_exists = False
            for search_path in [root_dir, root_dir / 'data', root_dir / 'src' / 'profcalc' / 'data']:
                if (search_path / filename).exists():
                    file_exists = True
                    actual_path = search_path / filename
                    rel_actual = actual_path.relative_to(root_dir)
                    print(f"   Location: {rel_actual}")
                    break

            if not file_exists:
                print("   Location: NOT FOUND (may be dynamically named)")

            print(f"   Used by {len(refs)} file(s):")

            unique_files = set()
            for py_file, line_num, line_content in refs:
                unique_files.add(py_file)

            for py_file in sorted(unique_files):
                rel_py = py_file.relative_to(root_dir)
                file_refs = [(ln, lc) for pf, ln, lc in refs if pf == py_file]
                print(f"   • {rel_py} ({len(file_refs)} reference(s))")
            print()

    # 4. TEST FILES
    if by_category['TEST']:
        print("="*80)
        print("🧪 TEST DATA FILES (CAN RELOCATE - UPDATE TEST PATHS)")
        print("="*80)
        print("These are test data files used by unit tests:\n")

        for filename, refs in sorted(by_category['TEST']):
            # Only show if used by non-test files (test-only files are less critical)
            non_test_refs = [r for r in refs if 'test' not in str(r[0]).lower()]

            if non_test_refs:
                status = "⚠️  CRITICAL"
            else:
                status = "✓ TEST-ONLY"

            print(f"{status} {filename}")
            print(f"   Used by {len(refs)} file(s):")

            unique_files = set()
            for py_file, line_num, line_content in refs:
                unique_files.add(py_file)

            for py_file in sorted(unique_files)[:5]:
                rel_py = py_file.relative_to(root_dir)
                file_refs = [(ln, lc) for pf, ln, lc in refs if pf == py_file]
                print(f"   • {rel_py} ({len(file_refs)} reference(s))")

            if len(unique_files) > 5:
                print(f"   ... and {len(unique_files) - 5} more files")
            print()

    # 5. OUTPUT FILES
    if by_category['OUTPUT']:
        print("="*80)
        print("📤 OUTPUT FILES (SAFE TO MOVE - NOT REQUIRED AS INPUT)")
        print("="*80)
        print("These are output files that are written by the application:\n")

        for filename, refs in sorted(by_category['OUTPUT']):
            print(f"📄 {filename}")
            print(f"   Referenced by {len(refs)} file(s) (likely for writing)")

            unique_files = set()
            for py_file, line_num, line_content in refs:
                unique_files.add(py_file)

            for py_file in sorted(unique_files)[:3]:
                rel_py = py_file.relative_to(root_dir)
                print(f"   • {rel_py}")

            if len(unique_files) > 3:
                print(f"   ... and {len(unique_files) - 3} more files")
            print()

    # 6. SHAPEFILES
    if by_category['SHAPEFILE']:
        print("="*80)
        print("🗺️  SHAPEFILE DATA (RELOCATE AS SETS)")
        print("="*80)
        print("Shapefiles come in sets (.shp, .shx, .dbf, .prj) - move together:\n")

        # Group by base name
        shapefile_sets: Dict[str, List[str]] = {}
        for filename, refs in by_category['SHAPEFILE']:
            base = Path(filename).stem
            if base not in shapefile_sets:
                shapefile_sets[base] = []
            shapefile_sets[base].append(filename)

        for base_name, files in sorted(shapefile_sets.items()):
            print(f"📦 {base_name} shapefile set:")
            for f in sorted(files):
                refs = dependencies.get(f, [])
                print(f"   • {f} (used by {len(refs)} file(s))")

            # Show which Python files use this shapefile
            all_refs = []
            for f in files:
                all_refs.extend(dependencies.get(f, []))

            unique_files = set(r[0] for r in all_refs)
            if unique_files:
                print("   Used by:")
                for py_file in sorted(unique_files):
                    rel_py = py_file.relative_to(root_dir)
                    print(f"     - {rel_py}")
            print()

    # SUMMARY AND RECOMMENDATIONS
    print("="*80)
    print("📋 SUMMARY & RELOCATION RECOMMENDATIONS")
    print("="*80)

    total_files = len(dependencies)
    config_files = len(by_category['PROJECT_CONFIG']) + len(by_category['CONFIG'])
    data_files = len(by_category['DATA'])
    test_files = len(by_category['TEST'])
    output_files = len(by_category['OUTPUT'])

    print(f"\nTotal files referenced: {total_files}")
    print(f"  🔧 Project config (DO NOT MOVE): {len(by_category['PROJECT_CONFIG'])}")
    print(f"  ⚙️  App config (relocate with updates): {len(by_category['CONFIG'])}")
    print(f"  📊 Data files (relocate with path updates): {data_files}")
    print(f"  🧪 Test files (relocate with test updates): {test_files}")
    print(f"  📤 Output files (safe to move): {output_files}")
    print(f"  🗺️  Shapefiles (move as sets): {len(by_category['SHAPEFILE'])}")

    print("\n💡 RELOCATION STRATEGY:")
    print("\n1. CREATE NEW DIRECTORY STRUCTURE:")
    print("   data/")
    print("   ├── input/         # Move DATA files here")
    print("   ├── test/          # Move TEST files here")
    print("   ├── output/        # Move OUTPUT files here")
    print("   └── config/        # Move CONFIG .json files here")

    print("\n2. UPDATE CODE:")
    print("   - Search for hardcoded paths in the files listed above")
    print("   - Replace with configurable path variables")
    print("   - Consider using Path(__file__).parent for relative paths")

    print("\n3. CRITICAL FILES (verify before moving):")
    critical = []
    for filename, refs in dependencies.items():
        non_test_refs = [r for r in refs if 'test' not in str(r[0]).lower()]
        if len(non_test_refs) >= 3:  # Used by 3+ non-test files
            critical.append((filename, len(non_test_refs)))

    for filename, count in sorted(critical, key=lambda x: x[1], reverse=True)[:10]:
        print(f"   • {filename} (used by {count} non-test files)")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    analyze_dependencies()

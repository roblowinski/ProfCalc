# =============================================================================
# Project Structure Analysis Script
# =============================================================================
#
# FILE: scripts/maintenance/analyze_structure.py
#
# PURPOSE:
# This maintenance script analyzes the overall project structure and identifies
# opportunities for reorganization. It provides insights into file distribution,
# folder organization, and potential improvements to project layout.
#
# WHAT IT'S FOR:
# - Analyzing overall project folder structure
# - Identifying file distribution patterns
# - Assessing organization effectiveness
# - Providing recommendations for structural improvements
# - Supporting project maintenance and refactoring
#
# WORKFLOW POSITION:
# This script is used during project maintenance to evaluate the current
# organization and identify areas for improvement. It helps ensure the project
# structure remains logical and maintainable as the codebase evolves.
#
# LIMITATIONS:
# - Basic structural analysis without content examination
# - Cannot assess code quality or functionality
# - Limited to file and folder counting
# - May not detect all organizational issues
#
# ASSUMPTIONS:
# - Standard Python project structure conventions
# - Files are organized by functional purpose
# - Directory structure reflects logical grouping
# - Excluded directories are properly identified
#
# =============================================================================

"""
Analyze project structure and identify reorganization opportunities.
"""
from collections import defaultdict
from pathlib import Path


def analyze_project_structure():
    root = Path(".")

    # Exclude patterns
    exclude = {'.venv', '.git', '__pycache__', '.pytest_cache', '.mypy_cache',
               '.ruff_cache', '.history', '.specstory', 'profcalc.egg-info'}

    structure = {
        'root_scripts': [],
        'root_docs': [],
        'scripts_folder': [],
        'src_structure': defaultdict(list),
        'tests_structure': defaultdict(list),
        'data_structure': defaultdict(list),
        'docs_structure': defaultdict(list),
        'config_structure': defaultdict(list),
    }

    # Root level files
    for item in root.glob('*'):
        if item.is_file():
            if item.suffix == '.py':
                structure['root_scripts'].append(item.name)
            elif item.suffix == '.md':
                structure['root_docs'].append(item.name)

    # Scripts folder
    scripts_dir = root / 'scripts'
    if scripts_dir.exists():
        for item in scripts_dir.rglob('*.py'):
            rel = item.relative_to(scripts_dir)
            structure['scripts_folder'].append(str(rel))

    # Src structure
    src_dir = root / 'src' / 'profcalc'
    if src_dir.exists():
        for item in src_dir.iterdir():
            if item.is_dir() and item.name not in exclude:
                py_files = list(item.rglob('*.py'))
                structure['src_structure'][item.name] = len(py_files)

    # Tests structure
    tests_dir = root / 'tests'
    if tests_dir.exists():
        test_files = [f.name for f in tests_dir.glob('test_*.py')]
        structure['tests_structure']['test_files'] = len(test_files)
        for item in tests_dir.iterdir():
            if item.is_dir() and item.name not in exclude:
                count = len(list(item.rglob('*')))
                structure['tests_structure'][f'subdir_{item.name}'] = count

    # Data structure
    data_dir = root / 'data'
    if data_dir.exists():
        for category in data_dir.iterdir():
            if category.is_dir():
                for subdir in category.iterdir():
                    if subdir.is_dir():
                        files = list(subdir.glob('*'))
                        structure['data_structure'][f'{category.name}/{subdir.name}'] = len(files)

    # Docs structure
    docs_dir = root / 'docs'
    if docs_dir.exists():
        for category in docs_dir.iterdir():
            if category.is_dir():
                files = list(category.glob('*.md'))
                structure['docs_structure'][category.name] = len(files)

    # Config structure
    config_dir = root / 'config'
    if config_dir.exists():
        for subdir in config_dir.iterdir():
            if subdir.is_dir():
                files = list(subdir.glob('*'))
                structure['config_structure'][subdir.name] = len(files)

    return structure

def print_analysis(structure):
    print("="*80)
    print("PROJECT STRUCTURE ANALYSIS")
    print("="*80)

    print("\n### ROOT LEVEL")
    print(f"\nPython scripts ({len(structure['root_scripts'])}):")
    for script in sorted(structure['root_scripts']):
        print(f"  - {script}")

    print(f"\nMarkdown docs ({len(structure['root_docs'])}):")
    for doc in sorted(structure['root_docs']):
        print(f"  - {doc}")

    print("\n### SCRIPTS FOLDER")
    print(f"Python files ({len(structure['scripts_folder'])}):")
    for script in sorted(structure['scripts_folder']):
        print(f"  - {script}")

    print("\n### SRC STRUCTURE (src/profcalc/)")
    for dir_name, count in sorted(structure['src_structure'].items()):
        print(f"  - {dir_name}/: {count} Python files")

    print("\n### TESTS STRUCTURE")
    for key, count in sorted(structure['tests_structure'].items()):
        print(f"  - {key}: {count}")

    print("\n### DATA STRUCTURE")
    for path, count in sorted(structure['data_structure'].items()):
        print(f"  - {path}: {count} files")

    print("\n### DOCS STRUCTURE")
    for category, count in sorted(structure['docs_structure'].items()):
        print(f"  - {category}/: {count} markdown files")

    print("\n### CONFIG STRUCTURE")
    for subdir, count in sorted(structure['config_structure'].items()):
        print(f"  - {subdir}/: {count} files")

    print("\n" + "="*80)
    print("REORGANIZATION OPPORTUNITIES")
    print("="*80)

    opportunities = []

    # Root level scripts
    if structure['root_scripts']:
        opportunities.append({
            'priority': 'HIGH',
            'category': 'Root Python Scripts',
            'issue': f"{len(structure['root_scripts'])} analysis scripts cluttering root",
            'recommendation': 'Move to scripts/ or archive/ folder',
            'files': structure['root_scripts']
        })

    # Scripts folder organization
    if len(structure['scripts_folder']) > 10:
        opportunities.append({
            'priority': 'MEDIUM',
            'category': 'Scripts Organization',
            'issue': f"{len(structure['scripts_folder'])} scripts in scripts/ - may need categorization",
            'recommendation': 'Consider grouping into subdirectories by purpose',
            'files': None
        })

    # Display opportunities
    for i, opp in enumerate(opportunities, 1):
        print(f"\n{i}. [{opp['priority']}] {opp['category']}")
        print(f"   Issue: {opp['issue']}")
        print(f"   Recommendation: {opp['recommendation']}")
        if opp['files']:
            print(f"   Files: {', '.join(opp['files'][:5])}")
            if len(opp['files']) > 5:
                print(f"          ... and {len(opp['files']) - 5} more")

if __name__ == '__main__':
    structure = analyze_project_structure()
    print_analysis(structure)

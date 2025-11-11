# =============================================================================
# Data File Organization Analysis Script
# =============================================================================
#
# FILE: scripts/analysis/analyze_file_organization.py
#
# PURPOSE:
# This script analyzes the organization of data files within the ProfCalc project
# and provides recommendations for a logical folder structure. It categorizes
# files by their purpose and usage patterns, helping maintain a clean and
# organized codebase for data management.
#
# WHAT IT'S FOR:
# - Analyzing current file organization patterns
# - Categorizing data files by purpose and type
# - Recommending logical folder structures
# - Identifying files that need path updates
# - Supporting project maintenance and refactoring
#
# WORKFLOW POSITION:
# This script is used during project maintenance and refactoring phases to
# assess and improve data file organization. It helps ensure that data files
# are properly categorized and stored in appropriate locations for better
# maintainability and collaboration.
#
# LIMITATIONS:
# - Analysis is based on file naming patterns and paths
# - May not capture all contextual relationships between files
# - Recommendations are suggestions, not absolute requirements
# - Does not automatically reorganize files
#
# ASSUMPTIONS:
# - File naming conventions follow project standards
# - Directory structure reflects functional organization
# - Files are appropriately named for their content/purpose
# - Project follows standard Python packaging conventions
#
# =============================================================================

"""
Categorize data files and suggest organized folder structure.
Analyzes file usage patterns to recommend logical groupings.
"""

from pathlib import Path
from typing import Dict, List, Tuple

EXCLUDE_DIRS = {'.venv', '.git', '__pycache__', '.pytest_cache', '.mypy_cache',
                '.ruff_cache', '.history', '.specstory', 'dist', 'build', 'profcalc.egg-info'}


def get_all_data_files(root_dir: Path) -> List[Path]:
    """Get all data files in the project."""
    extensions = {'.csv', '.txt', '.json', '.ini', '.cfg', '.toml', '.yml',
                  '.shp', '.shx', '.dbf', '.prj'}

    data_files = []
    for ext in extensions:
        for file_path in root_dir.rglob(f'*{ext}'):
            if any(excluded in file_path.parts for excluded in EXCLUDE_DIRS):
                continue
            data_files.append(file_path)
    return data_files


def categorize_data_file(file_path: Path, root_dir: Path) -> Tuple[str, str, str]:
    """
    Categorize a data file by purpose.
    Returns: (category, subcategory, reason)
    """
    rel_path = file_path.relative_to(root_dir)
    name = file_path.name.lower()
    path_str = str(rel_path).lower()

    # Project configuration files (root level)
    if file_path.parent == root_dir:
        if name in ['pyproject.toml', 'setup.cfg', 'requirements.txt']:
            return ('PROJECT_ROOT', 'python_packaging', 'Python project configuration')
        elif name in ['pytest.ini', 'mypy.ini']:
            return ('PROJECT_ROOT', 'dev_tools', 'Development tool configuration')
        elif name.startswith('output_'):
            return ('OUTPUTS', 'script_results', 'Output from analysis runs')
        elif name in ['test_bmap.txt', 'test_no_id.csv']:
            return ('TEST_DATA', 'quick_tests', 'Quick test data files')
        elif name == 'menu_list.txt':
            return ('DOCUMENTATION', 'reference', 'Documentation reference')

    # GitHub configuration
    if '.github' in rel_path.parts:
        if 'workflows' in rel_path.parts:
            return ('PROJECT_ROOT', 'ci_cd', 'CI/CD configuration')
        else:
            return ('PROJECT_ROOT', 'github_config', 'GitHub configuration')

    # VS Code configuration
    if '.vscode' in rel_path.parts:
        return ('PROJECT_ROOT', 'editor_config', 'Editor configuration')

    # Application configuration
    if name == 'menu_data.json':
        return ('APP_CONFIG', 'menu_system', 'Menu system configuration')

    if name in ['config.json', 'analysis_config.json']:
        return ('APP_CONFIG', 'runtime', 'Runtime configuration')

    # Profile/baseline data
    if 'profileoriginazimuth' in name or 'beach_profile_network' in name:
        return ('REFERENCE_DATA', 'baselines', 'Profile baseline definitions')

    if 'profileline' in name or 'project_data' in name:
        return ('REFERENCE_DATA', 'project_metadata', 'Project and profile metadata')

    # Input data files
    if 'required_inputs' in path_str or 'required' in path_str:
        if '9col' in name or '4col' in name or '3col' in name:
            return ('SAMPLE_DATA', 'format_examples', 'Sample data in various formats')
        elif 'bmap' in name:
            return ('SAMPLE_DATA', 'bmap_format', 'BMAP format examples')
        elif 'origin' in name or 'azimuth' in name:
            return ('REFERENCE_DATA', 'baselines', 'Baseline/origin data')
        else:
            return ('SAMPLE_DATA', 'general', 'General sample data')

    # Test data in data/temp
    if 'data' in rel_path.parts and 'temp' in rel_path.parts:
        if name.startswith('output_'):
            return ('OUTPUTS', 'test_runs', 'Test run outputs')
        elif 'bounds' in name:
            return ('OUTPUTS', 'bounds_analysis', 'Bounds analysis outputs')
        elif file_path.suffix in ['.shp', '.shx', '.dbf', '.prj']:
            return ('OUTPUTS', 'shapefiles', 'Generated shapefile outputs')
        elif name == 'schema.ini':
            return ('APP_CONFIG', 'data_schemas', 'Data schema definitions')
        else:
            return ('SAMPLE_DATA', 'format_examples', 'Sample data for testing')

    # Test data used by unit tests
    if 'test' in path_str and file_path.suffix == '.csv':
        return ('TEST_DATA', 'unit_tests', 'Unit test fixtures')

    # Documentation files
    if 'docs' in rel_path.parts:
        if name.endswith('.txt'):
            return ('DOCUMENTATION', 'technical', 'Technical documentation')
        else:
            return ('DOCUMENTATION', 'general', 'General documentation')

    # Reference code data
    if 'ref_code' in rel_path.parts:
        return ('REFERENCE_DATA', 'legacy', 'Legacy reference implementation data')

    # Scan/processing data
    if 'scan' in path_str:
        return ('SAMPLE_DATA', 'processing', 'Data for processing/scanning')

    # Output files in temp folders
    if 'out_fix' in path_str or name.startswith('fixed_'):
        return ('OUTPUTS', 'corrections', 'Corrected/fixed data outputs')

    # Default categorization
    if file_path.suffix == '.json':
        return ('APP_CONFIG', 'other', 'Configuration file')
    elif file_path.suffix in ['.ini', '.cfg']:
        return ('APP_CONFIG', 'settings', 'Settings file')
    elif file_path.suffix in ['.shp', '.shx', '.dbf', '.prj']:
        return ('OUTPUTS', 'shapefiles', 'Shapefile data')
    elif 'output' in name:
        return ('OUTPUTS', 'general', 'Output file')
    else:
        return ('SAMPLE_DATA', 'other', 'Data file')


def analyze_and_categorize():
    """Analyze data files and suggest folder structure."""
    root_dir = Path(__file__).parent

    print("="*80)
    print("DATA FILE ORGANIZATION ANALYSIS")
    print("="*80)
    print("\nAnalyzing files to suggest organized folder structure...\n")

    # Get all data files
    data_files = get_all_data_files(root_dir)

    # Categorize files
    categories: Dict[str, Dict[str, List[Tuple[Path, str]]]] = {}

    for file_path in data_files:
        category, subcategory, reason = categorize_data_file(file_path, root_dir)

        if category not in categories:
            categories[category] = {}
        if subcategory not in categories[category]:
            categories[category][subcategory] = []

        categories[category][subcategory].append((file_path, reason))

    # Print organized structure
    print("="*80)
    print("RECOMMENDED FOLDER STRUCTURE")
    print("="*80)

    # Define order and descriptions
    category_info = {
        'PROJECT_ROOT': ('📦 PROJECT ROOT FILES', 'Keep in root - required by tools'),
        'APP_CONFIG': ('⚙️  APPLICATION CONFIGURATION', 'config/'),
        'REFERENCE_DATA': ('📍 REFERENCE DATA', 'data/reference/'),
        'SAMPLE_DATA': ('📊 SAMPLE & INPUT DATA', 'data/samples/'),
        'TEST_DATA': ('🧪 TEST FIXTURES', 'tests/fixtures/'),
        'OUTPUTS': ('📤 OUTPUT FILES', 'data/outputs/'),
        'DOCUMENTATION': ('📚 DOCUMENTATION DATA', 'docs/data/'),
    }

    total_files = 0

    for category_key, (category_name, suggested_path) in category_info.items():
        if category_key not in categories:
            continue

        print(f"\n{category_name}")
        print(f"Suggested location: {suggested_path}")
        print("-" * 80)

        category_total = sum(len(files) for files in categories[category_key].values())
        total_files += category_total

        for subcategory, files in sorted(categories[category_key].items()):
            print(f"\n  📁 {subcategory}/ ({len(files)} files)")

            # Group by file type
            by_type: Dict[str, List[Tuple[Path, str]]] = {}
            for file_path, reason in files:
                ext = file_path.suffix
                if ext not in by_type:
                    by_type[ext] = []
                by_type[ext].append((file_path, reason))

            for ext, ext_files in sorted(by_type.items()):
                print(f"    {ext}: {len(ext_files)} file(s)")
                for file_path, reason in sorted(ext_files)[:3]:
                    rel_path = file_path.relative_to(root_dir)
                    size_kb = file_path.stat().st_size / 1024
                    print(f"      • {file_path.name} ({size_kb:.1f} KB)")
                    print(f"        Current: {rel_path.parent}")

                if len(ext_files) > 3:
                    print(f"      ... and {len(ext_files) - 3} more {ext} files")

    # Print proposed directory structure
    print("\n" + "="*80)
    print("PROPOSED DIRECTORY STRUCTURE")
    print("="*80)
    print("""
Profile_Analysis/
├── config/                          # Application configuration
│   ├── menu_system/                 # Menu definitions
│   │   └── menu_data.json
│   ├── runtime/                     # Runtime settings
│   │   ├── config.json
│   │   └── analysis_config.json
│   ├── data_schemas/                # Data format schemas
│   │   └── schema.ini
│   └── settings/                    # Other settings
│
├── data/
│   ├── reference/                   # Reference/lookup data (CRITICAL)
│   │   ├── baselines/               # Profile baselines & origins
│   │   │   ├── ProfileOriginAzimuths.csv
│   │   │   └── beach_profile_network.csv
│   │   ├── project_metadata/        # Project definitions
│   │   │   ├── ProfileLine_Data_Input.csv
│   │   │   └── Project_Data_Input.csv
│   │   └── legacy/                  # Legacy reference data
│   │
│   ├── samples/                     # Sample input data
│   │   ├── format_examples/         # Various format examples
│   │   │   ├── 3Col_NoHeader__NoID.csv
│   │   │   ├── 4Col_WithHeader.csv
│   │   │   ├── 9Col_WithHeader.csv
│   │   │   └── ...
│   │   ├── bmap_format/             # BMAP format examples
│   │   │   ├── Bmap_FreeFormat_JustID.txt
│   │   │   └── ...
│   │   ├── processing/              # Data for processing tests
│   │   └── general/                 # Other sample data
│   │
│   └── outputs/                     # Generated outputs (can archive/delete)
│       ├── script_results/          # Analysis run results
│       │   ├── output_assign_4col.csv
│       │   ├── output_profile_scanner_*.txt
│       │   └── ...
│       ├── test_runs/               # Test execution outputs
│       ├── bounds_analysis/         # Bounds analysis results
│       ├── corrections/             # Corrected data files
│       │   └── report.txt
│       └── shapefiles/              # Generated shapefiles
│           └── output_bounds_x_*.*
│
├── tests/
│   └── fixtures/                    # Test data fixtures
│       ├── unit_tests/              # Unit test data
│       └── quick_tests/             # Quick test files
│           ├── test_bmap.txt
│           └── test_no_id.csv
│
├── docs/
│   └── data/                        # Documentation data files
│       ├── technical/               # Technical docs
│       │   ├── BMAP_Calcs_EdgeCases.txt
│       │   └── ChatHistory.txt
│       └── reference/               # Reference docs
│           └── tree.txt
│
└── [Root level]                     # Keep these in root
    ├── pyproject.toml               # Python packaging
    ├── setup.cfg
    ├── requirements.txt
    ├── pytest.ini                   # Dev tools config
    ├── mypy.ini
    ├── .vscode/                     # Editor config
    └── .github/                     # GitHub config
    """)

    print("\n" + "="*80)
    print("MIGRATION STATISTICS")
    print("="*80)

    print(f"\nTotal files to organize: {total_files}")
    print("\nBy category:")
    for category_key, (category_name, suggested_path) in category_info.items():
        if category_key in categories:
            count = sum(len(files) for files in categories[category_key].values())
            print(f"  {category_name[:40]:40s} {count:3d} files → {suggested_path}")

    print("\n" + "="*80)
    print("MIGRATION PRIORITY")
    print("="*80)

    print("""
1. HIGH PRIORITY - Create structure first:
   • config/                    - Application config files
   • data/reference/baselines/  - Critical baseline data
   • data/reference/project_metadata/ - Project definitions

2. MEDIUM PRIORITY - Organize existing data:
   • data/samples/              - Sample/example data files
   • tests/fixtures/            - Test data files

3. LOW PRIORITY - Archive outputs:
   • data/outputs/              - Generated outputs (can delete old ones)

4. KEEP IN PLACE:
   • Root config files (pyproject.toml, pytest.ini, etc.)
   • .vscode/, .github/ folders
""")

    print("\n" + "="*80)
    print("CRITICAL FILES TO UPDATE AFTER MIGRATION")
    print("="*80)

    critical_updates = [
        ('src/profcalc/cli/menu.py', 'menu_data.json path',
         'Update to: config/menu_system/menu_data.json'),
        ('src/profcalc/common/config_utils.py', 'config.json path',
         'Update to: config/runtime/config.json'),
        ('src/profcalc/cli/tools/bounds.py', 'ProfileOriginAzimuths.csv path',
         'Update to: data/reference/baselines/ProfileOriginAzimuths.csv'),
        ('src/profcalc/common/csv_io.py', 'ProfileOriginAzimuths.csv path',
         'Update to: data/reference/baselines/ProfileOriginAzimuths.csv'),
    ]

    print()
    for py_file, description, new_path in critical_updates:
        print(f"📝 {py_file}")
        print(f"   {description}")
        print(f"   → {new_path}\n")

    print("="*80)
    print("\n💡 RECOMMENDATION:")
    print("   1. Create the new folder structure")
    print("   2. Update hardcoded paths in Python files")
    print("   3. Move files in batches (config → reference → samples → outputs)")
    print("   4. Run tests after each batch to verify")
    print("   5. Archive old output files to save space")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    analyze_and_categorize()

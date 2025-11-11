# =============================================================================
# Unused Python Files Analysis Script
# =============================================================================
#
# FILE: scripts/analysis/analyze_unused_detailed.py
#
# PURPOSE:
# This script performs detailed analysis of potentially unused Python files in
# the ProfCalc project, categorizing them by risk level and providing removal
# recommendations. It helps maintain code quality by identifying dead code.
#
# WHAT IT'S FOR:
# - Identifying potentially unused Python files
# - Analyzing import relationships and dependencies
# - Categorizing files by removal risk level
# - Providing cleanup recommendations for maintenance
# - Supporting code quality and project organization
#
# WORKFLOW POSITION:
# This script is used during project maintenance and cleanup phases to identify
# and remove unused code. It helps keep the codebase lean and maintainable by
# eliminating dead code that may confuse developers or cause maintenance issues.
#
# LIMITATIONS:
# - Static analysis may miss dynamic imports or reflection
# - Cannot detect files used by external tools or scripts
# - Risk assessment is based on heuristics, not guaranteed accuracy
# - May flag legitimate but rarely used utility functions
#
# ASSUMPTIONS:
# - All relevant entry points are properly identified
# - Import statements follow standard Python conventions
# - Files not imported are truly unused
# - Project structure follows expected patterns
#
# =============================================================================

"""
Detailed analysis of potentially unused Python files.
Categorizes by risk level and provides removal recommendations.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

EXCLUDE_DIRS = {'.venv', '.git', '__pycache__', '.pytest_cache', '.mypy_cache',
                '.ruff_cache', '.history', '.specstory', 'dist', 'build', 'profcalc.egg-info'}

ENTRY_POINTS = {
    '__main__.py',
    'run_menu.py',
    'compute_aer_demo.py',
    'scan_typehints.py',
    'import_scan.py',
    'import_graph.py',
    'find_unused_files.py',
    'analyze_unused_detailed.py',
}


def get_all_python_files(root_dir: Path) -> List[Path]:
    """Get all Python files in the project, excluding certain directories."""
    python_files = []
    for file_path in root_dir.rglob('*.py'):
        if any(excluded in file_path.parts for excluded in EXCLUDE_DIRS):
            continue
        python_files.append(file_path)
    return python_files


def extract_imports(file_path: Path) -> Set[str]:
    """Extract all import statements from a Python file."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except (SyntaxError, UnicodeDecodeError, OSError):
        pass

    return imports


def has_main_block(file_path: Path) -> bool:
    """Check if file has 'if __name__ == "__main__":' block."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return 'if __name__ ==' in content and '__main__' in content
    except (OSError, UnicodeDecodeError):
        return False


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    try:
        return file_path.stat().st_size
    except OSError:
        return 0


def count_lines(file_path: Path) -> int:
    """Count non-empty lines in file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f if line.strip())
    except (OSError, UnicodeDecodeError):
        return 0


def categorize_file(file_path: Path, root_dir: Path) -> Tuple[str, str]:
    """
    Categorize file by removal safety and reason.
    Returns (category, reason)

    Categories:
    - SAFE: Very likely safe to remove
    - PROBABLY_SAFE: Likely safe but review recommended
    - REVIEW: Needs careful review before removal
    - KEEP: Should probably keep
    """
    rel_path = file_path.relative_to(root_dir)
    parts = rel_path.parts
    name = file_path.name

    # Empty __init__.py files
    if name == '__init__.py':
        lines = count_lines(file_path)
        if lines == 0:
            return ('SAFE', 'Empty package marker')
        else:
            return ('KEEP', f'Non-empty __init__.py ({lines} lines)')

    # Scripts directory
    if 'scripts' in parts:
        if has_main_block(file_path):
            return ('PROBABLY_SAFE', 'Standalone script with main block')
        return ('REVIEW', 'Script without main block - may be imported')

    # Reference code
    if 'ref_code' in parts:
        return ('PROBABLY_SAFE', 'Reference implementation (archive)')

    # Test utilities
    if 'tests' in parts and not name.startswith('test_'):
        lines = count_lines(file_path)
        if lines < 10:
            return ('SAFE', f'Small test utility ({lines} lines)')
        return ('REVIEW', 'Test utility - may be used')

    # BMAP tools
    if 'bmap' in parts and name.startswith('bmap_'):
        if has_main_block(file_path):
            return ('REVIEW', 'BMAP tool with CLI entry point')
        return ('REVIEW', 'BMAP tool library - may be CLI entry point')

    # Empty tool directories
    if name == '__init__.py' and any(x in parts for x in ['construction', 'monitoring', 'storm_eval']):
        return ('SAFE', 'Empty placeholder directory')

    # CLI tools
    if 'cli' in parts and 'tools' in parts:
        return ('REVIEW', 'CLI tool - may be dynamically imported')

    # Quick tools
    if 'quick_tools' in parts:
        return ('REVIEW', 'Quick tool - may be CLI entry point')

    # Common utilities
    if 'common' in parts:
        lines = count_lines(file_path)
        if lines < 20:
            return ('SAFE', f'Small unused utility ({lines} lines)')
        return ('REVIEW', f'Utility module - verify not dynamically imported ({lines} lines)')

    # Core modules
    if 'core' in parts:
        return ('REVIEW', 'Core module - verify not used')

    # Default
    lines = count_lines(file_path)
    return ('REVIEW', f'Needs investigation ({lines} lines)')


def analyze_unused_detailed():
    """Perform detailed analysis of unused files."""
    root_dir = Path(__file__).parent

    # Get all Python files
    all_files = get_all_python_files(root_dir)

    # Build file to module mapping
    file_to_module: Dict[Path, str] = {}
    for file_path in all_files:
        if 'src' in file_path.parts:
            try:
                src_idx = file_path.parts.index('src')
                module_parts = file_path.parts[src_idx + 1:]
                module_name = '.'.join(module_parts)
                if module_name.endswith('.py'):
                    module_name = module_name[:-3]
                if module_name.endswith('.__init__'):
                    module_name = module_name[:-9]
            except (ValueError, IndexError):
                module_name = file_path.stem
        else:
            module_name = file_path.stem

        file_to_module[file_path] = module_name

    # Collect all imports
    all_imports: Set[str] = set()
    for file_path in all_files:
        imports = extract_imports(file_path)
        all_imports.update(imports)

    # Find unused files
    unused_files = []
    for file_path in all_files:
        file_name = file_path.name
        module_name = file_to_module[file_path]

        # Skip entry points and test files
        if file_name in ENTRY_POINTS:
            continue
        if 'test' in file_path.parts or file_name.startswith('test_'):
            continue
        if file_name == 'conftest.py':
            continue

        # Check if imported
        is_imported = False
        checks = [
            module_name,
            module_name.split('.')[-1],
            file_path.stem,
        ]

        if 'profcalc' in module_name:
            profcalc_idx = module_name.index('profcalc')
            from_profcalc = module_name[profcalc_idx:]
            checks.append(from_profcalc)
            checks.append(from_profcalc.split('.')[-1])

        for check in checks:
            if check in all_imports:
                is_imported = True
                break

        if not is_imported:
            unused_files.append(file_path)

    # Categorize files
    categorized: Dict[str, List[Tuple[Path, str]]] = {
        'SAFE': [],
        'PROBABLY_SAFE': [],
        'REVIEW': [],
        'KEEP': [],
    }

    for file_path in unused_files:
        category, reason = categorize_file(file_path, root_dir)
        categorized[category].append((file_path, reason))

    # Print report
    print("="*80)
    print("DETAILED UNUSED FILE ANALYSIS")
    print("="*80)

    # SAFE TO REMOVE
    if categorized['SAFE']:
        print(f"\n{'='*80}")
        print(f"✅ SAFE TO REMOVE ({len(categorized['SAFE'])} files)")
        print(f"{'='*80}")
        print("These files are very likely safe to remove:\n")

        by_dir: Dict[str, List[Tuple[Path, str]]] = {}
        for file_path, reason in sorted(categorized['SAFE']):
            rel_path = file_path.relative_to(root_dir)
            dir_name = str(rel_path.parent)
            if dir_name not in by_dir:
                by_dir[dir_name] = []
            by_dir[dir_name].append((file_path, reason))

        for dir_name, files in sorted(by_dir.items()):
            print(f"\n{dir_name}/")
            for file_path, reason in files:
                rel_path = file_path.relative_to(root_dir)
                print(f"  ✓ {rel_path.name}")
                print(f"    → {reason}")

    # PROBABLY SAFE
    if categorized['PROBABLY_SAFE']:
        print(f"\n{'='*80}")
        print(f"⚠️  PROBABLY SAFE TO REMOVE ({len(categorized['PROBABLY_SAFE'])} files)")
        print(f"{'='*80}")
        print("These files are likely safe but recommend quick review:\n")

        by_dir: Dict[str, List[Tuple[Path, str]]] = {}
        for file_path, reason in sorted(categorized['PROBABLY_SAFE']):
            rel_path = file_path.relative_to(root_dir)
            dir_name = str(rel_path.parent)
            if dir_name not in by_dir:
                by_dir[dir_name] = []
            by_dir[dir_name].append((file_path, reason))

        for dir_name, files in sorted(by_dir.items()):
            print(f"\n{dir_name}/")
            for file_path, reason in files:
                rel_path = file_path.relative_to(root_dir)
                has_main = has_main_block(file_path)
                lines = count_lines(file_path)
                print(f"  ⚠️  {rel_path.name} ({lines} lines{', has main()' if has_main else ''})")
                print(f"    → {reason}")

    # NEEDS REVIEW
    if categorized['REVIEW']:
        print(f"\n{'='*80}")
        print(f"🔍 NEEDS REVIEW ({len(categorized['REVIEW'])} files)")
        print(f"{'='*80}")
        print("These files need careful investigation before removal:\n")

        by_dir: Dict[str, List[Tuple[Path, str]]] = {}
        for file_path, reason in sorted(categorized['REVIEW']):
            rel_path = file_path.relative_to(root_dir)
            dir_name = str(rel_path.parent)
            if dir_name not in by_dir:
                by_dir[dir_name] = []
            by_dir[dir_name].append((file_path, reason))

        for dir_name, files in sorted(by_dir.items()):
            print(f"\n{dir_name}/")
            for file_path, reason in files:
                rel_path = file_path.relative_to(root_dir)
                has_main = has_main_block(file_path)
                lines = count_lines(file_path)
                print(f"  🔍 {rel_path.name} ({lines} lines{', has main()' if has_main else ''})")
                print(f"    → {reason}")

    # KEEP
    if categorized['KEEP']:
        print(f"\n{'='*80}")
        print(f"🛑 KEEP ({len(categorized['KEEP'])} files)")
        print(f"{'='*80}")
        print("These files should probably be kept:\n")

        for file_path, reason in sorted(categorized['KEEP']):
            rel_path = file_path.relative_to(root_dir)
            print(f"  🛑 {rel_path}")
            print(f"    → {reason}")

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY & RECOMMENDATIONS")
    print(f"{'='*80}")
    print(f"Total unused files found: {len(unused_files)}")
    print(f"  ✅ Safe to remove: {len(categorized['SAFE'])}")
    print(f"  ⚠️  Probably safe: {len(categorized['PROBABLY_SAFE'])}")
    print(f"  🔍 Needs review: {len(categorized['REVIEW'])}")
    print(f"  🛑 Keep: {len(categorized['KEEP'])}")

    if categorized['SAFE']:
        print("\n💡 NEXT STEPS:")
        print("  1. Review the 'SAFE TO REMOVE' list")
        print("  2. Remove empty __init__.py files and small utilities")
        print("  3. Consider archiving reference code to a separate directory")
        print("  4. Review scripts directory for obsolete debug/test scripts")

    print(f"\n{'='*80}\n")

    # Generate removal script
    if categorized['SAFE']:
        print("\n📝 To remove SAFE files, you can run:")
        print("\n# PowerShell command to remove safe files:")
        for file_path, _ in categorized['SAFE']:
            rel_path = file_path.relative_to(root_dir)
            print(f"Remove-Item '{rel_path}'")


if __name__ == "__main__":
    analyze_unused_detailed()

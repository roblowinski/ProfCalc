# =============================================================================
# Unused Files Discovery Script
# =============================================================================
#
# FILE: scripts/analysis/find_unused_files.py
#
# PURPOSE:
# This script identifies potentially unused Python files in the codebase by
# analyzing import relationships. It helps maintain code quality by finding
# files that are not referenced or imported by other parts of the application.
#
# WHAT IT'S FOR:
# - Identifying Python files not imported by other modules
# - Analyzing code dependencies and usage patterns
# - Supporting codebase cleanup and maintenance
# - Detecting potentially obsolete or dead code
# - Providing insights for refactoring decisions
#
# WORKFLOW POSITION:
# This script is used during code maintenance and refactoring phases to
# identify unused code that can be safely removed. It helps keep the codebase
# clean and reduces maintenance overhead.
#
# LIMITATIONS:
# - Static analysis may miss dynamic imports
# - Cannot detect usage through reflection or external tools
# - May flag legitimate utility scripts as unused
# - Depends on accurate entry point identification
#
# ASSUMPTIONS:
# - All relevant entry points are properly configured
# - Import statements follow standard Python conventions
# - Files not imported are truly unused
# - Project structure follows expected patterns
#
# =============================================================================

"""
Find potentially unused Python files in the codebase.
Checks which Python files are never imported or referenced by other files.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set

# Directories to exclude from analysis
EXCLUDE_DIRS = {'.venv', '.git', '__pycache__', '.pytest_cache', '.mypy_cache',
                '.ruff_cache', '.history', '.specstory', 'dist', 'build', 'profcalc.egg-info'}

# Files that are entry points and won't be imported
ENTRY_POINTS = {
    '__main__.py',
    'run_menu.py',
    'compute_aer_demo.py',
    'scan_typehints.py',
    'import_scan.py',
    'import_graph.py',
    'find_unused_files.py',
}

# Files in scripts directory are typically standalone
SCRIPT_DIRS = {'scripts'}


def get_all_python_files(root_dir: Path) -> List[Path]:
    """Get all Python files in the project, excluding certain directories."""
    python_files = []
    for file_path in root_dir.rglob('*.py'):
        # Skip excluded directories
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
    except (SyntaxError, UnicodeDecodeError, OSError) as e:
        print(f"Warning: Could not parse {file_path}: {e}")

    return imports


def get_module_name(file_path: Path, root_dir: Path) -> str:
    """Convert a file path to its Python module name."""
    rel_path = file_path.relative_to(root_dir)
    parts = list(rel_path.parts)

    # Remove .py extension
    if parts[-1].endswith('.py'):
        parts[-1] = parts[-1][:-3]

    # Remove __init__ from module names
    if parts[-1] == '__init__':
        parts.pop()

    return '.'.join(parts)


def find_unused_files():
    """Find Python files that are never imported."""
    root_dir = Path(__file__).parent
    src_dir = root_dir / 'src'

    # Get all Python files
    all_files = get_all_python_files(root_dir)
    print(f"Found {len(all_files)} Python files")

    # Build a map of file paths to their module names
    file_to_module: Dict[Path, str] = {}
    module_to_file: Dict[str, Path] = {}

    for file_path in all_files:
        # Try to get module name relative to src directory if in src
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
        module_to_file[module_name] = file_path

    # Collect all imports from all files
    all_imports: Set[str] = set()
    file_imports: Dict[Path, Set[str]] = {}

    for file_path in all_files:
        imports = extract_imports(file_path)
        file_imports[file_path] = imports
        all_imports.update(imports)

    # Find files that are never imported
    unused_files = []
    for file_path in all_files:
        file_name = file_path.name
        module_name = file_to_module[file_path]

        # Skip entry points
        if file_name in ENTRY_POINTS:
            continue

        # Skip test files (they're executed, not imported)
        if 'test' in file_path.parts or file_name.startswith('test_'):
            continue

        # Skip conftest.py (pytest discovery file)
        if file_name == 'conftest.py':
            continue

        # Check if this module is imported anywhere
        is_imported = False

        # Check various forms of the module name
        checks = [
            module_name,
            module_name.split('.')[-1],  # Just the last part
            file_path.stem,  # Just the filename without extension
        ]

        # Also check with profcalc prefix
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

    # Report results
    print(f"\n{'='*80}")
    print(f"Potentially Unused Python Files ({len(unused_files)} found)")
    print(f"{'='*80}\n")

    if unused_files:
        # Group by directory
        by_dir: Dict[str, List[Path]] = {}
        for file_path in sorted(unused_files):
            rel_path = file_path.relative_to(root_dir)
            dir_name = str(rel_path.parent) if rel_path.parent != Path('.') else 'root'
            if dir_name not in by_dir:
                by_dir[dir_name] = []
            by_dir[dir_name].append(file_path)

        for dir_name, files in sorted(by_dir.items()):
            print(f"\n{dir_name}/")
            for file_path in files:
                rel_path = file_path.relative_to(root_dir)
                print(f"  - {rel_path}")
    else:
        print("No unused files found!")

    # Show some statistics
    print(f"\n{'='*80}")
    print("Statistics:")
    print(f"  Total Python files: {len(all_files)}")
    print(f"  Entry points (excluded): {len([f for f in all_files if f.name in ENTRY_POINTS])}")
    print(f"  Test files (excluded): {len([f for f in all_files if 'test' in f.parts or f.name.startswith('test_')])}")
    print(f"  Potentially unused: {len(unused_files)}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    find_unused_files()

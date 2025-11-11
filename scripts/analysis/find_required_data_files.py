# =============================================================================
# Required Data Files Discovery Script
# =============================================================================
#
# FILE: scripts/analysis/find_required_data_files.py
#
# PURPOSE:
# This script identifies data files (CSV, TXT, JSON, etc.) that are actually
# referenced and used by the Python codebase. It helps determine which data
# files are essential versus those that may be obsolete or unused.
#
# WHAT IT'S FOR:
# - Identifying data files referenced in Python code
# - Determining which files are actually needed by the application
# - Supporting cleanup of unused data files
# - Analyzing file usage patterns for project maintenance
# - Providing insights for data file organization
#
# WORKFLOW POSITION:
# This script is used during project maintenance and cleanup to identify
# essential data files. It helps ensure that only necessary files are kept
# in the project, reducing clutter and maintenance overhead.
#
# LIMITATIONS:
# - Based on static string pattern matching
# - May miss dynamically constructed file paths
# - Cannot detect files used by external tools or processes
# - Limited to explicit file references in code
#
# ASSUMPTIONS:
# - File references are explicit string literals in code
# - All necessary files are referenced in Python source
# - File extensions are standard and recognized
# - Project follows expected file organization patterns
#
# =============================================================================

"""
Find data files (CSV, TXT, etc.) that are referenced in Python code.
Identifies which non-Python files are actually needed by the codebase.
"""

import re
from pathlib import Path
from typing import Dict, List, Set

EXCLUDE_DIRS = {'.venv', '.git', '__pycache__', '.pytest_cache', '.mypy_cache',
                '.ruff_cache', '.history', '.specstory', 'dist', 'build', 'profcalc.egg-info'}

DATA_EXTENSIONS = {'.csv', '.txt', '.shp', '.shx', '.dbf', '.prj', '.json',
                   '.yaml', '.yml', '.ini', '.cfg', '.toml'}


def get_all_python_files(root_dir: Path) -> List[Path]:
    """Get all Python files in the project."""
    python_files = []
    for file_path in root_dir.rglob('*.py'):
        if any(excluded in file_path.parts for excluded in EXCLUDE_DIRS):
            continue
        python_files.append(file_path)
    return python_files


def get_all_data_files(root_dir: Path) -> List[Path]:
    """Get all data files in the project."""
    data_files = []
    for ext in DATA_EXTENSIONS:
        for file_path in root_dir.rglob(f'*{ext}'):
            if any(excluded in file_path.parts for excluded in EXCLUDE_DIRS):
                continue
            data_files.append(file_path)
    return data_files


def extract_file_references(file_path: Path) -> Set[str]:
    """Extract file path references from Python code."""
    references = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern 1: String literals with file extensions
        for ext in DATA_EXTENSIONS:
            # Find patterns like "file.csv", 'file.txt', etc.
            pattern = rf'["\']([^"\']*\{ext})["\']'
            matches = re.findall(pattern, content, re.IGNORECASE)
            references.update(matches)

        # Pattern 2: Path objects with file references
        # Path("file.csv"), Path('file.txt')
        path_pattern = r'Path\(["\']([^"\']+)["\']'
        matches = re.findall(path_pattern, content)
        references.update(matches)

        # Pattern 3: open() calls
        open_pattern = r'open\(["\']([^"\']+)["\']'
        matches = re.findall(open_pattern, content)
        references.update(matches)

        # Pattern 4: Common data file patterns in comments/strings
        # Look for test file names, data directory references
        test_file_pattern = r'["\']?(test_[a-zA-Z0-9_]+\.(csv|txt|shp))["\']?'
        matches = re.findall(test_file_pattern, content, re.IGNORECASE)
        references.update(m[0] for m in matches)

    except (OSError, UnicodeDecodeError) as e:
        print(f"Warning: Could not read {file_path}: {e}")

    return references


def normalize_path(ref: str) -> str:
    """Normalize a file reference to a comparable form."""
    # Remove leading/trailing slashes and backslashes
    ref = ref.strip('/\\')
    # Convert to forward slashes
    ref = ref.replace('\\', '/')
    # Convert to lowercase for comparison
    return ref.lower()


def find_required_data_files():
    """Find data files that are referenced in code."""
    root_dir = Path(__file__).parent

    print("="*80)
    print("SCANNING FOR REQUIRED DATA FILES")
    print("="*80)

    # Get all Python files
    python_files = get_all_python_files(root_dir)
    print(f"\nScanning {len(python_files)} Python files for file references...")

    # Extract all file references from Python code
    all_references: Set[str] = set()
    file_to_refs: Dict[Path, Set[str]] = {}

    for py_file in python_files:
        refs = extract_file_references(py_file)
        if refs:
            file_to_refs[py_file] = refs
            all_references.update(refs)

    print(f"Found {len(all_references)} file references in code")

    # Get all actual data files
    data_files = get_all_data_files(root_dir)
    print(f"Found {len(data_files)} data files in project\n")

    # Build a mapping of normalized names to actual files
    file_name_map: Dict[str, List[Path]] = {}
    for data_file in data_files:
        name = data_file.name.lower()
        if name not in file_name_map:
            file_name_map[name] = []
        file_name_map[name].append(data_file)

        # Also map relative paths
        try:
            rel_path = data_file.relative_to(root_dir)
            rel_key = str(rel_path).lower().replace('\\', '/')
            if rel_key not in file_name_map:
                file_name_map[rel_key] = []
            file_name_map[rel_key].append(data_file)
        except ValueError:
            pass

    # Match references to actual files
    referenced_files: Set[Path] = set()
    unreferenced_files: Set[Path] = set()

    for data_file in data_files:
        is_referenced = False

        # Check by filename
        if data_file.name.lower() in [normalize_path(ref) for ref in all_references]:
            is_referenced = True

        # Check by relative path
        try:
            rel_path = data_file.relative_to(root_dir)
            rel_str = str(rel_path).replace('\\', '/')
            if any(normalize_path(ref) in rel_str.lower() or
                   rel_str.lower() in normalize_path(ref)
                   for ref in all_references):
                is_referenced = True
        except ValueError:
            pass

        if is_referenced:
            referenced_files.add(data_file)
        else:
            unreferenced_files.add(data_file)

    # Print results
    print("="*80)
    print(f"REFERENCED FILES (KEEP - {len(referenced_files)} files)")
    print("="*80)

    if referenced_files:
        by_dir: Dict[str, List[Path]] = {}
        for file_path in sorted(referenced_files):
            rel_path = file_path.relative_to(root_dir)
            dir_name = str(rel_path.parent)
            if dir_name not in by_dir:
                by_dir[dir_name] = []
            by_dir[dir_name].append(file_path)

        for dir_name, files in sorted(by_dir.items()):
            print(f"\n{dir_name}/")
            for file_path in files:
                rel_path = file_path.relative_to(root_dir)
                size_kb = file_path.stat().st_size / 1024
                print(f"  ✅ {rel_path.name} ({size_kb:.1f} KB)")

    # Print unreferenced files
    print(f"\n{'='*80}")
    print(f"UNREFERENCED FILES (SAFE TO REMOVE - {len(unreferenced_files)} files)")
    print(f"{'='*80}")

    if unreferenced_files:
        by_dir: Dict[str, List[Path]] = {}
        for file_path in sorted(unreferenced_files):
            rel_path = file_path.relative_to(root_dir)
            dir_name = str(rel_path.parent)
            if dir_name not in by_dir:
                by_dir[dir_name] = []
            by_dir[dir_name].append(file_path)

        for dir_name, files in sorted(by_dir.items()):
            print(f"\n{dir_name}/")
            for file_path in files:
                rel_path = file_path.relative_to(root_dir)
                size_kb = file_path.stat().st_size / 1024
                print(f"  ❌ {rel_path.name} ({size_kb:.1f} KB)")

    # Print specific references by file
    print(f"\n{'='*80}")
    print("FILE REFERENCES BY PYTHON FILE")
    print(f"{'='*80}")

    for py_file, refs in sorted(file_to_refs.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        rel_py = py_file.relative_to(root_dir)
        print(f"\n{rel_py} ({len(refs)} references):")
        for ref in sorted(refs)[:5]:  # Show first 5
            print(f"  - {ref}")
        if len(refs) > 5:
            print(f"  ... and {len(refs) - 5} more")

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total data files found: {len(data_files)}")
    print(f"  ✅ Referenced in code (KEEP): {len(referenced_files)}")
    print(f"  ❌ Not referenced (SAFE TO REMOVE): {len(unreferenced_files)}")
    print("\nFile types breakdown:")

    ext_counts: Dict[str, int] = {}
    ext_refs: Dict[str, int] = {}
    for data_file in data_files:
        ext = data_file.suffix.lower()
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
        if data_file in referenced_files:
            ext_refs[ext] = ext_refs.get(ext, 0) + 1

    for ext in sorted(ext_counts.keys()):
        total = ext_counts[ext]
        ref = ext_refs.get(ext, 0)
        unref = total - ref
        print(f"  {ext:8s} Total: {total:3d}  Referenced: {ref:3d}  Unreferenced: {unref:3d}")

    print(f"\n{'='*80}\n")

    # Generate removal commands
    if unreferenced_files:
        print("💡 To remove unreferenced files, you can run:\n")
        print("# PowerShell commands:")
        for file_path in sorted(unreferenced_files)[:20]:  # Show first 20
            rel_path = file_path.relative_to(root_dir)
            print(f"Remove-Item '{rel_path}'")
        if len(unreferenced_files) > 20:
            print(f"# ... and {len(unreferenced_files) - 20} more files")


if __name__ == "__main__":
    find_required_data_files()

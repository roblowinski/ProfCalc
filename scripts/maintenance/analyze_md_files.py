# =============================================================================
# Markdown Files Analysis Script
# =============================================================================
#
# FILE: scripts/maintenance/analyze_md_files.py
#
# PURPOSE:
# This maintenance script analyzes markdown files in the project to identify
# outdated, redundant, or poorly organized documentation. It helps maintain
# documentation quality and organization during project evolution.
#
# WHAT IT'S FOR:
# - Analyzing markdown file organization and categorization
# - Identifying potentially redundant documentation
# - Assessing documentation freshness and relevance
# - Supporting documentation maintenance decisions
# - Providing insights for documentation cleanup
#
# WORKFLOW POSITION:
# This script is used during project maintenance to assess the state of
# documentation files. It helps identify areas where documentation may need
# updating, consolidation, or removal to keep the project's documentation
# current and useful.
#
# LIMITATIONS:
# - Basic file analysis without content examination
# - Cannot assess documentation quality or accuracy
# - Limited to file metadata and categorization
# - May not detect all documentation issues
#
# ASSUMPTIONS:
# - Markdown files follow expected naming conventions
# - File organization reflects documentation structure
# - File timestamps indicate last modification
# - Documentation is organized by functional areas
#
# =============================================================================

"""
Analyze markdown files to identify outdated or redundant documentation.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


def get_md_files(root_dir: Path) -> List[Path]:
    """Get all markdown files excluding certain directories."""
    exclude_dirs = {'.venv', '.git', '__pycache__', '.history', '.specstory',
                    'node_modules', 'dist', 'build'}

    md_files = []
    for file_path in root_dir.rglob('*.md'):
        if any(excluded in file_path.parts for excluded in exclude_dirs):
            continue
        md_files.append(file_path)
    return md_files


def analyze_md_files():
    """Analyze markdown files for redundancy and relevance."""
    root_dir = Path(__file__).parent
    md_files = get_md_files(root_dir)

    print("="*80)
    print(f"MARKDOWN FILE ANALYSIS ({len(md_files)} files)")
    print("="*80)

    # Categorize files
    categories: Dict[str, List[Tuple[Path, int, datetime]]] = {
        'root_docs': [],
        'github_config': [],
        'src_docs': [],
        'tool_specific': [],
        'workflow': [],
        'chatmodes': [],
    }

    for file_path in md_files:
        rel_path = file_path.relative_to(root_dir)
        parts = rel_path.parts
        name = file_path.name.upper()

        try:
            size = file_path.stat().st_size
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        except OSError:
            size = 0
            mtime = datetime.min

        # Categorize
        if '.github' in parts:
            if 'chatmodes' in parts:
                categories['chatmodes'].append((file_path, size, mtime))
            else:
                categories['github_config'].append((file_path, size, mtime))
        elif str(rel_path.parent) == '.':
            categories['root_docs'].append((file_path, size, mtime))
        elif 'docs' in parts:
            if any(x in name for x in ['WORKFLOW', 'IMPLEMENTATION', 'ROADMAP']):
                categories['workflow'].append((file_path, size, mtime))
            else:
                categories['tool_specific'].append((file_path, size, mtime))
        else:
            categories['src_docs'].append((file_path, size, mtime))

    # Check for duplicates
    print("\n" + "="*80)
    print("POTENTIAL DUPLICATES")
    print("="*80)

    base_names: Dict[str, List[Path]] = {}
    for file_path in md_files:
        base = file_path.stem.upper()
        # Normalize common variations
        base = base.replace('_', '').replace('-', '')
        if base not in base_names:
            base_names[base] = []
        base_names[base].append(file_path)

    found_dupes = False
    for base, paths in sorted(base_names.items()):
        if len(paths) > 1:
            found_dupes = True
            print(f"\n'{base}' appears {len(paths)} times:")
            for p in paths:
                rel = p.relative_to(root_dir)
                size_kb = p.stat().st_size / 1024
                print(f"  - {rel} ({size_kb:.1f} KB)")

    if not found_dupes:
        print("\nNo obvious duplicates found.")

    # Analysis by category
    print("\n" + "="*80)
    print("RECOMMENDATIONS BY CATEGORY")
    print("="*80)

    # Root docs
    if categories['root_docs']:
        print(f"\n📄 ROOT DOCUMENTATION ({len(categories['root_docs'])} files)")
        print("-" * 80)
        for file_path, size, mtime in sorted(categories['root_docs'], key=lambda x: x[0].name):
            rel = file_path.relative_to(root_dir)
            size_kb = size / 1024
            age_days = (datetime.now() - mtime).days

            status = "✅ KEEP"
            reason = ""

            if rel.name == "README.md":
                reason = "Main project documentation"
            elif rel.name == "README_RUN_HELP.md":
                reason = "User guide for running tools"
            elif rel.name == "ChatHistory.md":
                status = "⚠️  REVIEW"
                reason = "Personal chat log - consider archiving"
            elif rel.name == "DATA.md":
                reason = "Data format documentation"
            elif "MENU" in rel.name:
                status = "⚠️  REVIEW"
                reason = "Menu implementation notes - may be outdated"

            print(f"{status} {rel.name} ({size_kb:.1f} KB, {age_days}d old)")
            if reason:
                print(f"    → {reason}")

    # GitHub config
    if categories['github_config']:
        print(f"\n⚙️  GITHUB CONFIGURATION ({len(categories['github_config'])} files)")
        print("-" * 80)
        for file_path, size, mtime in sorted(categories['github_config'], key=lambda x: x[0].name):
            rel = file_path.relative_to(root_dir)
            size_kb = size / 1024
            print(f"✅ KEEP {rel} ({size_kb:.1f} KB)")
            print("    → Active GitHub/Copilot configuration")

    # Chat modes
    if categories['chatmodes']:
        print(f"\n💬 CHAT MODES ({len(categories['chatmodes'])} files)")
        print("-" * 80)
        for file_path, size, mtime in sorted(categories['chatmodes'], key=lambda x: x[0].name):
            rel = file_path.relative_to(root_dir)
            size_kb = size / 1024
            age_days = (datetime.now() - mtime).days

            status = "⚠️  REVIEW"
            reason = "Custom chat mode - verify still used"

            print(f"{status} {rel} ({size_kb:.1f} KB, {age_days}d old)")
            print(f"    → {reason}")

    # Documentation in src/profcalc/docs
    if categories['tool_specific']:
        print(f"\n📚 TOOL-SPECIFIC DOCUMENTATION ({len(categories['tool_specific'])} files)")
        print("-" * 80)

        keep_patterns = ['BMAP', 'CONVERSION', 'FORMAT', 'VALIDATION', 'SHAPEFILE',
                        'FEATURES', 'INDEX', 'CHANGELOG', 'ISSUES']
        review_patterns = ['COMPLETE', 'STATUS', 'GUIDE']

        for file_path, size, mtime in sorted(categories['tool_specific'], key=lambda x: x[0].name):
            rel = file_path.relative_to(root_dir)
            size_kb = size / 1024
            age_days = (datetime.now() - mtime).days
            name_upper = rel.name.upper()

            status = "✅ KEEP"
            reason = "Technical documentation"

            if any(p in name_upper for p in review_patterns):
                status = "⚠️  REVIEW"
                reason = "Status/guide doc - may be superseded"
            elif "INTEGRATION" in name_upper:
                status = "⚠️  REVIEW"
                reason = "Integration doc - verify current"

            print(f"{status} {rel.name} ({size_kb:.1f} KB, {age_days}d old)")
            print(f"    → {reason}")

    # Workflow documents
    if categories['workflow']:
        print(f"\n🔄 WORKFLOW DOCUMENTATION ({len(categories['workflow'])} files)")
        print("-" * 80)
        for file_path, size, mtime in sorted(categories['workflow'], key=lambda x: x[0].name):
            rel = file_path.relative_to(root_dir)
            size_kb = size / 1024
            age_days = (datetime.now() - mtime).days

            status = "⚠️  REVIEW"
            reason = "Workflow doc - may need updates as implementation changes"

            if "ROADMAP" in rel.name.upper():
                reason = "Roadmap - verify against current implementation"

            print(f"{status} {rel.name} ({size_kb:.1f} KB, {age_days}d old)")
            print(f"    → {reason}")

    # Other src docs
    if categories['src_docs']:
        print(f"\n📋 OTHER SOURCE DOCUMENTATION ({len(categories['src_docs'])} files)")
        print("-" * 80)
        for file_path, size, mtime in sorted(categories['src_docs'], key=lambda x: x[0].name):
            rel = file_path.relative_to(root_dir)
            size_kb = size / 1024
            age_days = (datetime.now() - mtime).days

            status = "✅ KEEP"
            reason = "Source documentation"

            if "README" in rel.name.upper():
                reason = "Module documentation"
            elif "CONFIGURATION" in rel.name.upper():
                reason = "Configuration documentation"

            print(f"{status} {rel.name} ({size_kb:.1f} KB, {age_days}d old)")
            print(f"    → {reason}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    total_keep = sum(1 for cat in categories.values() for f, s, m in cat if 'README' in f.name or 'BMAP' in f.name.upper())
    total_review = len(md_files) - total_keep

    print(f"Total markdown files: {len(md_files)}")
    print(f"  ✅ Likely keep: {total_keep}")
    print(f"  ⚠️  Need review: {total_review}")

    print("\n💡 RECOMMENDATIONS:")
    print("  1. Review ChatHistory.md - archive if it's personal notes")
    print("  2. Check MENU_*.md files - consolidate or update if outdated")
    print("  3. Review *_COMPLETE.md and *_STATUS.md - remove if superseded")
    print("  4. Verify workflow docs match current implementation")
    print("  5. Check chat modes - remove unused custom modes")

    # Check for README duplicates
    print("\n" + "="*80)
    print("README FILE CHECK")
    print("="*80)

    readme_files = [f for f in md_files if 'README' in f.name.upper()]
    if len(readme_files) > 1:
        print(f"\nFound {len(readme_files)} README files:")
        for rf in readme_files:
            rel = rf.relative_to(root_dir)
            size_kb = rf.stat().st_size / 1024
            print(f"  - {rel} ({size_kb:.1f} KB)")

        # Check if there's a duplicate in docs/
        root_readme = root_dir / "README_RUN_HELP.md"
        docs_readme = root_dir / "src" / "profcalc" / "docs" / "README_RUN_HELP.md"

        if root_readme.exists() and docs_readme.exists():
            print("\n⚠️  WARNING: README_RUN_HELP.md exists in both root and docs/")
            print("   Consider keeping only one version (probably the root one)")


if __name__ == "__main__":
    analyze_md_files()

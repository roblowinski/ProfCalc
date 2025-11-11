# =============================================================================
# Type Hint Quality Scanner Script
# =============================================================================
#
# FILE: scripts/analysis/scan_typehints.py
#
# PURPOSE:
# This script scans Python files for type hint quality and completeness. It
# analyzes functions, methods, and classes to identify missing or incomplete
# type annotations, helping maintain code quality and type safety.
#
# WHAT IT'S FOR:
# - Scanning Python files for missing type hints
# - Analyzing type annotation completeness
# - Generating reports on type hint quality
# - Supporting gradual typing adoption
# - Identifying areas needing type annotation improvements
#
# WORKFLOW POSITION:
# This script is used during development and code review to assess type hint
# coverage and quality. It helps maintain consistent typing practices across
# the codebase and supports static type checking efforts.
#
# LIMITATIONS:
# - Static analysis of source code only
# - Cannot verify type hint correctness
# - May not detect all typing issues
# - Limited to explicit type annotations
#
# ASSUMPTIONS:
# - Files are syntactically correct Python
# - Type hints follow standard Python typing conventions
# - Source files are accessible and readable
# - AST parsing is supported for the Python version
#
# =============================================================================

#!/usr/bin/env python3
"""
Type Hint Quality Scanner

Scans Python files for missing type hints and generates a report.
"""

import ast
import os
from typing import Dict, List


class TypeHintScanner:
    """Scans Python files for type hint quality issues."""

    def __init__(self):
        self.issues = []

    def scan_file(self, file_path: str) -> List[Dict]:
        """Scan a single file for type hint issues."""
        issues: List[Dict] = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)

            # Check functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_issues = self._check_function_type_hints(node, file_path)
                    issues.extend(func_issues)
                elif isinstance(node, ast.ClassDef):
                    class_issues = self._check_class_type_hints(node, file_path)
                    issues.extend(class_issues)

        except Exception as e:
            issues.append({
                'file': file_path,
                'type': 'file',
                'name': 'file',
                'issue': f'Parse error: {e}',
                'severity': 'high'
            })

        return issues

    def _check_function_type_hints(self, node: ast.FunctionDef, file_path: str) -> List[Dict]:
        """Check a function's type hints."""
        issues: List[Dict] = []

        # Skip private functions for now (they can have missing hints)
        if node.name.startswith('_'):
            return issues

        # Check return type annotation
        if node.returns is None:
            issues.append({
                'file': file_path,
                'type': 'function',
                'name': node.name,
                'issue': 'Missing return type annotation',
                'severity': 'medium'
            })

        # Check parameter type annotations
        missing_params = []
        for arg in node.args.args:
            if arg.arg != 'self' and arg.annotation is None:
                missing_params.append(arg.arg)

        if missing_params:
            issues.append({
                'file': file_path,
                'type': 'function',
                'name': node.name,
                'issue': f'Missing type hints for parameters: {", ".join(missing_params)}',
                'severity': 'medium'
            })

        return issues

    def _check_class_type_hints(self, node: ast.ClassDef, file_path: str) -> List[Dict]:
        """Check a class's type hints."""
        issues = []

        # Check if class has __init__ method
        init_method = None
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                init_method = item
                break

        if init_method:
            # Check __init__ parameters (skip self)
            missing_params = []
            for arg in init_method.args.args:
                if arg.arg != 'self' and arg.annotation is None:
                    missing_params.append(arg.arg)

            if missing_params:
                issues.append({
                    'file': file_path,
                    'type': 'class',
                    'name': node.name,
                    'issue': f'__init__ missing type hints for parameters: {", ".join(missing_params)}',
                    'severity': 'medium'
                })

        return issues

    def scan_directory(self, directory: str) -> List[Dict]:
        """Scan all Python files in a directory."""
        all_issues = []

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    issues = self.scan_file(file_path)
                    all_issues.extend(issues)

        return all_issues

    def print_report(self, issues: List[Dict]):
        """Print a formatted report of issues."""
        if not issues:
            print("No type hint issues found!")
            return

        # Group by severity
        by_severity: Dict[str, List[Dict]] = {'high': [], 'medium': [], 'low': []}
        for issue in issues:
            by_severity[issue['severity']].append(issue)

        print(f"Type Hint Quality Report ({len(issues)} issues)")
        print("=" * 60)

        for severity in ['high', 'medium', 'low']:
            sev_issues = by_severity[severity]
            if sev_issues:
                print(f"\n{severity.upper()} PRIORITY ({len(sev_issues)} issues):")
                for issue in sev_issues[:10]:  # Show first 10
                    print(f"  • {issue['file']}:{issue['type']} {issue['name']}")
                    print(f"    {issue['issue']}")

                if len(sev_issues) > 10:
                    print(f"    ... and {len(sev_issues) - 10} more")

        print(f"\nTotal: {len(issues)} issues")


def main():
    """Main entry point."""
    scanner = TypeHintScanner()

    # Scan the src directory
    print("Scanning src/ directory for type hint issues...")
    issues = scanner.scan_directory("src")

    scanner.print_report(issues)


if __name__ == "__main__":
    main()

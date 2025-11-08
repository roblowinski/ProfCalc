"""Tests for quick_tools thin wrappers.

These tests assert that the thin wrapper modules under
`profcalc.cli.quick_tools` expose the expected entry points and are
importable. The tests avoid executing heavy CLI logic; they only check
presence of symbols.
"""
import importlib
import sys
from pathlib import Path

# Ensure 'src' (which contains the 'profcalc' package) is on sys.path so
# tests can import the package when running from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def test_quick_tool_wrappers_present():
    modules = ["fix_bmap", "bounds", "inventory", "assign"]
    for name in modules:
        mod = importlib.import_module(f"profcalc.cli.quick_tools.{name}")
        assert hasattr(mod, "execute_from_cli"), f"{name} missing execute_from_cli"
        assert hasattr(mod, "execute_from_menu"), f"{name} missing execute_from_menu"


def test_package_dispatcher_present():
    pkg = importlib.import_module("profcalc.cli.quick_tools")
    assert hasattr(pkg, "execute_from_cli"), "package-level execute_from_cli missing"

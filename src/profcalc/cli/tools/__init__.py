# =============================================================================
# CLI Tools Package Initialization
# =============================================================================
#
# FILE: src/profcalc/cli/tools/__init__.py
#
# PURPOSE:
# This module initializes the CLI tools package, providing unified access to
# all command-line interface tools and utilities. It serves as the central
# import point for tool functionality and manages prototype module loading
# for development workflows.
#
# WHAT IT'S FOR:
# - Provides package-level imports for CLI tools
# - Manages development prototype module loading
# - Exports key tool functions for external access
# - Supports dynamic tool discovery and loading
#
# WORKFLOW POSITION:
# This module sits at the root of the CLI tools package, enabling imports
# from the tools directory. It's used by the CLI router and menu system
# to access tool functionality throughout the application.
#
# LIMITATIONS:
# - Prototype loading is development-environment specific
# - Module loading may fail if prototype paths are invalid
# - Dynamic imports require proper module structure
#
# ASSUMPTIONS:
# - Tool modules are properly structured and importable
# - Prototype paths are correctly configured for development
# - Package structure supports dynamic module discovery
#
# =============================================================================

"""
Unified tools for CLI operations, combining handlers and quick_tools.
"""

from pathlib import Path

_PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[4].joinpath("dev_scripts/cli_prototype.py")
)


def _load_prototype_module():
    """Load the development prototype module if it exists.

    Returns:
        Module | None: The loaded prototype module or ``None`` when not found.
    """
    if _PROTOTYPE_PATH.exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "cli_prototype", str(_PROTOTYPE_PATH)
        )
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore
            return module

    return None


__all__ = ["bounds", "convert", "inventory", "assign", "fix_bmap"]

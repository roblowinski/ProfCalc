# =============================================================================
# Quick Tools Package Initialization
# =============================================================================
#
# FILE: src/profcalc/cli/quick_tools/__init__.py
#
# PURPOSE:
# This module initializes the quick tools package, which provides streamlined
# command-line access to common coastal profile analysis operations. It serves
# as the package entry point and enforces the menu-only execution model for
# quick tools.
#
# WHAT IT'S FOR:
# - Initializing the quick tools package structure
# - Providing package-level exports for quick tool modules
# - Enforcing menu-only execution policy for quick tools
# - Supporting legacy CLI dispatch routing
# - Maintaining clean separation between menu and direct CLI access
#
# WORKFLOW POSITION:
# This module sits at the package level for quick tools and ensures that all
# quick tool operations are accessed through the interactive menu system rather
# than direct CLI calls. It provides the package infrastructure while enforcing
# the design decision that quick tools require menu interaction.
#
# LIMITATIONS:
# - Explicitly prevents direct CLI execution of quick tools
# - Requires menu system for all quick tool access
# - Limited to predefined quick tool modules
# - No programmatic API for quick tools
#
# ASSUMPTIONS:
# - Quick tools are designed for interactive use only
# - Menu system provides adequate access to quick tools
# - Users understand menu navigation for tool access
# - Direct CLI execution is not required for quick tools
#
# =============================================================================

"""
Quick command-line tools for common coastal profile analysis tasks.

Each module provides both CLI execution and menu integration.
"""

__all__ = ["bounds", "convert", "inventory", "assign", "fix_bmap"]


def execute_from_cli(args: list[str]) -> None:
    """Dispatch a quick-tools style CLI call.

    For historical tests and callers that import
    `profcalc.cli.quick_tools.execute_from_cli`, route the call to the
    conversion tool (the tests exercise CSV/XYZ/shapefile conversions).

    This is a small dispatcher that currently forwards to
    `profcalc.cli.tools.convert.execute_from_cli`.
    """
    # Quick tools are intentionally menu-only. If a caller attempts to
    # dispatch quick-tools from a CLI context, raise a clear error and
    # advise using the interactive menu via run_menu.ps1 or the Python
    # menu entrypoint.
    raise NotImplementedError(
        "Quick tools are menu-only; run them from the interactive menu (run_menu.ps1)"
    )

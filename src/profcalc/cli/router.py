# =============================================================================
# ProfCalc CLI Router and Main Entry Point
# =============================================================================
#
# FILE: src/profcalc/cli/router.py
#
# PURPOSE:
# This is the main entry point for the ProfCalc command-line interface. It serves
# as the primary router that launches the interactive menu system and provides
# the main() function that can be called from console scripts or imported modules.
#
# WHAT IT'S FOR:
# - Provides the primary command-line entry point for ProfCalc
# - Launches the interactive menu system for user-guided analysis workflows
# - Enables the CLI to be run as a module (python -m profcalc.cli.router)
# - Serves as a simple router to the more complex menu system
# - Supports both direct execution and programmatic launching
#
# WORKFLOW POSITION:
# This file is the first point of contact when users run ProfCalc from the command
# line. It sits at the top of the CLI hierarchy and delegates to the menu system
# for all interactive functionality. It's designed to be simple and lightweight,
# focusing only on launching the main menu interface.
#
# LIMITATIONS:
# - Only launches the interactive menu system (no direct tool execution)
# - Requires the menu system to be properly implemented and importable
# - No command-line argument parsing or configuration options
# - Assumes interactive usage (not suitable for automated scripts)
#
# ASSUMPTIONS:
# - The menu system is properly implemented and functional
# - User wants an interactive experience rather than direct tool execution
# - Console environment is available for menu display and navigation
# - All necessary dependencies are installed and importable
#
# =============================================================================

#!/usr/bin/env python3
"""
Profile Calculator Menu Launcher

Launches the interactive menu system for profile analysis tools.

Usage:
    python -m profcalc.cli.router  # Launch interactive menu
"""

from profcalc.cli.menu_system import launch_menu


def main() -> None:
    """Launch the interactive menu system."""
    launch_menu()


if __name__ == "__main__":
    main()

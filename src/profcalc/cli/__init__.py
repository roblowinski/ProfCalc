# =============================================================================
# ProfCalc Command-Line Interface Package
# =============================================================================
#
# FILE: src/profcalc/cli/__init__.py
#
# PURPOSE:
# This is the initialization file for the ProfCalc CLI (Command-Line Interface)
# package, which provides both interactive and programmatic access to all
# ProfCalc analysis tools. It serves as the main entry point for command-line
# usage and exposes the primary CLI router function.
#
# WHAT IT'S FOR:
# - Provides unified access to all CLI functionality through the main() function
# - Supports both interactive menu-driven workflows and direct command execution
# - Enables integration with external scripts and automation systems
# - Offers quick tools for common analysis tasks without full menu navigation
# - Provides a clean separation between core analysis logic and user interfaces
#
# WORKFLOW POSITION:
# This file sits at the top of the CLI hierarchy and is typically imported when
# users want to run ProfCalc from the command line. It connects the core analysis
# functionality (in profcalc.tools and profcalc.common) with user interaction
# layers (menus, file dialogs, input validation). It's used for both interactive
# sessions and automated processing pipelines.
#
# LIMITATIONS:
# - Requires a terminal/console environment for interactive features
# - Some features depend on tkinter for file dialogs (GUI environment needed)
# - Interactive prompts may not work well in automated/CI environments
# - Performance depends on terminal capabilities and user input speed
#
# ASSUMPTIONS:
# - User has access to a terminal or console for interaction
# - GUI environment is available for file selection dialogs
# - Core profcalc functionality is properly installed and importable
# - User understands basic command-line concepts and file system navigation
# - Input files are accessible and properly formatted for analysis
#
# =============================================================================

"""
Command-line interface modules for coastal profile analysis.

Provides both interactive menu system and quick command-line tools.
"""

from .router import main

__all__ = ["main"]

# =============================================================================
# Menu Testing Script
# =============================================================================
#
# FILE: scripts/run_menu.py
#
# PURPOSE:
# This script provides a standalone execution environment for testing individual
# menu functions from the profcalc.cli.menu_system module. It allows developers
# and testers to exercise specific menu components without launching the full
# application, enabling focused testing and debugging of menu functionality.
#
# WHAT IT'S FOR:
# - Testing individual menu functions in isolation
# - Debugging menu system components during development
# - Validating menu behavior without full application startup
# - Quick verification of menu system changes
# - Supporting automated testing of menu workflows
#
# WORKFLOW POSITION:
# This script is used during development and testing phases to validate menu
# system functionality. It sits outside the main application workflow but
# provides essential testing capabilities for menu components that are used
# throughout the application.
#
# LIMITATIONS:
# - Requires menu functions to be properly defined in menu_system module
# - Does not provide full application context or state management
# - Limited error handling compared to full application environment
# - May not capture all integration issues between menu components
#
# ASSUMPTIONS:
# - Menu functions are properly imported and available in menu_system
# - System has necessary dependencies for menu execution
# - User has appropriate permissions for menu operations
# - Terminal environment supports interactive menu display
#
# =============================================================================

"""Run an individual menu from `profcalc.cli.menu_system` for interactive testing.

Usage:
    python scripts/run_menu.py main_menu
    python scripts/run_menu.py annual_monitoring_menu

This script imports the requested function and calls it. Use it to exercise a
single menu without launching the full application.
"""

import sys

from profcalc.cli import menu_system


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_menu.py <menu_function_name>")
        print("Available menus: main_menu, select_data_source, data_management_menu, annual_monitoring_menu, quick_tools_menu")
        sys.exit(1)

    name = sys.argv[1]
    func = getattr(menu_system, name, None)
    if func is None or not callable(func):
        print(f"Menu function '{name}' not found in profcalc.cli.menu_system")
        sys.exit(2)

    print(f"Running menu: {name} (press Ctrl+C to exit)")
    try:
        func()
    except KeyboardInterrupt:
        print("\nInterrupted by user")


if __name__ == "__main__":
    main()

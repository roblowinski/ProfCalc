"""Run an individual menu from `profcalc.cli.menu_system` for interactive testing.

Usage:
    python scripts/run_menu.py main_menu
    python scripts/run_menu.py annual_monitoring_menu

This script imports the requested function and calls it. Use it to exercise a
single menu without launching the full application.
"""

import sys
from typing import Callable

from profcalc.cli import menu_system


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_menu.py <menu_function_name>")
        print("Available menus: main_menu, select_data_source, data_management_menu, annual_monitoring_menu, quick_tools_menu")
        sys.exit(1)

    name = sys.argv[1]
    func = getattr(menu_system, name, None)
    if func is None or not isinstance(func, Callable):
        print(f"Menu function '{name}' not found in profcalc.cli.menu_system")
        sys.exit(2)

    print(f"Running menu: {name} (press Ctrl+C to exit)")
    try:
        func()
    except KeyboardInterrupt:
        print("\nInterrupted by user")


if __name__ == "__main__":
    main()

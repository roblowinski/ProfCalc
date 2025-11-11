"""Make the package runnable with `python -m profcalc`.

This module simply delegates to the interactive menu system so users can
start the main menu without installing the package.
"""

from profcalc.cli import menu_system


def main() -> None:
    """Run the interactive main menu.

    This function is called when executing `python -m profcalc`.
    """
    menu_system.main_menu()


if __name__ == "__main__":
    main()

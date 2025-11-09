#!/usr/bin/env python3
"""
Profile Calculator CLI Router

Command-line interface for profile analysis tools.

Examples:
    profcalc                                  # Launch interactive menu
    profcalc -b <files> -o <output>          # Find common bounds
    profcalc -c <input> --to <format> -o <output>  # Convert format
    profcalc -i <file> -o <output>           # File inventory
    profcalc -a <xyz> --baselines <file> -o <output>  # Assign XYZ points
    profcalc -f <input> -o <output>          # Fix BMAP point counts
"""

import argparse
import logging
import sys

from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error


def main() -> None:
    """Main CLI entry point - routes to menu or quick tools."""

    # If no arguments, launch interactive menu
    if len(sys.argv) == 1:
        from .menu_system import launch_menu

        launch_menu()
        return

    # Parse command-line arguments for quick tools
    parser = argparse.ArgumentParser(
        prog="profcalc",
        description="Profile Calculator Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  profcalc                              # Launch interactive menu
  profcalc -b *.dat -o report.txt       # Find bounds via command-line
  profcalc -c input.dat --to csv -o output.csv  # Convert format
  profcalc -i file.dat -o inventory.txt # Generate inventory
  profcalc --verbose -c input.dat --to csv -o output.csv  # Verbose logging
        """,
    )

    # Add global options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (INFO level)",
    )
    # Menu integration options
    parser.add_argument(
        "--menu",
        action="store_true",
        help="Launch interactive menu (same as running with no args)",
    )
    parser.add_argument(
        "--handler",
        help="Run a menu handler by key (e.g. data.import_data) non-interactively",
    )

    # Add mutually exclusive tool flags
    tool_group = parser.add_mutually_exclusive_group()
    tool_group.add_argument(
        "-b",
        "--bounds",
        action="store_true",
        help="Find common X bounds per profile",
    )
    tool_group.add_argument(
        "-c",
        "--convert",
        action="store_true",
        help="Convert between file formats",
    )
    tool_group.add_argument(
        "-i",
        "--inventory",
        action="store_true",
        help="Generate file inventory report",
    )
    tool_group.add_argument(
        "-a",
        "--assign",
        action="store_true",
        help="Assign XYZ points to profiles",
    )
    tool_group.add_argument(
        "-f",
        "--fix-bmap",
        action="store_true",
        help="Fix incorrect point counts in BMAP file",
    )

    # Parse just the tool flag first
    args, remaining = parser.parse_known_args()

    # Configure logging based on verbose flag
    if args.verbose:
        logging.basicConfig(
            level=logging.INFO, format="%(levelname)s: %(message)s"
        )
    else:
        logging.basicConfig(
            level=logging.WARNING, format="%(levelname)s: %(message)s"
        )

    # Route to appropriate quick tool handler
    try:
        # If menu flag provided explicitly, launch interactive menu
        if getattr(args, "menu", False):
            from .menu_system import launch_menu

            launch_menu()
            return

        # If a menu handler key was provided, resolve and call it
        if getattr(args, "handler", None):
            from .menu import MenuEngine

            engine = MenuEngine()
            try:
                handler_callable = engine.resolve_handler(args.handler)
            except (
                LookupError,
                ValueError,
                AttributeError,
                ImportError,
            ) as exc:
                log_quick_tool_error(
                    "router",
                    f"Failed to resolve handler '{args.handler}': {exc}",
                    exc=exc,
                )
                print(
                    f"Failed to resolve handler '{args.handler}': {exc}",
                    file=sys.stderr,
                )
                sys.exit(2)

            if handler_callable is None:
                log_quick_tool_error(
                    "router", f"Handler '{args.handler}' not found"
                )
                print(f"Handler '{args.handler}' not found", file=sys.stderr)
                sys.exit(2)

            try:
                handler_callable()
            except TypeError:
                handler_callable()
            return

        if args.bounds:
            from .tools import bounds

            bounds.execute_from_cli(remaining)
        elif args.convert:
            from .tools import convert

            convert.execute_from_cli(remaining)
        elif args.inventory:
            from .tools import inventory

            inventory.execute_from_cli(remaining)
        elif args.assign:
            from .tools import assign

            assign.execute_from_cli(remaining)
        elif args.fix_bmap:
            from .tools import fix_bmap

            fix_bmap.execute_from_cli(remaining)
        else:
            parser.print_help()
            sys.exit(1)

    except (OSError, ValueError, TypeError, RuntimeError, ImportError) as e:
        log_quick_tool_error("router", f"Router error: {e}", exc=e)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

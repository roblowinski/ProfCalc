"""Interactive menu engine for ProfCalc CLI.

This module provides MenuEngine, a small interactive menu system that loads a
hierarchical menu from a JSON file and dispatches menu selections to handler
callables. Handler keys are resolved to functions under
`profcalc.cli.handlers` or, as a fallback, to functions in a development
prototype module.

Google-style docstrings are used for public classes and methods.
"""

import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error


class MenuEngine:
    """Simple interactive menu engine that loads a JSON menu and dispatches
    handlers.

    Resolution strategy for handler keys like "data.import_data":

      1. Try to import `profcalc.cli.handlers.data` and get attribute
         `import_data`.
      2. Fallback: attempt to load `dev_scripts/cli_prototype.py` and map a
         few well-known handler keys to the prototype functions to avoid
         duplicating work.

    Attributes:
        menu_path (Path): Path to the JSON menu file.
        menu (Any): Parsed menu structure loaded from the JSON file.
    """

    PROTOTYPE_PATH_NAME = "dev_scripts/cli_prototype.py"

    # Mapping of menu handler keys -> function names in dev_scripts.cli_prototype
    PROTOTYPE_MAPPING: Dict[str, str] = {
        "data.import_data": "import_data_menu",
        "data.browse": "view_surveys_menu",
        "data.manage_db": "manage_database_menu",
    }

    def __init__(self, menu_path: Optional[Path] = None) -> None:
        """Initialize a MenuEngine instance.

        Args:
            menu_path (Optional[Path]): Optional path to the menu JSON file.
                If not provided, the engine will look for `menu_data.json`
                adjacent to this module.

        Raises:
            FileNotFoundError: If the resolved menu file does not exist.
        """
        if menu_path is None:
            # locate package-relative menu_data.json
            menu_path = Path(__file__).parent.joinpath("menu_data.json")
        self.menu_path = Path(menu_path)
        self.menu = self._load_menu()

    def _load_menu(self) -> Any:
        """Load and parse the JSON menu file.

        Returns:
            Any: Parsed JSON structure (expected to contain a top-level

                {"menu": [...]}

            key).

        Raises:
            FileNotFoundError: If the menu file cannot be found.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        if not self.menu_path.exists():
            raise FileNotFoundError(f"Menu file not found: {self.menu_path}")

        # Use utf-8-sig to gracefully handle files that include a BOM
        # (some editors on Windows add a BOM which json.load can't handle
        # when opening with plain utf-8).
        with self.menu_path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)["menu"]

    def run(self) -> None:
        """Start the interactive menu loop at the top level.

        This method begins a blocking interactive session that displays the
        top-level menu and responds to user input until the user quits.

        Example:
            engine = MenuEngine()
            engine.run()
        """
        self._interactive_menu(self.menu, title="Main Menu")

    def _interactive_menu(self, nodes: list, title: str = "Menu") -> None:
        """Render an interactive menu for the given node list and handle input.

        The method prints numbered options, accepts user selection, handles
        navigation (back/quit), and dispatches handlers when a menu leaf with
        a handler is selected. Handlers are called without arguments.

        Args:
            nodes (list): List of menu node dictionaries. Each node is expected
                to contain keys like "title", "handler", and optionally
                "children".
            title (str): Display title for the current menu level.

        Notes:
            - The handler resolution is performed by `resolve_handler`.
            - Prototype handlers that expect arguments are attempted to be
              invoked with no arguments; TypeError is caught and the handler
              is retried without args.
        """
        while True:
            print(f"\n== {title} ==")

            options = []
            for i, node in enumerate(nodes, start=1):
                options.append((str(i), node))
                print(f"  {i}. {node.get('title')}")

            print("\n  b. Back    q. Quit")

            choice = input("Enter selection: ").strip()

            if choice.lower() == "q":
                print("Exiting...\n")
                return
            if choice.lower() == "b":
                return

            selected = next(
                (node for key, node in options if key == choice), None
            )

            if selected is None:
                print("Invalid selection, try again.")
                continue

            # If node has children, descend into submenu
            if selected.get("children"):
                self._interactive_menu(
                    selected["children"], title=selected.get("title", "Menu")
                )
                continue

            handler_key = selected.get("handler")
            if handler_key:
                try:
                    handler = self.resolve_handler(handler_key)
                except (ImportError, ValueError, AttributeError) as e:
                    # Failed to find/resolve the handler; present a friendly message
                    log_quick_tool_error(
                        "menu",
                        f"Failed to resolve handler '{handler_key}': {e}",
                        exc=e,
                    )
                    print(f"Failed to resolve handler '{handler_key}': {e}")
                    continue

                if handler is None:
                    print("No action assigned to this menu item.")
                    continue

                # Call the handler (no args for now)
                try:
                    handler()
                except TypeError:
                    # Some prototype handlers expect arguments; call without args
                    handler()
                except (
                    RuntimeError,
                    OSError,
                    ValueError,
                    ZeroDivisionError,
                    KeyError,
                ) as e:  # pragma: no cover - interactive
                    # Top-level interactive loop: surface common handler errors
                    # without crashing the menu. We avoid catching BaseException
                    # so KeyboardInterrupt/SystemExit still propagate.
                    log_quick_tool_error(
                        "menu",
                        f"Handler '{handler_key}' raised an exception: {e}",
                        exc=e,
                    )
                    print(f"Handler raised an exception: {e}")
            else:
                print("No action assigned to this menu item.")

    def resolve_handler(self, handler_key: str) -> Optional[Callable]:
        """Resolve a handler key like 'data.import_data' to a callable.

        Resolution strategy:
            1. Attempt to import `profcalc.cli.handlers.<module>` and return
               the attribute `<function>`.
            2. If that fails, attempt to load the development prototype file
               `dev_scripts/cli_prototype.py` and map the handler key to a
               prototype function using PREDEFINED mapping.

        Args:
            handler_key (str): Dotted handler key in the form
                "<module>.<function>".

        Returns:
            Optional[Callable]: The resolved callable, or None when the key
            is empty.

        Raises:
            ValueError: If the handler_key is not a valid dotted string.
            ImportError: If neither a package handler nor a prototype
                fallback function could be found.
        """
        if not handler_key:
            return None

        try:
            module_name, func_name = handler_key.split(".", 1)
        except ValueError:
            raise ValueError(f"Invalid handler key: {handler_key}")

        # Try to import the official handler module under the package
        pkg_module = f"profcalc.cli.handlers.{module_name}"
        try:
            mod = importlib.import_module(pkg_module)
            func = getattr(mod, func_name)
            return func
        except (ImportError, AttributeError) as import_err:
            # Fallback to the dev_scripts prototype by loading the file dynamically
            repo_root = Path(__file__).resolve().parents[4]
            proto_path = repo_root.joinpath(self.PROTOTYPE_PATH_NAME)

            if proto_path.exists():
                spec = importlib.util.spec_from_file_location(
                    "cli_prototype", str(proto_path)
                )
                if spec and spec.loader:
                    proto = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(proto)  # type: ignore

                    # Map handler_key to prototype function name
                    proto_name = self.PROTOTYPE_MAPPING.get(handler_key)
                    if proto_name and hasattr(proto, proto_name):
                        return getattr(proto, proto_name)

            # Last resort: try to import a handlers module that might be nearby
            raise ImportError(
                f"Could not resolve handler for key: {handler_key}"
            ) from import_err


def main() -> None:
    """Create a MenuEngine and run the interactive menu.

    This function is provided for convenience so the module can be executed
    as a script.

    Example:
        python -m profcalc.cli.menu
    """
    import argparse

    ap = argparse.ArgumentParser(description="ProfCalc menu CLI")
    ap.add_argument("--menu-path", "-m", help="Path to menu JSON file (overrides package default)")
    ap.add_argument("--list", action="store_true", help="Print the menu tree and exit (non-interactive)")
    ap.add_argument("--no-interactive", action="store_true", help="Do not start the interactive menu loop")
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = ap.parse_args()

    engine = MenuEngine(menu_path=Path(args.menu_path) if args.menu_path else None)

    if args.verbose:
        print(f"Loaded menu from: {engine.menu_path}")

    if args.list:
        # Print a simple textual representation of the menu and exit
        def _print_nodes(nodes: list, indent: int = 0) -> None:
            prefix = "" if indent == 0 else "".join(["  "] * indent)
            for node in nodes:
                title = node.get("title", "<no title>")
                handler = node.get("handler")
                children = node.get("children")
                if handler:
                    print(f"{prefix}- {title} -> {handler}")
                else:
                    print(f"{prefix}- {title}")
                if children:
                    _print_nodes(children, indent + 1)

        _print_nodes(engine.menu)
        return

    if args.no_interactive:
        if args.verbose:
            print("No-interactive mode selected; exiting.")
        return

    engine.run()


if __name__ == "__main__":
    main()

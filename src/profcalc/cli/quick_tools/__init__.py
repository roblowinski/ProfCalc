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

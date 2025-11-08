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
    try:
        from profcalc.cli.tools.convert import execute_from_cli as _conv

        # Call the conversion CLI and allow runtime exceptions to propagate
        # (FileNotFoundError, ValueError, etc.). Only catch ImportError which
        # means the conversion implementation is not available.
        return _conv(args)
    except ImportError as exc:  # pragma: no cover - thin dispatcher
        raise ImportError(
            "No conversion CLI available in profcalc.cli.tools.convert"
        ) from exc

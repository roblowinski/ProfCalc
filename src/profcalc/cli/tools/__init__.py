"""
Unified tools for CLI operations, combining handlers and quick_tools.
"""

from pathlib import Path

_PROTOTYPE_PATH = (
    Path(__file__)
    .resolve()
    .parents[4]
    .joinpath("dev_scripts/cli_prototype.py")
)

def _load_prototype_module():
    """Load the development prototype module if it exists.

    Returns:
        Module | None: The loaded prototype module or ``None`` when not found.
    """
    if _PROTOTYPE_PATH.exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "cli_prototype", str(_PROTOTYPE_PATH)
        )
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore
            return module

    return None

__all__ = ["bounds", "convert", "inventory", "assign", "fix_bmap"]
"""CLI handlers package for profcalc.

This package exposes a collection of simple callable handlers used by the
command-line menu. Each handler is a tiny wrapper that delegates to the
real implementation in this package or, during early development, to the
prototype functions located in ``dev_scripts/cli_prototype.py``.

Utilities:
    _load_prototype_module: Try to dynamically load the prototype module
        when present.
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


def data():
    """Placeholder symbol to satisfy package exports used by the menu loader.

    The real handlers live in modules such as ``data.py`` and ``annual.py``.
    This placeholder allows importlib to find the handlers package during
    menu resolution.
    """
    pass


__all__ = ["data"]

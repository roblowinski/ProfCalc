"""Handler module shim: re-export data handlers for the CLI menu.

Tests and MenuEngine expect handler modules under ``profcalc.cli.handlers``.
The authoritative implementations live under ``profcalc.cli.tools``. This
module re-exports those implementations so the menu resolver can import
``profcalc.cli.handlers.data`` and access the expected callables.
"""

from profcalc.cli.tools.data import (
    browse,
    delete,
    edit,
    export,
    integrity_check,
    list_datasets,
    merge,
    outlier_detection,
    plot,
    select_dataset,
    spec_check,
    summary,
    validation,
)
from profcalc.cli.tools.data import (
    import_data as _import_data,
)

__all__ = [
    "import_data",
    "select_dataset",
    "list_datasets",
    "browse",
    "plot",
    "summary",
    "integrity_check",
    "outlier_detection",
    "spec_check",
    "validation",
    "edit",
    "merge",
    "delete",
    "export",
]


def import_data(
    file_path: str | None = None,
    *,
    file_type: str = "csv",
    require_exists: bool = True,
):
    """Interactive wrapper around the deterministic import_data implementation.

    When invoked without a `file_path` (i.e., from the menu engine), prompt the
    user for a path. When called programmatically with a `file_path`, behave
    like the underlying implementation.
    """
    if not file_path:
        try:
            p = input("Enter path to CSV file to import: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("Import cancelled.")
            return {"status": "cancelled", "imported": 0, "sample": []}
        if not p:
            print("No path provided. Import cancelled.")
            return {"status": "cancelled", "imported": 0, "sample": []}
        file_path = p

    # Delegate to the underlying non-interactive implementation
    return _import_data(
        file_path=file_path, file_type=file_type, require_exists=require_exists
    )

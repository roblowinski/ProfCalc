# =============================================================================
# Data Management Handler Module
# =============================================================================
#
# FILE: src/profcalc/cli/handlers/data.py
#
# PURPOSE:
# This module serves as a handler shim for data management operations in the
# CLI menu system. It re-exports data-related functions from the tools module
# to provide a consistent interface for menu handler resolution, bridging the
# gap between menu navigation and actual data processing functionality.
#
# WHAT IT'S FOR:
# - Providing menu-accessible data management functions
# - Re-exporting data tools for consistent handler interface
# - Supporting data import, export, and manipulation operations
# - Enabling data validation and integrity checking
# - Facilitating data visualization and summary operations

# WORKFLOW POSITION:
# This module acts as a bridge between the menu system and the core data
# processing tools. It ensures that menu selections for data operations are
# properly routed to the appropriate implementation functions in the tools
# module, maintaining clean separation between UI and business logic.

# LIMITATIONS:
# - Pure re-export module with no additional logic
# - Depends on tools module for actual implementations
# - No error handling or validation beyond what's in tools
# - Menu-specific interface constraints

# ASSUMPTIONS:
# - Tools module provides all necessary data functions
# - Function signatures are compatible with menu expectations
# - Import/export operations work with current data formats
# - Data integrity checks are sufficient for use cases

# =============================================================================

"""Handler module shim: re-export data handlers for the CLI menu.

Tests and MenuEngine expect handler modules under ``profcalc.cli.handlers``.
The authoritative implementations live under ``profcalc.cli.tools``. This
module re-exports those implementations so the menu resolver can import
``profcalc.cli.handlers.data`` and access the expected callables.
"""

from typing import Dict

from profcalc.cli.file_dialogs import select_input_file
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
) -> Dict[str, object]:
    """Interactive wrapper around the deterministic import_data implementation.

    When invoked without a `file_path` (i.e., from the menu engine), prompt the
    user for a path. When called programmatically with a `file_path`, behave
    like the underlying implementation.
    """
    if not file_path:
        try:
            print("Select a CSV file...")
            p = select_input_file("Select CSV File")
        except (EOFError, KeyboardInterrupt):
            print("Import cancelled.")
            return {"status": "cancelled", "imported": 0, "sample": []}
        if not p:
            print("No file selected. Import cancelled.")
            return {"status": "cancelled", "imported": 0, "sample": []}
        file_path = p

    # Delegate to the underlying non-interactive implementation
    return _import_data(
        file_path=file_path, file_type=file_type, require_exists=require_exists
    )

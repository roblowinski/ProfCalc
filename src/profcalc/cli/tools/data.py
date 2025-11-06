"""Data management handlers for the command-line menu.

These functions are intentionally small wrappers so they can be tested easily
and replaced later with full implementations.
"""

import json
from pathlib import Path
from typing import Dict, Optional

from profcalc.cli.context import Session

# Initialize a session object
session = Session()


def _maybe_register_path(p: Path) -> Optional[str]:
    """Register path in session if it exists and isn't already registered.

    Returns the dataset_id or None if not registered.
    """
    if not p.exists():
        return None

    # If already registered (by path), return existing id
    for dsid, info in session.list_datasets().items():
        try:
            if info.get("path") == p.resolve():
                return dsid
        except (AttributeError, TypeError):
            # Defensive: skip any malformed dataset entries
            continue

    dsid = session.load_dataset(str(p))
    return dsid


def _load_prototype():
    """Dynamically load the development prototype module if present.

    The repository contains a lightweight `dev_scripts/cli_prototype.py`
    used during development. This helper attempts to load that file as a
    module so the CLI can fall back to prototype implementations for
    handlers that are not yet implemented in the package.

    Returns:
        Module | None: The loaded module object or ``None`` if the file
            does not exist.
    """
    proto_path = (
        Path(__file__)
        .resolve()
        .parents[4]
        .joinpath("dev_scripts/cli_prototype.py")
    )
    if proto_path.exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "cli_prototype", str(proto_path)
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore
            return module
    return None


def import_data(
    file_path: Optional[str] = None,
    *,
    file_type: str = "csv",
    require_exists: bool = True,
) -> Dict[str, object]:
    """Import data from a file and register it with the current session.

    This is a deterministic, non-interactive API intended for tests and
    programmatic use. Currently only CSV files are supported.

    Args:
        file_path: Path to the input file. Must be provided for
            non-interactive imports.
        file_type: Input file type. Only ``'csv'`` is supported.
        require_exists: If True, raise ``FileNotFoundError`` when the
            file does not exist; otherwise return a successful empty
            result.

    Returns:
        Dict[str, object]: Result summary with keys: ``status``,
            ``imported`` (int number of rows) and ``sample`` (list of
            parsed rows up to 10 items).

    Raises:
        NotImplementedError: If an unsupported file type is requested.
        ValueError: If ``file_path`` is not provided.
        FileNotFoundError: If the input file does not exist and
            ``require_exists`` is True.
    """
    # Basic argument validation
    if file_type.lower() != "csv":
        raise NotImplementedError("Only CSV import is implemented")

    if not file_path:
        raise ValueError("file_path is required for non-interactive import")

    p = Path(file_path)
    if not p.exists():
        if require_exists:
            raise FileNotFoundError(f"Input file not found: {file_path}")
        return {"status": "ok", "imported": 0, "sample": []}

    import csv

    rows = []
    with p.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)

    # Register dataset in session
    dataset_id = session.load_dataset(file_path)
    session.set_active(dataset_id)

    # After importing a survey (9-column CSV), attempt to auto-load supporting
    # static input files defined in project settings (project and profile line CSVs).
    try:
        # Resolve config.json which lives at src/profcalc/settings/config.json
        cfg_path = Path(__file__).resolve().parents[2].joinpath("settings", "config.json")
        if cfg_path.exists():
            with cfg_path.open("r", encoding="utf-8") as fh:
                cfg = json.load(fh)
            data_dir = cfg.get("paths", {}).get("data")
            if data_dir:
                data_dir_path = Path(data_dir)
                # If relative path, resolve relative to repo root
                if not data_dir_path.is_absolute():
                    data_dir_path = Path(__file__).resolve().parents[3].joinpath(data_dir)

                # Look for common supporting files
                proj_csv = data_dir_path.joinpath("Project_Data_Input.csv")
                profline_csv = data_dir_path.joinpath("ProfileLine_Data_Input.csv")

                proj_id = _maybe_register_path(proj_csv)
                prof_id = _maybe_register_path(profline_csv)

                if proj_id:
                    print(f"Auto-registered project data: {proj_csv} (id={proj_id})")
                if prof_id:
                    print(f"Auto-registered profile line data: {profline_csv} (id={prof_id})")

    except (OSError, json.JSONDecodeError):
        # Non-fatal: auto-load is best-effort and should not block import
        pass

    return {"status": "ok", "imported": len(rows), "sample": rows[:10]}


def select_dataset(dataset_id: str):
    """Select an active dataset by ID.

    Args:
        dataset_id: Identifier returned by :py:meth:`Session.load_dataset`.
    """
    session.set_active(dataset_id)
    print(f"Dataset {dataset_id} is now active.")


def list_datasets():
    """Print a human-readable list of datasets registered in the session.

    The function is a convenience for the CLI and prints each dataset's
    ID and metadata to stdout.
    """
    datasets = session.list_datasets()
    for dataset_id, dataset_info in datasets.items():
        print(f"ID: {dataset_id}, Info: {dataset_info}")


def browse() -> None:
    """Open the data browsing UI.

    If a development prototype is available the function will delegate to
    ``view_surveys_menu`` from the prototype; otherwise it prints a stub
    message. This function is implemented primarily for CLI-driven
    exploration and is intentionally lightweight here.
    """
    proto = _load_prototype()
    if proto and hasattr(proto, "view_surveys_menu"):
        proto.view_surveys_menu()
        return

    print("[data.browse] Browsing data (stub).")


def plot() -> None:
    """Plot the active dataset.

    This is a CLI stub that will be replaced with a proper plotting
    implementation later. For now it prints a placeholder message.
    """
    print("[data.plot] Plotting data (stub).")


def summary() -> None:
    """Show summary statistics for the active dataset.

    Currently a stub that prints a placeholder message.
    """
    print("[data.summary] Showing summary statistics (stub).")


def integrity_check() -> None:
    """Run integrity checks on datasets.

    Stub implementation; future versions will perform schema and value
    validations and report issues.
    """
    print("[data.integrity_check] Running data integrity checks (stub).")


def outlier_detection() -> None:
    """Detect outliers in the active dataset.

    Placeholder implementation.
    """
    print("[data.outlier_detection] Detecting outliers (stub).")


def spec_check() -> None:
    """Check datasets against specification templates.

    Placeholder implementation.
    """
    print("[data.spec_check] Checking spec/requirements (stub).")


def validation() -> None:
    """Run full validation workflows on datasets.

    Placeholder implementation.
    """
    print("[data.validation] Running validation (stub).")


def edit() -> None:
    """Edit dataset metadata or contents.

    Placeholder CLI stub.
    """
    print("[data.edit] Editing data (stub).")


def merge() -> None:
    """Merge or append datasets.

    Placeholder CLI stub.
    """
    print("[data.merge] Merging/appending data (stub).")


def delete() -> None:
    """Delete a dataset from the session or underlying store.

    Placeholder CLI stub.
    """
    print("[data.delete] Deleting data (stub).")


def export() -> None:
    """Export dataset to common formats (CSV, Excel, Shapefile).

    Placeholder CLI stub.
    """
    print("[data.export] Exporting data (stub).")

# =============================================================================
# Annual Monitoring Analysis Tools
# =============================================================================
#
# FILE: src/profcalc/cli/tools/annual.py
#
# PURPOSE:
# This module provides specialized handlers for annual monitoring workflows in
# ProfCalc, focusing on shoreline analysis, survey data processing, and reporting
# tools. It handles AER (Annual Erosion Rate) computations, survey import
# summaries, and other annual monitoring tasks that are critical for coastal
# management and beach morphology studies.
#
# WHAT IT'S FOR:
# - Processes annual survey data for shoreline change analysis
# - Computes Annual Erosion Rates (AER) and accretion rates
# - Generates summary reports for annual monitoring programs
# - Handles survey data import and validation for annual workflows
# - Provides tools for comparing survey data across time periods
# - Supports both programmatic use and interactive menu-driven workflows
#
# WORKFLOW POSITION:
# This module sits in the "Annual Monitoring" section of the ProfCalc menu system.
# It's used when analysts need to process yearly survey data, track shoreline
# changes over time, and generate reports for coastal management decisions.
# It works with survey data that has been collected at regular intervals and
# needs to be analyzed for trends and changes.
#
# LIMITATIONS:
# - Designed specifically for annual monitoring workflows (not ad-hoc analysis)
# - Requires properly formatted survey data with temporal information
# - AER calculations assume consistent survey methodologies across years
# - May not handle irregular survey intervals optimally
# - Depends on core AER calculation modules for accuracy
#
# ASSUMPTIONS:
# - Survey data is collected at regular annual intervals
# - Coordinate systems and datums are consistent across survey years
# - Profile locations remain relatively stable between surveys
# - Users understand shoreline change analysis concepts and terminology
# - Data quality has been validated before annual processing
# - Temporal analysis requires at least 2 years of survey data
#
# =============================================================================

"""Annual monitoring handlers

Small CLI-facing handlers used by the interactive menu for annual
monitoring workflows (AER computations, survey import summaries, etc.).
Functions are intentionally lightweight and delegate to core modules for
data processing.

Usage examples:
    - Programmatic: import and call functions directly in scripts.
    - Menu: choose the corresponding Quick Tool entry in the interactive
        menu to run the prompt-driven flow (these menu entries delegate to
        the handlers in this module).
"""

import datetime as _dt
from pathlib import Path
from typing import Any, Dict, List, Optional

import profcalc.cli.menu_system as menu_system
from profcalc.cli.file_dialogs import select_input_file, select_output_file
from profcalc.cli.quick_tools.quick_tool_logger import log_quick_tool_error
from profcalc.cli.tools.data import import_data
from profcalc.cli.tools.data import session as data_session
from profcalc.common.bmap_io import BMAPImportError, Profile
from profcalc.common.error_handler import BeachProfileError
from profcalc.common.ninecol_io import read_9col_profiles
from profcalc.core import aer as aer_mod

# Use the shared session from the data tools so datasets registered via
# the Data Management menu are visible to annual handlers.
# `data_session` is imported from profcalc.cli.tools.data


def import_survey() -> Optional[dict]:
    """Import survey data using the active session dataset or prompt user.

    The function first checks whether a dataset is already active in the
    current :pyclass:`Session`. If present, that dataset's metadata is
    returned. Otherwise, the user is prompted for a file path and the
    request is forwarded to :pyfunc:`profcalc.cli.tools.data.import_data`.

    Returns:
        Optional[dict]: The active dataset info or the import result
            dictionary from :pyfunc:`import_data`. Returns ``None`` on
            import failure.
    """
    active_dataset = data_session.get_active()

    if active_dataset:
        print(f"Using active dataset: {active_dataset.get('info')}")
        print()
        return active_dataset

    print("No active dataset found. Prompting user to import data...")
    print()
    file_path = select_input_file("Select survey data file")

    if not file_path:
        print("No file selected. Import cancelled.")
        return None

    try:
        result = import_data(file_path)
        print(f"Data imported successfully: {result['imported']} rows.")
        print()
        return result
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        print()
        log_quick_tool_error("annual", f"File not found during import_survey: {e}")
        return None
    except ValueError as e:
        print(f"Value error: {e}")
        print()
        log_quick_tool_error("annual", f"Value error during import_survey: {e}")
        return None
    except (OSError, IOError) as e:  # Catch file-related errors
        print()
        print(f"An unexpected file-related error occurred: {e}")
        print()
        log_quick_tool_error(
            "annual", f"Unexpected file error during import_survey: {e}"
        )
        return None


def profcalc_profcalc() -> None:
    """Handler for the Profile Analysis submenu in the Annual Monitoring Report menu."""
    print("Launching Profile Analysis submenu...")
    menu_system.profcalc_profcalc_menu()


def compute_aer() -> Optional[dict]:
    """Interactive handler to compute Annual Erosion Rate (AER) between two surveys.

    The handler prompts for two 9-column survey files (earlier and later),
    allows picking a profile if multiple are present in a file, accepts an
    optional grid spacing (dx) and whether to use the BMAP core splitting
    logic, then computes AER and prints a concise summary. The function may
    optionally write a small CSV summary file.
    """
    print("\n--- Compute Annual Erosion Rate (AER) ---")

    # Prefer datasets registered in the shared session. If none or if the
    # user chooses, allow importing a file path.
    datasets = data_session.list_datasets()

    def _choose_dataset(label: str) -> Optional[Path]:
        # If there are registered datasets, present a short list to choose from
        if datasets:
            print(f"Registered datasets available for {label}:")
            ids = list(datasets.keys())
            for i, dsid in enumerate(ids):
                info = datasets[dsid]
                path = info.get("path")
                active_mark = " (active)" if data_session.active_dataset == dsid else ""
                print(f"{i + 1}. {dsid}{active_mark} -> {path}")
            choice = input(
                f"Select dataset number for {label} (blank to import from file): "
            ).strip()
            if choice:
                try:
                    idx = max(0, min(len(ids) - 1, int(choice) - 1))
                    return Path(datasets[ids[idx]].get("path"))
                except (ValueError, TypeError):
                    print("Invalid selection; falling back to file import.")

        # Fall back to prompting for a file path
        pth = select_input_file(f"Select {label} survey (9-col CSV)")
        if not pth:
            return None
        p = Path(pth)
        if not p.exists():
            log_quick_tool_error(
                "annual", f"File not found during dataset selection: {pth}"
            )
            print(f"File not found: {pth}")
            return None
        # Attempt to import/register the file so future tools see it
        try:
            import_data(str(p))
        except (FileNotFoundError, ValueError, NotImplementedError, OSError):
            # Non-fatal; still attempt to read the file directly
            pass
        return p

    pb = _choose_dataset("earlier")
    if pb is None:
        print("Cancelled.")
        return None
    pa = _choose_dataset("later")
    if pa is None:
        print("Cancelled.")
        return None

    try:
        before_profiles = read_9col_profiles(str(pb))
        after_profiles = read_9col_profiles(str(pa))
    except (
        BeachProfileError,
        ValueError,
    ) as exc:  # pragma: no cover - interactive
        # read_9col_profiles may raise BeachProfileError or ValueError for
        # malformed inputs; surface a friendly message and abort.
        log_quick_tool_error(
            "annual", f"Failed to read 9-col profiles for AER: {exc}", exc=exc
        )
        print(f"Failed to read 9-col profiles: {exc}")
        return None

    def choose_profile(profiles: List[Profile], label: str) -> Optional[Profile]:
        if not profiles:
            print(f"No profiles found in {label} file.")
            return None
        if len(profiles) == 1:
            return profiles[0]
        print(f"Multiple profiles found in {label} file:")
        for i, p in enumerate(profiles):
            print(f"{i + 1}. {p.name} ({p.date}) - {len(p.x)} pts")
        sel = input(
            f"Select profile number from {label} file (1-{len(profiles)}), blank=1: "
        ).strip()
        if not sel:
            idx = 0
        else:
            try:
                idx = max(0, min(len(profiles) - 1, int(sel) - 1))
            except (ValueError, TypeError):
                idx = 0
        return profiles[idx]

    prof_before = choose_profile(before_profiles, "earlier")
    if prof_before is None:
        return None
    prof_after = choose_profile(after_profiles, "later")
    if prof_after is None:
        return None

    # Attempt to parse survey dates
    def _parse_date(ds: Optional[str]) -> Optional[_dt.date]:
        if not ds:
            return None
        try:
            return _dt.date.fromisoformat(ds)
        except (ValueError, TypeError):
            try:
                return _dt.datetime.strptime(ds, "%Y%m%d").date()
            except (ValueError, TypeError):
                return None

    date_before = _parse_date(prof_before.date)
    date_after = _parse_date(prof_after.date)

    dx_in = input("Grid spacing dx (feet, default 0.1): ").strip()
    try:
        dx = float(dx_in) if dx_in else 0.1
    except (ValueError, TypeError):
        dx = 0.1

    use_bmap = input("Use BMAP core splitting logic? (Y/n) [Y]: ").strip().lower()
    use_bmap_core = use_bmap != "n"

    # Compute AER
    try:
        res = aer_mod.calculate_aer(
            prof_before.x,
            prof_before.z,
            prof_after.x,
            prof_after.z,
            date_before,
            date_after,
            dx=dx,
            use_bmap_core=use_bmap_core,
        )
    except (
        ValueError,
        ArithmeticError,
    ) as exc:  # pragma: no cover - interactive
        # calculate_aer can raise ValueError or other numeric errors; in
        # interactive mode present a message and abort.
        log_quick_tool_error("annual", f"AER computation failed: {exc}", exc=exc)
        print(f"AER computation failed: {exc}")
        return None

    # Print concise summary
    print("\nAER Summary:")
    print(f"Profile (before): {prof_before.name} date={prof_before.date}")
    print(f"Profile (after):  {prof_after.name} date={prof_after.date}")
    print(f"Cut (cuyd/ft): {res['cut_cuyd_per_ft']:.3f}")
    print(f"Fill (cuyd/ft): {res['fill_cuyd_per_ft']:.3f}")
    print(f"Net (fill - cut) (cuyd/ft): {res['all_cuyd_per_ft']:.3f}")
    years = res.get("years")
    if years and not (isinstance(years, float) and (years != years)):
        print(f"Years between surveys: {years:.4f}")
        print(f"AER (cuyd/ft/yr): {res['aer_cuyd_per_ft_per_yr']:.4f}")
    else:
        print("Dates not available or invalid; AER not computed.")

    save = select_output_file("Save summary CSV", "annual_summary.csv")
    if save:
        try:
            import csv

            keys = [
                "profile_before",
                "profile_after",
                "cut_cuyd_per_ft",
                "fill_cuyd_per_ft",
                "all_cuyd_per_ft",
                "years",
                "aer_cuyd_per_ft_per_yr",
            ]
            with open(save, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(keys)
                writer.writerow(
                    [
                        prof_before.name,
                        prof_after.name,
                        res["cut_cuyd_per_ft"],
                        res["fill_cuyd_per_ft"],
                        res["all_cuyd_per_ft"],
                        res.get("years"),
                        res.get("aer_cuyd_per_ft_per_yr"),
                    ]
                )
            print(f"Summary written to {save}")
        except (OSError, IOError) as exc:  # pragma: no cover - interactive
            log_quick_tool_error(
                "annual", f"Failed to save AER summary CSV: {exc}", exc=exc
            )
            print(f"Failed to save summary: {exc}")

    return res


def _parse_date_str(ds: Optional[str]) -> Optional[_dt.date]:
    """Parse a date string into a datetime.date or return None.

    Supports ISO format and YYYYMMDD.
    """
    if not ds:
        return None
    try:
        return _dt.date.fromisoformat(ds)
    except (ValueError, TypeError):
        try:
            return _dt.datetime.strptime(ds, "%Y%m%d").date()
        except (ValueError, TypeError):
            return None


def _get_profiles_for_path(path: Path):
    """Return list of Profile-like objects for a given file path.

    Tries nine-column parser first, then BMAP parser as fallback. Returns
    a list (possibly empty) of objects with attributes: name, date, x, z.
    """
    try:
        return read_9col_profiles(str(path))
    except (BeachProfileError, ValueError):
        # Try BMAP parser fallback
        try:
            from profcalc.common.bmap_io import BMAPParser

            parser = BMAPParser()
            return parser.parse_file(str(path))
        except (BeachProfileError, BMAPImportError, ValueError, OSError):
            return []


def compute_aer_noninteractive(
    before: str | Path,
    after: str | Path,
    *,
    profile_before: int | str | None = None,
    profile_after: int | str | None = None,
    dx: float = 0.1,
    use_bmap_core: bool = True,
) -> Dict[str, Any]:
    """Non-interactive AER wrapper for automation/tests.

    Args:
        before, after: file paths or registered dataset paths
        profile_before/profile_after: index (int, 0-based) or name (str) to
            select a specific profile within the file. If None, the function
            will select the latest-dated profile, or first if dates unavailable.
        dx: grid spacing
        use_bmap_core: whether to use BMAP split_trap_area logic

    Returns:
        dict: same structure as profcalc.core.aer.calculate_aer result
    """

    # Resolve inputs: accept either filesystem paths or dataset IDs registered
    # in the shared session (data_session). If a dataset id is provided, use
    # the dataset's registered path.
    def _resolve_input(inp: str | Path) -> Path:
        # If already a Path, return it
        p = Path(inp) if not isinstance(inp, Path) else inp
        # If this looks like a registered dataset id, prefer the session path
        datasets = data_session.list_datasets()
        if isinstance(inp, str) and inp in datasets:
            ds_info = datasets[inp]
            ds_path = ds_info.get("path")
            if ds_path:
                return Path(ds_path)
        # Otherwise return the path as given
        return p

    p_before = _resolve_input(before)
    p_after = _resolve_input(after)

    if not p_before.exists() or not p_after.exists():
        raise FileNotFoundError("Before/after file not found")

    profs_before = _get_profiles_for_path(p_before)
    profs_after = _get_profiles_for_path(p_after)

    if not profs_before:
        raise ValueError(f"No profiles found in before file: {p_before}")
    if not profs_after:
        raise ValueError(f"No profiles found in after file: {p_after}")

    def _select(profs, sel):
        if sel is None:
            # pick latest-dated if possible
            best = None
            best_date = None
            for p in profs:
                d = None
                try:
                    if isinstance(p.date, str):
                        d = _dt.date.fromisoformat(p.date)
                    elif isinstance(p.date, _dt.datetime):
                        d = p.date.date()
                    elif isinstance(p.date, _dt.date):
                        d = p.date
                except (ValueError, TypeError):
                    d = None
                if d and (best_date is None or d > best_date):
                    best_date = d
                    best = p
            return best or profs[0]
        if isinstance(sel, int):
            return profs[sel]
        # string -> name match
        for p in profs:
            if getattr(p, "name", None) == sel:
                return p
        # fallback to index 0
        return profs[0]

    chosen_before = _select(profs_before, profile_before)
    chosen_after = _select(profs_after, profile_after)

    return aer_mod.calculate_aer(
        chosen_before.x,
        chosen_before.z,
        chosen_after.x,
        chosen_after.z,
        None,
        None,
        dx=dx,
        use_bmap_core=use_bmap_core,
    )

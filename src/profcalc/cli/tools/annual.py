"""Handlers for annual monitoring workflows.

This module contains small CLI-facing handlers used by the interactive
menu. Each function is intentionally lightweight and delegates to the
data management handlers or the session object where appropriate.
"""

import datetime as _dt
from pathlib import Path
from typing import Optional

import profcalc.cli.menu_system as menu_system
from profcalc.cli.tools.data import import_data
from profcalc.cli.tools.data import session as data_session
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
        return active_dataset

    print("No active dataset found. Prompting user to import data...")
    file_path = input("Enter the path to the survey data file: ")

    try:
        result = import_data(file_path)
        print(f"Data imported successfully: {result['imported']} rows.")
        return result
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return None
    except ValueError as e:
        print(f"Value error: {e}")
        return None
    except (OSError, IOError) as e:  # Catch file-related errors
        print(f"An unexpected file-related error occurred: {e}")
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
                except Exception:
                    print("Invalid selection; falling back to file import.")

        # Fall back to prompting for a file path
        pth = input(f"Path to {label} survey (9-col CSV) (blank to cancel):").strip()
        if not pth:
            return None
        p = Path(pth)
        if not p.exists():
            print(f"File not found: {pth}")
            return None
        # Attempt to import/register the file so future tools see it
        try:
            import_data(str(p))
        except Exception:
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
    except Exception as exc:  # pragma: no cover - interactive
        print(f"Failed to read 9-col profiles: {exc}")
        return None

    def choose_profile(profiles, label: str):
        if not profiles:
            print(f"No profiles found in {label} file.")
            return None
        if len(profiles) == 1:
            return profiles[0]
        print(f"Multiple profiles found in {label} file:")
        for i, p in enumerate(profiles):
            print(f"{i + 1}. {p.name} ({p.date}) - {len(p.x)} pts")
        sel = input(f"Select profile number from {label} file (1-{len(profiles)}), blank=1: ").strip()
        if not sel:
            idx = 0
        else:
            try:
                idx = max(0, min(len(profiles) - 1, int(sel) - 1))
            except Exception:
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
        except Exception:
            try:
                return _dt.datetime.strptime(ds, "%Y%m%d").date()
            except Exception:
                return None

    date_before = _parse_date(prof_before.date)
    date_after = _parse_date(prof_after.date)

    dx_in = input("Grid spacing dx (feet, default 0.1): ").strip()
    try:
        dx = float(dx_in) if dx_in else 0.1
    except Exception:
        dx = 0.1

    use_bmap = input("Use BMAP core splitting logic? (Y/n) [Y]: ").strip().lower()
    use_bmap_core = (use_bmap != "n")

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
    except Exception as exc:  # pragma: no cover - interactive
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

    save = input("Save summary CSV? (enter path or blank to skip): ").strip()
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
        except Exception as exc:  # pragma: no cover - interactive
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
    except Exception:
        try:
            return _dt.datetime.strptime(ds, "%Y%m%d").date()
        except Exception:
            return None


def compute_aer_noninteractive(
    before: Path | str,
    after: Path | str,
    *,
    profile_before: Optional[str] = None,
    profile_after: Optional[str] = None,
    dx: float = 0.1,
    use_bmap_core: bool = True,
) -> dict:
    """Non-interactive AER computation for scripts and tests.

    Args:
        before, after: Paths to 9-column survey files (or dataset ids/paths)
        profile_before, profile_after: optional profile names to select when
            multiple profiles exist in a file. If omitted the first profile
            is used.
        dx: grid spacing
        use_bmap_core: whether to use the BMAP split_trap_area logic

    Returns:
        result dict from `profcalc.core.aer.calculate_aer`.

    Raises:
        FileNotFoundError: if input files are missing
        ValueError: if profiles cannot be found or parsed
    """
    pb = Path(before)
    pa = Path(after)
    if not pb.exists():
        raise FileNotFoundError(f"Input file not found: {pb}")
    if not pa.exists():
        raise FileNotFoundError(f"Input file not found: {pa}")

    before_profiles = read_9col_profiles(str(pb))
    after_profiles = read_9col_profiles(str(pa))

    if not before_profiles:
        raise ValueError(f"No profiles found in {pb}")
    if not after_profiles:
        raise ValueError(f"No profiles found in {pa}")

    def _select(profiles, name: Optional[str]):
        if name:
            for p in profiles:
                if p.name == name:
                    return p
            raise ValueError(f"Profile '{name}' not found")
        return profiles[0]

    prof_before = _select(before_profiles, profile_before)
    prof_after = _select(after_profiles, profile_after)

    date_before = _parse_date_str(prof_before.date)
    date_after = _parse_date_str(prof_after.date)

    return aer_mod.calculate_aer(
        prof_before.x,
        prof_before.z,
        prof_after.x,
        prof_after.z,
        date_before,
        date_after,
        dx=dx,
        use_bmap_core=use_bmap_core,
    )


def _get_profiles_for_path(path: Path):
    """Return list of Profile-like objects for a given file path.

    Tries nine-column parser first, then BMAP parser as fallback. Returns
    a list (possibly empty) of objects with attributes: name, date, x, z.
    """
    try:
        return read_9col_profiles(str(path))
    except Exception:
        # Try BMAP parser fallback
        try:
            from profcalc.common.bmap_io import BMAPParser

            parser = BMAPParser()
            return parser.parse_file(str(path))
        except Exception:
            return []


def compute_aer_noninteractive(
    before: str | Path,
    after: str | Path,
    *,
    profile_before: int | str | None = None,
    profile_after: int | str | None = None,
    dx: float = 0.1,
    use_bmap_core: bool = True,
):
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
    p_before = Path(before)
    p_after = Path(after)

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
                except Exception:
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

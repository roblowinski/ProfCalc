README — Quick run & test help
================================

This file contains quick commands and examples for running the ProfCalc
repo locally, running the AER demo, and executing tests/lint/type checks.

Activate virtual environment (PowerShell)

---------------------------------------
If you use the project's venv in the repository root, activate it with PowerShell:

. .\.venv\Scripts\Activate.ps1

Run the interactive menu (Quick Tools are menu-only)
---------------------------------------
Quick Tools are intended to be used from the interactive menu only. The
menu launcher sets up `PYTHONPATH` and starts the menu UI where Quick
Tools, Data Management and other workflows are available.

Recommended (PowerShell):

```powershell
.\run_menu.ps1
```

Convenience shim (Windows)
---------------------------
If you'd like to run the menu without the `.\` prefix on Windows, use the
provided `run_menu.cmd` shim in the repository root (see below). You can
also set `PYTHONPATH` manually and run the Python menu entrypoint:

```powershell
$env:PYTHONPATH = 'src'
python src\profcalc\cli\menu_system.py
```

Install dependencies

Install the pinned requirements (if you haven't already):

pip install -r requirements.txt
```

Run the compute AER demo script

The demo script is a tiny CLI that demonstrates the non-interactive AER API.

Examples:

- Run the demo directly against two files (before and after):

```powershell
python scripts\compute_aer_demo.py --before src\profcalc\data\temp\9Col_WithHeader.csv --after src\profcalc\data\temp\9Col_WithHeader.csv
```

- Register files with the in-memory session and then run against the registered dataset ids:
1. Register files with the session (the demo supports --register):

```powershell
python scripts\compute_aer_demo.py --register src\profcalc\data\temp\9Col_WithHeader.csv --register src\profcalc\data\temp\9Col_WithHeader.csv
```

1. Inspect registered datasets (open a Python REPL):
Examples:

- Run the demo directly against two files (before and after):

  ```powershell
  python scripts\compute_aer_demo.py --before src\profcalc\data\temp\9Col_WithHeader.csv --after src\profcalc\data\temp\9Col_WithHeader.csv
  ```

- Register files with the in-memory session and then run against the registered dataset ids:

  1. Register files with the session (the demo supports --register):

     ```powershell
     python scripts\compute_aer_demo.py --register src\profcalc\data\temp\9Col_WithHeader.csv --register src\profcalc\data\temp\9Col_WithHeader.csv
     ```

  1. Inspect registered datasets (open a Python REPL):

     ```powershell
     python -c "from profcalc.cli.tools.data import session; print(session.list_datasets())"
     ```

  1. Use the dataset ids printed by the previous command with the demo's --before/--after arguments.

Run tests (pytest)
-------------------

Run the entire test suite:

```powershell
python -m pytest tests/ -v
```

```powershell
python -c "from profcalc.cli.tools.data import session; print(session.list_datasets())"
```

1. Use the dataset ids printed by the previous command with the demo's --before/--after arguments.

Run tests (pytest)
-------------------

Run the entire test suite:

```powershell
python -m pytest tests/ -v
```

Run only the new AER edge-case tests:

```powershell
python -m pytest tests/test_aer_noninteractive_edges.py -q
```

Lint and auto-fix (ruff)
------------------------

Run ruff and auto-fix formatting/lint issues across code, tests and scripts:

```powershell
ruff check src/profcalc/ tests/ scripts/ --fix
```

Static typing (mypy)
--------------------

Run mypy across the codebase and tests:

```powershell
mypy src/profcalc/ tests/ scripts/
```

Notes & troubleshooting
-----------------------

- The demo script is intentionally lightweight and uses the same `Session`
  object as the CLI, so registering files via the demo will make them
  available to other CLI tools during that Python process.
- If you run into parsing errors for your own files, try opening them to
  confirm they match the expected 9-column format (headers or whitespace can
  be tolerated by the parser). The sample data files are under `src/profcalc/data/temp/`.

What the new numeric tests cover (plain language)
-----------------------------------------------

- Identical profiles: verifies that when two surveys are the same, the
  computed volume change is zero (no cut or fill) — a basic correctness
  check.

- Constant offset: checks a simple case where one profile is uniformly
  higher than the other by a fixed amount; the computed volume matches the
  expected area times offset (this validates the integration step).

- Convergence with grid spacing: ensures results don't change
  dramatically when using a much finer interpolation grid (dx), i.e. the
  calculation is stable as the grid gets finer.

-- Sparse (two-point) profiles: verifies minimal, realistic profiles with
  only two points are handled correctly.

If you'd like, I can add a short CI job YAML that runs the tests, linter and
type-checks on every push. Say the word and I'll add it.

Recent changes and important notes
---------------------------------

- Quick Tools are now menu-only: quick tools must be launched from the
  interactive menu (run via `.\run_menu.ps1` or `run_menu.cmd`). Attempting
  to run the quick-tool CLI entrypoints directly will raise a clear
  NotImplementedError or print guidance telling you to use the menu.

- Launcher helpers:
  - PowerShell: `.\run_menu.ps1` — sets `PYTHONPATH=src` and runs the menu.
  - Windows shim: `run_menu.cmd` — convenience shim in the repo root so you
    can run `run_menu` from cmd.exe / PowerShell without the `./` prefix.

- Menu navigation:
  - Help & Documentation is option 8 in the Main Menu and calls the
    `about()` summary.
  - Exit is option 9 in the Main Menu. Choosing `9` prints "Goodbye!" and
    returns from the menu so the launcher can exit cleanly.

- CSV parsing improvements:
  - The 9-column CSV parser now performs header normalization (strips
    punctuation and tolerates variant header forms like "EASTING (X)"
    / "NORTHING (Y)") and accepts compact date formats such as `YYYYMMDD`.
  - These fixes reduce common parsing failures when using external data
    exports.

- Central quick-tool logging:
  - Quick-tool exceptions are recorded to `src/profcalc/QuickToolErrors.log`.
    The quick-tool wrappers log unexpected exceptions and re-raise so
    failures are visible both in the log and the interactive session.

- Tests added:
  - Unit tests for the interactive menu and all submenus were added:
    `tests/test_menu_system.py` and `tests/test_menus_all_levels.py`.
    These use `monkeypatch` to simulate user input and stub heavy tool
    modules so menu routing can be validated quickly in CI.

- How to run the (new) menu tests locally:

```powershell
python -m pytest tests/test_menu_system.py -q
python -m pytest tests/test_menus_all_levels.py -q
```

If you want the full test suite run, just run `python -m pytest tests/ -v` as
before.

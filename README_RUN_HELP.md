README — Quick run & test help
================================

This file contains quick commands and examples for running the ProfCalc
repo locally, running the AER demo, and executing tests/lint/type checks.

Activate virtual environment (PowerShell)

---------------------------------------
If you use the project's venv in the repository root, activate it with PowerShell:

```powershell
. .\.venv\Scripts\Activate.ps1
```

Install dependencies

Install the pinned requirements (if you haven't already):

```powershell
pip install -r requirements.txt
```

Run the compute AER demo script

The demo script is a tiny CLI that demonstrates the non-interactive AER API.

Examples:

- Run the demo directly against two files (before and after):

```powershell
python scripts\compute_aer_demo.py --before data\temp\9Col_WithHeader.csv --after data\temp\9Col_WithHeader.csv
```

- Register files with the in-memory session and then run against the registered dataset ids:

1. Register files with the session (the demo supports --register):

```powershell
python scripts\compute_aer_demo.py --register data\temp\9Col_WithHeader.csv --register data\temp\9Col_WithHeader.csv
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
  be tolerated by the parser). The sample data files are under `data/temp/`.

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

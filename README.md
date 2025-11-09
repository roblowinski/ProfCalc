# Profile Analysis Tools

## Project Structure

The project is organized for clarity, maintainability, and ease of use:

- `src/profcalc/` — Production codebase (core logic, CLI, modules)
- `tests/` — Automated and manual test scripts for validation
- `validation/` — Enhanced validation scripts and tools
- `archive/` — Legacy, debug, and demonstration scripts (for reference only)
- `logs/` — Validation logs and output summaries
- `notebooks/` — Jupyter notebooks for exploratory analysis
- `ref_scripts/` — Reference implementations and legacy code
- `dev_scripts/` — Prototypes and experimental scripts (not for production)
- `src/profcalc/data/` — Input, output, and required data files (moved inside the package)
- `docs/` — Project documentation and workflow guides

## Overview

The Profile Analysis Tools package is a Python-based framework designed for coastal engineers to analyze beach profile data. It replicates the functionality of the USACE Beach Morphology Analysis Package (BMAP) and extends it with modern features for integration, testing, and customization.

This package includes tools for beach profile analysis, beachfill construction monitoring, and long-term coastal monitoring. It is designed to be modular and extendable to support a wide range of coastal engineering tasks.

## Features

- **BMAP-equivalent tools**: Tools for generating equilibrium profiles, profile comparisons, volume calculations, and more.
- **Profile comparison and analysis**: Tools for computing elevation differences, volume changes, and contour shifts.
- **Monitoring and construction tools**: Utilities for analyzing beach profile changes over time and during beachfill construction projects.
- **Data integration**: Compatible with CSV, Excel, and other formats for easy import of profile data.
- **Scalable architecture**: Easily extendable to include new tools or workflows as needed.

## Where to Find Things

- **Production code**: `src/profcalc/`
- **Test scripts**: `tests/`
- **Validation tools**: `validation/`
- **Debug/demo/reference scripts**: `archive/`, `ref_scripts/`
- **Logs and outputs**: `logs/`
- **Prototypes/experimental**: `dev_scripts/` (not for production)

## Data files and policy

Generated data and large binary artifacts (CSV outputs, shapefiles, archives) are kept out of source-controlled package code. See `DATA.md` for the data placement and handling policy, how to regenerate outputs, and recommended Git workflows (Git LFS, bundles, backups).

See `README_RUN_HELP.md` for details on running scripts and tests.

## Quick tools: centralized logging and tests

Quick tools (the small utilities under `src/profcalc/cli/quick_tools`) now use a
centralized rotating logger to capture error and diagnostic messages. The log
file is located at `src/profcalc/QuickToolErrors.log` by default and is written
using a RotatingFileHandler to avoid unbounded log growth.

If you're running tests or need to capture logs to a specific location, the
test-suite reconfigures the logger at runtime by overriding
`profcalc.cli.quick_tools.quick_tool_logger.LOG_FILE` and clearing the logger
handlers. This allows tests to assert log contents without affecting the
repository-level log file.

To run the quick-tool logging tests locally:

```powershell
# Run only logging-related tests
python -m pytest tests/test_quick_tools_logging.py -q
python -m pytest tests/test_quick_tools_logging_extended.py -q
python -m pytest tests/test_quick_tools_logging_more.py -q
```

You can run the full test suite similarly with `python -m pytest tests/ -v`.

## Installation

### Clone the Repository

To get started, clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/profcalc.git
cd profcalc
pip install -r requirements.txt
```

## Non-interactive AER API

The package exposes a small non-interactive wrapper to compute Annual Erosion Rate
between two surveys without user prompts. Use this from scripts or tests.

Python example:

```python
from profcalc.cli.tools.annual import compute_aer_noninteractive

# Arguments can be file paths or dataset IDs previously registered via
# `profcalc.cli.tools.data.import_data`.
res = compute_aer_noninteractive(

    "/path/to/before.csv",
    "/path/to/after.csv",
    dx=0.5,
    use_bmap_core=False,
)

print(res["cut_cuyd_per_ft"], res["fill_cuyd_per_ft"], res["all_cuyd_per_ft"])
```

If you have already registered the files with the in-memory session via
``profcalc.cli.tools.data.import_data(path)``, you may pass the returned
dataset id strings directly to `compute_aer_noninteractive` instead of
filesystem paths.

## Developer checks

This repository includes a static import-graph scanner that detects intra-package
import cycles (which are a common source of runtime import errors). It is
implemented in `import_graph.py` and is executed during CI. You can run it
locally with:

```powershell
python import_graph.py
```

If the script finds strongly-connected components (cycles) it will exit
non-zero and print the involved modules. The CI workflow runs this check and
will fail the job if cycles are introduced.

If you change package-level imports or refactor modules, run the scanner
to ensure no cycles were introduced.

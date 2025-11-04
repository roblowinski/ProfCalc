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

See `README_RUN_HELP.md` for details on running scripts and tests.

## Installation


### Clone the Repository

To get started, clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/profcalc.git
cd profcalc
pip install -r requirements.txt
```

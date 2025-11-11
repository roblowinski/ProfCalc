# MENU IMPLEMENTATION CHECKLIST

Generated: 2025-11-06

This file summarizes which menu items in the interactive CLI are already implemented, partially implemented, or remain as stubs.

Legend

- ✅ Implemented / usable
- ⚠️ Partial (interactive wrapper exists, core logic may be partial)
- ❌ Stub / not implemented

Summary by menu

## 1.0 Main Menu

- Data Management ........................................ ✅ (uses `profcalc.cli.tools.data` handlers)
- Annual Monitoring Report Analyses ..................... ✅ (menu + handlers in `profcalc.cli.tools.annual`)
- File Conversion Tools ................................ ⚠️ (conversion core in `profcalc.cli.tools.convert` exists; menu currently prints stub in some places)
- Profile Analysis Tools ............................... ⚠️ (menu shell exists; many options are stubs but some handlers exist under `profcalc.cli.tools`)
- Batch Processing ..................................... ❌ (menu placeholder)
- Configuration & Settings ............................. ❌ (placeholder)
- Quick Tools .......................................... ✅/⚠️ (several tools implemented: bounds, convert, assign, inventory; some quick-tool menu entries still stubbed)
- Help & Documentation ................................ ❌ (placeholder)
- Exit ................................................ ✅

## 1.1 Data Management

- Select Data Source .................................. ✅ (`select_data_source`, `ensure_data_source` use `profcalc.cli.tools.data`)
- Import Data (9-col CSV) ............................ ✅ (`profcalc.cli.tools.data.import_data`)
- List Registered Datasets ............................ ✅ (`data.list_datasets`)
- Select Active Dataset .............................. ✅ (`data.select_dataset`)
- View Data Summary .................................. ⚠️ (`data.summary` exists but is a stub message)
- Return to Main Menu ................................ ✅

## 1.2 Annual Monitoring

- Import Survey Data ................................ ✅ (`profcalc.cli.tools.annual.import_survey` + `data.import_data`)
- Compute Annual Erosion Rate (AER) .................. ✅ (`profcalc.cli.tools.annual.compute_aer` + non-interactive wrapper)
- Profile Analysis ................................... ⚠️ (menu shells exist; deeper options may be stubs)
- Shoreline Analysis ................................ ❌ (menu calls print stubs; some tooling may be available elsewhere)
- Condition Evaluation .............................. ❌ (stub)
- Reporting & Export ................................. ❌ (stub)
- Return to Main Menu ................................ ✅

## 1.3 Profile Analysis

- Ad-Hoc Analyses .................................... ⚠️ (many submenus added in `MENU_LIST.txt`; several sub-tools are present)
  - Profile Modifications ............................ ❌/⚠️ (menu earlier was a stub; some operations available in core modules not yet wired)
  - Profile Area/Volume .............................. ❌ (placeholder in `MENU_LIST.txt`)
  - Profile Shoreline Tracking ....................... ❌ (placeholder)
  - Profile Characteristics .......................... ❌ (placeholder)
  - Synthetic Profiles ............................... ❌ (placeholder)
- Annual Monitoring Analyses .......................... ✅ (linked to `profcalc.cli.tools.annual` menus/handlers)
- Construction Activities Analyses .................... ❌ (placeholder)
- Storm-Related Analyses ............................. ❌ (placeholder)

## Quick Tools (selected handlers)

- Fix BMAP point counts (point-count correction) ...... ✅ (`profcalc.cli.tools.fix_bmap.execute_from_menu` implemented)
- Format Conversion (BMAP/CSV/XYZ/Shapefile) ......... ✅ (`profcalc.cli.tools.convert` implemented)
- Profile Inventory .................................. ✅ (`profcalc.cli.tools.inventory.execute_from_menu` implemented)
- Assign Missing Profile Names ....................... ✅ (`profcalc.cli.tools.assign.execute_from_menu` implemented)
- Misc quick tools (some entries) .................... ⚠️/❌ (menu entries may still print stub)

## Core analysis function stubs in `menu_system.py`

- cross_sectional_analysis ........................... ❌ (prints stub)
- volumetric_change .................................. ❌ (prints stub)
- shoreline_change ................................... ❌ (prints stub)
- temporal_trends .................................... ❌ (prints stub)
- outlier_detection .................................. ❌ (prints stub)
- statistics_summaries ............................... ❌ (prints stub)
- export_results ..................................... ❌ (prints stub)

## Notes & Next steps

- Many CLI handlers intentionally wrap smaller modules in `profcalc.cli.tools` — where those modules exist, wiring menu items to call `execute_from_menu` or the module handler is straightforward.
- I recommend using the included `scripts/run_menu.py` runner (created alongside this checklist) to exercise implemented handlers interactively.
- For each ❌ stub, we can either implement the core logic or provide a prototype implementation that delegates to existing `profcalc.core` functions where available.

If you'd like, I can generate a CSV/Excel checklist or a prioritized list of which menu items to implement next.

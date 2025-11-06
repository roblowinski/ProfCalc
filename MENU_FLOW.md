ProfCalc Menu Flow
==================

This document maps the interactive menu functions in `src/profcalc/cli/menu_system.py` and shows the flow from one menu to another.

- Top-level entry points
- `launch_menu()` -> `select_data_source()` -> `main_menu()`
- `main_menu()` options:
  1. Data Management -> `data_management_menu()`
  2. Annual Monitoring Report Analyses -> `annual_monitoring_menu()`
  3. File Conversion Tools -> (stub)
  4. Profile Analysis Tools -> `profcalc_profcalc_menu()`
  5. Batch Processing -> (stub)
  6. Configuration & Settings -> (stub)
  7. Quick Tools -> `quick_tools_menu()`
  8. Help & Documentation -> (stub)
  9. Exit

## Menus and submenus (call graph)

`select_data_source()`

- options: database, file (calls `data_tools.import_data()`), exit

`data_management_menu()`

1. Change Data Source -> `select_data_source()`
1. Import Data -> calls `data_tools.import_data()`
1. List Registered Datasets -> `data_tools.list_datasets()`
1. Select Active Dataset -> `data_tools.select_dataset()`
1. View Data Summary -> `data_tools.summary()`
1. Back to Main Menu

`annual_monitoring_menu()`

1. Import Survey Data -> `data_tools.import_data()`
1. Compute AER -> imports `profcalc.cli.tools.annual` and calls `compute_aer()`
1. Profile Analysis -> `shoreline_analysis_menu()` (or other)
1. Other stubs/back

`profcalc_profcalc_menu()` (Profile Analysis Tools)

1. Survey vs. Design -> `survey_vs_design_menu()`
1. Survey vs. Survey -> `survey_vs_survey_menu()`

`quick_tools_menu()`

1. Bounds tool (stub)
1. Conversion submenu -> `conversion_submenu()`
1. Inventory tool (stub)
1. Assign tool (stub)

Notes and guidance for manual edits

- To add or change functionality, edit the specific submenu function (e.g., `annual_monitoring_menu`) and replace stub prints with calls into `src/profcalc/cli/tools/`.
- Keep user input and output isolated near the menu functions; the underlying logic should live in `cli/tools/*` modules.
- If you want to test a single menu interactively, use the `scripts/run_menu.py` helper.

# Quick Tools (menu wrappers)

This folder contains lightweight menu wrappers and helpers for the project's "quick tools" — small utilities exposed via the interactive menu and also usable from the command line.

Usage

- Menu: Run the main menu (e.g., run_menu.py or your usual menu launcher). The quick tools are available from the "Quick Tools" submenu. Interactive runs prompt for inputs and, when no output path is provided, write timestamped output files to avoid overwriting previous runs.

- CLI (non-interactive): Many quick tools expose a `execute_from_cli(args: list[str])` entrypoint. These accept typical command-line arguments and will use a default output path of the form `output_<toolname>.<ext>` when an explicit output path is not provided.

Helpers

- `quick_tool_utils.default_output_path(tool_name, input_path=None, ext=None)` — CLI default output naming: `output_<toolname>.<ext>` (uses the input path's directory when available).
- `quick_tool_utils.timestamped_output_path(tool_name, ext=None)` — Menu default output naming: `output_<toolname>_YYYYmmdd_HHMMSS.<ext>` (uses the current working directory).
- `quick_tool_logger.log_quick_tool_error(tool_name, message)` — Append timestamped error/warning lines to `src/profcalc/QuickToolErrors.log` for centralized quick-tool diagnostics.

Centralized logging & tests
---------------------------

Quick tools write errors and diagnostics to a centralized rotating log file by
default at `src/profcalc/QuickToolErrors.log`. The logger is implemented in
`quick_tool_logger.py` and exposes the helper `log_quick_tool_error(tool_name, message, exc=None)`.

Unit and integration tests in `tests/` reconfigure `quick_tool_logger.LOG_FILE`
to point at temporary log files (via `tmp_path`) and clear logger handlers so
each test can assert on the log contents without polluting the repository
log. If you need to capture logs while running tools manually, change
`quick_tool_logger.LOG_FILE` before importing the quick-tool modules.

Testing quick-tools logging examples:

```powershell
# Run the added quick-tool logging tests
python -m pytest tests/test_quick_tools_logging.py -q
python -m pytest tests/test_quick_tools_logging_extended.py -q
python -m pytest tests/test_quick_tools_logging_more.py -q
```


Notes

- For running scripts directly (outside `pip install -e .`), ensure `PYTHONPATH` includes the repository `src` directory so the `profcalc` package imports correctly.
- The quick-tool smoke tests are in `tests/test_quick_tools_smoke.py` and validate wrapper presence and helper behavior.

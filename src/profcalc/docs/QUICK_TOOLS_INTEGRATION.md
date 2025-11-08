# Quick Tools Integration Note

This short note documents the recent changes made to the "quick tools"
menu and the approach used to integrate the existing full-feature CLI
implementations from `src/profcalc/cli/tools/`.

What changed

- The interactive quick tools menu (`src/profcalc/cli/menu_system.py`) was
  updated to call the richer implementations under `profcalc.cli.tools`
  (e.g. `fix_bmap`, `bounds`, `inventory`, `assign`). This ensures the
  menu shows the most complete behaviour without duplicating code.
- Thin wrapper modules were added under
  `src/profcalc/cli/quick_tools/` for the tools listed above. These wrappers
  simply re-export the key entry points (`execute_from_cli`,
  `execute_from_menu`, and other helpers) from `profcalc.cli.tools` and
  provide safe fallback errors when the full implementation is not
  available.
- A small dispatcher `profcalc.cli.quick_tools.execute_from_cli` was
  added to maintain the historical package-level entrypoint used by some
  test scripts. The dispatcher forwards to
  `profcalc.cli.tools.convert.execute_from_cli` (conversion tests rely on
  that behaviour).

Why this approach

- Keeps a single source of truth (the full-feature `cli/tools` modules)
  while preserving the `profcalc.cli.quick_tools` namespace used by
  existing tests and callers.
- Avoids duplication and reduces maintenance overhead.

Next steps / recommendations

- If you prefer to keep `quick_tools` as dependency-free, lightweight
  implementations, we can port minimal functionality individually from
  `cli/tools` into `cli/quick_tools`. That requires ensuring any heavy
  dependencies (pandas, geopandas) are optional.
- Alternatively, we can consolidate everything into `cli/tools` and
  update imports and docs to use that package exclusively.

Files added/changed

- `src/profcalc/cli/menu_system.py` — quick tools menu wiring (calls into
  `cli.tools`).
- `src/profcalc/cli/quick_tools/__init__.py` — package-level dispatcher.
- `src/profcalc/cli/quick_tools/{fix_bmap,bounds,inventory,assign}.py`
  — thin wrappers that re-export implementations.

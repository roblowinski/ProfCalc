# How to Run ProfCalc Scripts and Tools


## For All Users

- Always run commands from the project root (where `src/` and `dev_scripts/` are siblings).
- Activate your virtual environment if you have one:
  `./venv/Scripts/Activate.ps1` (PowerShell)


## Running CLI Tools (in src/profcalc)

- Use the `-m` flag from the root:

  ```powershell
  python -m profcalc.cli.quick_tools.fix_bmap --help
  ```

- This works for any CLI-enabled module in `src/profcalc`.



## Running Scripts in dev_scripts/ (Prototypes Only)

- Set the `PYTHONPATH` to `src` so Python can find the `profcalc` package:

  ```powershell
  $env:PYTHONPATH = "src"
  python dev_scripts/your_script.py [args]
  ```

- You can also do this in one line:

  ```powershell
  $env:PYTHONPATH = "src"; python dev_scripts/your_script.py [args]
  ```


## Running Test Scripts (in tests/)

- Test scripts are now in the `tests/` directory:

  ```powershell
  $env:PYTHONPATH = "src"; python tests/test_bmap_minimal.py [args]
  ```


## Running Validation Scripts (in validation/)

- Enhanced validation tools are in the `validation/` directory:

  ```powershell
  $env:PYTHONPATH = "src"; python validation/validation_enhanced.py [args]
  ```


## Debug/Demo Scripts (archive/)

- Legacy, debug, and demonstration scripts are in `archive/` for reference only.


## Troubleshooting

- If you see `ModuleNotFoundError: No module named 'profcalc'`, make sure you:
  - Are running from the project root
  - Have set `PYTHONPATH` to `src` (for dev_scripts/)
  - Have installed the package in editable mode: `pip install -e .`



## Example: Run BMAP Integration Test

```powershell
$env:PYTHONPATH = "src"; python tests/test_fix_bmap_integration.py --input data/testing_files/bmap_ff_file_pointfix/250823-251005_Mantoloking_Merged_BD_190+00-300+00_BMAP_Free_Format_fix.ASC --contour 4.0 --profiles OC100-OC153 --year 2021 --output temp/test_contour_xlocs.csv
```

---

For more help, see the README or ask your friendly neighborhood developer!

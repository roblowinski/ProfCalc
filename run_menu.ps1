# PowerShell launcher for ProfCalc menu with correct PYTHONPATH
# Usage: .\run_menu.ps1

$env:PYTHONPATH = "src"
python src/profcalc/cli/menu_system.py

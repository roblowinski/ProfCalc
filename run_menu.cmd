@echo off
REM Windows shim to launch the ProfCalc interactive menu without needing to prefix .\
SET PYTHONPATH=src
python src\profcalc\cli\menu_system.py %*

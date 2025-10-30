# PowerShell helper to run dev_scripts with correct PYTHONPATH
# Usage: .\run_dev.ps1 your_script.py [args]

param(
    [string]$Script = $(throw "Please provide a script to run (e.g., test_fix_bmap_integration.py)"),
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$env:PYTHONPATH = "src"
python dev_scripts/$Script @Args

<#
Launch ProfCalc interactive menu.
#>

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]
    $Args
)

python -m profcalc @Args

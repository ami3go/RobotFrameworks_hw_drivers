param(
    [bool]$Simulated = $true,
    [string]$Port = "COM4",
    [string]$OutputDir = "results/examples"
)
$Runner = Join-Path (Split-Path -Parent $PSScriptRoot) "scripts\run_all_examples.ps1"
& $Runner -Simulated $Simulated -Port $Port -OutputDir $OutputDir
exit $LASTEXITCODE

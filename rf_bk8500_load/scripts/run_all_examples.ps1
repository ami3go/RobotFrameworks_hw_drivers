param(
    [bool]$Simulated = $true,
    [string]$Port = "COM4",
    [string]$OutputDir = "results/examples"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = [string](& (Join-Path $PSScriptRoot "ensure_environment.ps1"))

Write-Host "Running all examples with SIMULATED=$Simulated PORT=$Port"
& $Python -m robot --pythonpath $Root --outputdir (Join-Path $Root $OutputDir) `
    --variable "SIMULATED:$Simulated" --variable "PORT:$Port" `
    (Join-Path $Root "examples")
exit $LASTEXITCODE

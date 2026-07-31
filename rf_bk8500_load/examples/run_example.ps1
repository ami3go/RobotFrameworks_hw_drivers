param(
    [Parameter(Mandatory=$true, Position=0)][string]$Name,
    [bool]$Simulated = $true,
    [string]$Port = "COM4"
)
$Runner = Join-Path (Split-Path -Parent $PSScriptRoot) "scripts\run_example.ps1"
& $Runner -Name $Name -Simulated $Simulated -Port $Port
exit $LASTEXITCODE

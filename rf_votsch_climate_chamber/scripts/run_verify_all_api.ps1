param(
    [Parameter(Mandatory=$true)][string]$Ip,
    [int]$Port = 2049,
    [double]$TemperatureMin = -40,
    [double]$TemperatureMax = 180,
    [double]$SafeTestTemperature = 25,
    [switch]$AllowControl,
    [switch]$AllowAuxiliaryOutputs
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ArgsList = @(
    "$Root\scripts\run_verify_all_api.py",
    "--ip", $Ip,
    "--port", $Port,
    "--temperature-min", $TemperatureMin,
    "--temperature-max", $TemperatureMax,
    "--safe-test-temperature", $SafeTestTemperature
)
if ($AllowControl) { $ArgsList += "--allow-control" }
if ($AllowAuxiliaryOutputs) { $ArgsList += "--allow-auxiliary-outputs" }
python @ArgsList
exit $LASTEXITCODE

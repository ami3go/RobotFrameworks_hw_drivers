param(
    [string]$Port = "COM12",
    [int]$Baudrate = 9600,
    [int]$Address = 0,
    [double]$Timeout = 3.0
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = [string](& (Join-Path $PSScriptRoot "ensure_environment.ps1"))
$Diagnostic = Join-Path $Root "hardware_tests/02_serial_echo_diagnostic.py"

& $Python $Diagnostic --port $Port --baudrate $Baudrate --address $Address --timeout $Timeout
exit $LASTEXITCODE

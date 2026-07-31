param(
    [Parameter(Mandatory=$true, Position=0)][string]$Name,
    [bool]$Simulated = $true,
    [string]$Port = "COM4",
    [string]$Baudrate = "9600",
    [bool]$AutoDetectBaudrate = $false
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = [string](& (Join-Path $PSScriptRoot "ensure_environment.ps1"))
$File = Get-ChildItem (Join-Path $Root "examples") -Filter "*$Name*.robot" | Select-Object -First 1
if (-not $File) { throw "Example '$Name' was not found." }
$Out = Join-Path $Root ("results/examples/" + $File.BaseName)

Write-Host "Running $($File.Name) with SIMULATED=$Simulated PORT=$Port BAUDRATE=$Baudrate AUTO_DETECT=$AutoDetectBaudrate"
& $Python -m robot --pythonpath $Root --outputdir $Out --variable "SIMULATED:$Simulated" `
    --variable "PORT:$Port" --variable "BAUDRATE:$Baudrate" `
    --variable "AUTO_DETECT_BAUDRATE:$AutoDetectBaudrate" $File.FullName
exit $LASTEXITCODE

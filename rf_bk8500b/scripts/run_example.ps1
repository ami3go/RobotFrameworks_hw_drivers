param(
    [Parameter(Mandatory=$true, Position=0)][string]$Example,
    [Parameter(Position=1)][string]$Port,
    [Parameter(Position=2)][string]$PortB
)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$argsList = @("scripts/run_example.py", $Example)
if ($Example -like "09*") {
    if ($Port) { $argsList += @("--port-a", $Port) }
    if ($PortB) { $argsList += @("--port-b", $PortB) }
} elseif ($Port) {
    $argsList += @("--port", $Port)
}
& $python @argsList
exit $LASTEXITCODE

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python -m robot --outputdir results/hil --include hardware tests/hardware
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

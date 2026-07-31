$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python scripts/run_example.py @args
exit $LASTEXITCODE

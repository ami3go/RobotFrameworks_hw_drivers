$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python scripts/run_all_examples.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

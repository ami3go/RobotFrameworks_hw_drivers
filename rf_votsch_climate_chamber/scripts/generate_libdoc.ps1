$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python scripts/generate_libdoc.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python scripts/build_release.py
exit $LASTEXITCODE

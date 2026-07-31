$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python -m pytest --cov=rf_votsch_climate_chamber --cov-branch
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

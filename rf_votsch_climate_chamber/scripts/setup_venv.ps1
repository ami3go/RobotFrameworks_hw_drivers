$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python -m venv .venv; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; .venv\Scripts\python.exe -m pip install --upgrade pip; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; .venv\Scripts\python.exe -m pip install -e .[dev,docs]
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

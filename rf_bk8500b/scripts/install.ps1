$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python -m pip install --upgrade pip
python -m pip install .

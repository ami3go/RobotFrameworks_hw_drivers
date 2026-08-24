$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python -m unittest discover -s tests/unit -p "test_*.py" -v

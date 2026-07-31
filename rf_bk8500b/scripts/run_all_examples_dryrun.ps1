$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
& $python scripts/run_all_examples.py
exit $LASTEXITCODE

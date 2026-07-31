$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
& $python scripts/verify_project_structure.py
& $python scripts/build_release.py

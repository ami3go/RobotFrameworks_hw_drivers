$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python scripts/verify_project_structure.py
python scripts/verify_ai_contract.py
python -m pip install --upgrade build twine
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Get-ChildItem -Filter "*.egg-info" | Remove-Item -Recurse -Force
python scripts/generate_libdoc.py
python -m build
python -m twine check dist/*
python scripts/verify_release_artifacts.py
python scripts/build_release.py

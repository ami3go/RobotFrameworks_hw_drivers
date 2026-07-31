$ErrorActionPreference = "Stop"
Remove-Item -Recurse -Force build, dist, *.egg-info -ErrorAction SilentlyContinue
python -m build
python -m twine check dist/*

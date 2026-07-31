#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/verify_project_structure.py
python scripts/verify_ai_contract.py
python -m pip install --upgrade build twine
rm -rf build dist ./*.egg-info
python scripts/generate_libdoc.py
python -m build
python -m twine check dist/*
python scripts/verify_release_artifacts.py
python scripts/build_release.py

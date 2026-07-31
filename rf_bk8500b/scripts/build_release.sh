#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON=python3
[[ -x .venv/bin/python ]] && PYTHON=.venv/bin/python
"$PYTHON" scripts/verify_project_structure.py
exec "$PYTHON" scripts/build_release.py

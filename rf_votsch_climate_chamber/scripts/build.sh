#!/usr/bin/env bash
set -euo pipefail
rm -rf build dist *.egg-info
python -m build
python -m twine check dist/*

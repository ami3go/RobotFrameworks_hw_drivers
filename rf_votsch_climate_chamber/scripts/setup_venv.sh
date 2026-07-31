#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m venv .venv && .venv/bin/python -m pip install --upgrade pip && .venv/bin/python -m pip install -e .[dev,docs]

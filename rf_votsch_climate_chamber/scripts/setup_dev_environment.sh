#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev,docs]"
printf '%s\n' 'Environment ready. Activate with: source .venv/bin/activate'

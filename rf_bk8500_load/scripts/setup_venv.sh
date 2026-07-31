#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"
HOST_PY="${PYTHON:-python3}"

if [[ ! -x "$PY" ]]; then
  echo "Creating driver virtual environment: $VENV"
  "$HOST_PY" -m venv "$VENV"
fi
"$PY" -m pip install --upgrade pip
(
  cd "$ROOT"
  "$PY" -m pip install -e '.[dev]'
)
"$PY" -c 'import robot, serial, bk8500_load'
echo "Environment ready: $PY"

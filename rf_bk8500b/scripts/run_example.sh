#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON=python3
[[ -x .venv/bin/python ]] && PYTHON=.venv/bin/python
EXAMPLE=${1:?Usage: scripts/run_example.sh EXAMPLE [PORT] [PORT_B]}
if [[ "$EXAMPLE" == 09* ]]; then
  exec "$PYTHON" scripts/run_example.py "$EXAMPLE" --port-a "${2:-}" --port-b "${3:-}"
else
  exec "$PYTHON" scripts/run_example.py "$EXAMPLE" --port "${2:-${BK8500B_PORT:-}}"
fi

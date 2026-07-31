#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$($ROOT/scripts/ensure_environment.sh)"
SIMULATED="${SIMULATED:-True}"
PORT="${PORT:-/dev/ttyUSB0}"
exec "$PY" -m robot --pythonpath "$ROOT" --outputdir "$ROOT/results/examples" \
  --variable "SIMULATED:$SIMULATED" --variable "PORT:$PORT" "$ROOT/examples"

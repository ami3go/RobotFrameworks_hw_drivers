#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$($ROOT/scripts/ensure_environment.sh)"
PORT="${1:-/dev/ttyUSB0}"
exec "$PYTHON" "$ROOT/hardware_tests/02_serial_echo_diagnostic.py" --port "$PORT"

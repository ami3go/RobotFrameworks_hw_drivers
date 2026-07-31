#!/usr/bin/env bash
set -euo pipefail
[[ $# -ge 1 ]] || { echo "Usage: $0 example_name_or_number" >&2; exit 2; }
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$($ROOT/scripts/ensure_environment.sh)"
shopt -s nullglob
matches=("$ROOT"/examples/*"$1"*.robot)
[[ ${#matches[@]} -gt 0 ]] || { echo "Example '$1' was not found." >&2; exit 2; }
file="${matches[0]}"
name="$(basename "${file%.robot}")"
exec "$PY" -m robot --pythonpath "$ROOT" --outputdir "$ROOT/results/examples/$name" \
  --variable "SIMULATED:${SIMULATED:-True}" --variable "PORT:${PORT:-/dev/ttyUSB0}" \
  --variable "BAUDRATE:${BAUDRATE:-9600}" --variable "AUTO_DETECT_BAUDRATE:${AUTO_DETECT_BAUDRATE:-False}" "$file"

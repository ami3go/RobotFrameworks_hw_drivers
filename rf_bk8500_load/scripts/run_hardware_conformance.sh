#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-/dev/ttyUSB0}"
BAUDRATE="${2:-9600}"
AUTO_DETECT="${3:-false}"
BAUDRATE_CANDIDATES="${4:-4800,9600,19200,38400}"
PROBE_TIMEOUT="${5:-0.75}"
PYTHON="$($ROOT/scripts/ensure_environment.sh)"
OUT="$ROOT/results/hardware_conformance"
mkdir -p "$OUT"
"$PYTHON" -c 'import datetime,importlib.metadata,json,platform,robot; print(json.dumps({"captured_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"bk8500_load_distribution":importlib.metadata.version("bk8500-load"),"robot_framework":robot.__version__,"python":platform.python_version(),"platform":platform.platform()}, indent=2))' > "$OUT/software_versions.json"
"$PYTHON" -m robot --pythonpath "$ROOT" \
  --outputdir "$OUT" \
  --variable "PORT:$PORT" \
  --variable "BAUDRATE:$BAUDRATE" \
  --variable "AUTO_DETECT_BAUDRATE:$AUTO_DETECT" \
  --variable "BAUDRATE_CANDIDATES:$BAUDRATE_CANDIDATES" \
  --variable "PROBE_TIMEOUT:$PROBE_TIMEOUT" \
  "$ROOT/hardware_tests/01_all_library_keywords.robot"

#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export RF_BK8500_ROOT="$ROOT"
PRIVATE_PY="$ROOT/.venv/bin/python"

candidates=("$PRIVATE_PY")
[[ -n "${VIRTUAL_ENV:-}" ]] && candidates+=("$VIRTUAL_ENV/bin/python")
candidates+=("${PYTHON:-python3}")

for candidate in "${candidates[@]}"; do
  if command -v "$candidate" >/dev/null 2>&1 || [[ -x "$candidate" ]]; then
    if "$candidate" -c 'import os,sys; sys.path.insert(0,os.environ["RF_BK8500_ROOT"]); import importlib.metadata as m,robot,serial,bk8500_load; assert m.version("bk8500-load")==bk8500_load.__version__' >/dev/null 2>&1 \
      && "$candidate" -m robot --dryrun --pythonpath "$ROOT" --output NONE --log NONE --report NONE \
         "$ROOT/scripts/verify_library_import.robot" >/dev/null 2>&1 \
      && "$candidate" -m robot --dryrun --pythonpath "$ROOT" --output NONE --log NONE --report NONE \
         "$ROOT/examples" >/dev/null 2>&1 \
      && "$candidate" -m robot --dryrun --pythonpath "$ROOT" --output NONE --log NONE --report NONE \
         "$ROOT/hardware_tests/01_all_library_keywords.robot" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      exit 0
    fi
  fi
done

echo "No complete Robot Framework environment was found. Repairing the package-private .venv..." >&2
"$ROOT/scripts/setup_venv.sh" >&2
printf '%s\n' "$PRIVATE_PY"

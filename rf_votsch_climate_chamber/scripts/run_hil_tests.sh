#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m robot --outputdir results/hil --include hardware tests/hardware

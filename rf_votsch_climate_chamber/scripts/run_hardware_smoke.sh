#!/usr/bin/env bash
set -euo pipefail
python -m robot --pythonpath . --outputdir results-hardware "$@" tests/hardware/smoke_test.robot

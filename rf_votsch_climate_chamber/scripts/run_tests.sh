#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pytest --cov=rf_votsch_climate_chamber --cov-branch

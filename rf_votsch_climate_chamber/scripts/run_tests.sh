#!/usr/bin/env bash
set -euo pipefail
python -m ruff check .
python -m mypy votsch_climate_chamber
python -m pytest --cov=votsch_climate_chamber --cov-report=term-missing
python -m robot --pythonpath . --outputdir results tests/robot

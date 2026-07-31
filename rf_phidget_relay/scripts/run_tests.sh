#!/usr/bin/env sh
set -eu
python -m pytest
python -m ruff check rf_phidget_relay tests


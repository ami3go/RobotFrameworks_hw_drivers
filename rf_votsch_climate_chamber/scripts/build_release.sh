#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python scripts/build_release.py

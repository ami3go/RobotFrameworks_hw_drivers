#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python -m robot --dryrun --pythonpath . --outputdir results/examples examples

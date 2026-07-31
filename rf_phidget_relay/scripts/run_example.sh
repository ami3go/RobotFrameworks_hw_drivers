#!/usr/bin/env sh
set -eu
if [ "$#" -ne 1 ]; then
  echo "Usage: ./scripts/run_example.sh examples/02_single_channel.robot" >&2
  exit 2
fi
python -m robot --outputdir results "$1"


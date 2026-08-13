#!/usr/bin/env bash
# Single-command installer for every RobotFrameworks_hw_drivers package.
#
# Usage:
#   ./install.sh                # create ./.venv, install all packages (runtime only)
#   ./install.sh --dev          # also install each package's dev/test/docs extras
#   ./install.sh --no-venv      # install into the currently active Python env
#   ./install.sh --venv PATH    # use a venv at a custom path (default: .venv)
#   ./install.sh --python PY    # python executable to use (default: python3)
#
# Requires Python 3.11+ so that every package (rf_votsch_climate_chamber needs
# >=3.11) can be installed into the same environment.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

PYTHON="python3"
VENV_DIR=".venv"
USE_VENV=1
DEV=0

while [ $# -gt 0 ]; do
  case "$1" in
    --dev) DEV=1; shift ;;
    --no-venv) USE_VENV=0; shift ;;
    --venv) VENV_DIR="$2"; shift 2 ;;
    --python) PYTHON="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,15p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# Packages, in dependency-agnostic order (each installs standalone).
# Distribution name -> extras to add when --dev is passed.
PACKAGES=(
  rf_agilent33220a
  rf_agilent34411a
  rf_bk8500b
  rf_bk8500_load
  rf_ea_ps9000t
  rf_eresistor
  rf_hp34401a
  rf_keysight_n6700
  rf_ngi_n83624
  rf_phidget_relay
  rf_picoscope2000a
  rf_slcan
  rf_tbs1000c
  rf_votsch_climate_chamber
)

declare -A DEV_EXTRAS=(
  [rf_agilent33220a]="dev"
  [rf_agilent34411a]="dev"
  [rf_bk8500b]="dev"
  [rf_bk8500_load]="dev"
  [rf_ea_ps9000t]="dev"
  [rf_eresistor]="test,yaml"
  [rf_hp34401a]="dev,hardware"
  [rf_keysight_n6700]="dev,docs"
  [rf_ngi_n83624]="dev,docs"
  [rf_phidget_relay]="dev"
  [rf_picoscope2000a]="dev"
  [rf_slcan]="dev"
  [rf_tbs1000c]="dev"
  [rf_votsch_climate_chamber]="dev,docs"
)

if [ "$USE_VENV" -eq 1 ]; then
  if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating virtual environment at $VENV_DIR"
    "$PYTHON" -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
fi

echo "==> Using $(command -v python) ($(python --version))"
python -m pip install --upgrade pip

for pkg in "${PACKAGES[@]}"; do
  if [ "$DEV" -eq 1 ]; then
    target="./${pkg}[${DEV_EXTRAS[$pkg]}]"
  else
    target="./${pkg}"
  fi
  echo "==> Installing $target"
  python -m pip install -e "$target"
done

echo
echo "==> All ${#PACKAGES[@]} packages installed."
if [ "$USE_VENV" -eq 1 ]; then
  echo "    Activate with: source $VENV_DIR/bin/activate"
fi

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/verify_project_structure.py
python scripts/verify_ai_contract.py
python -m pytest
python -m robot --outputdir results/acceptance tests/robot/adapter_acceptance.robot
python scripts/run_all_examples.py --outputdir results/dryrun
python -m ruff check BK8500BLibrary tests/test_robot_library.py tests/robot/FakeBK8500BLibrary.py scripts/build_release.py scripts/run_example.py scripts/run_all_examples.py scripts/verify_project_structure.py scripts/verify_ai_contract.py scripts/verify_release_artifacts.py scripts/generate_libdoc.py tests/test_ai_contract.py
python -m compileall -q BK8500BLibrary bk8500b scripts

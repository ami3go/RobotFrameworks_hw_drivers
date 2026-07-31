#!/usr/bin/env python3
"""Run the bounded D0 release checks without building distributions."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*arguments: str) -> None:
    subprocess.run([sys.executable, *arguments], cwd=ROOT, check=True)


def main() -> int:
    for script in (
        "generate_rfds_metadata.py",
        "validate_structure.py",
        "validate_ai_contract.py",
        "validate_call_protocol_conformance.py",
        "run_python_simulator_smoke.py",
    ):
        run(str(ROOT / "scripts" / script))
    run("-m", "pytest", "--cov=rf_votsch_climate_chamber", "--cov-branch", "-q")
    print("PASS: D0 release checks complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

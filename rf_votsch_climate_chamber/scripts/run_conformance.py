#!/usr/bin/env python3
"""Run RFDS-019 simulator conformance and create timestamped Robot evidence."""
from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = root / "results/call_protocol_conformance/votsch_climate_chamber" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "robot",
        "--pythonpath",
        str(root),
        "--outputdir",
        str(output_dir),
        str(root / "tests/conformance/driver_call_protocol_conformance.robot"),
    ]
    completed = subprocess.run(command, cwd=root, check=False)
    print(f"RFDS-019 results: {output_dir}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run the opt-in real-chamber all-API Robot verification suite."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ip", required=True, help="Climate chamber IP address or hostname")
    parser.add_argument("--port", type=int, default=2049)
    parser.add_argument("--temperature-min", type=float, default=-40.0)
    parser.add_argument("--temperature-max", type=float, default=180.0)
    parser.add_argument("--safe-test-temperature", type=float, default=25.0)
    parser.add_argument("--allow-control", action="store_true")
    parser.add_argument("--allow-auxiliary-outputs", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = root / "results" / "hardware_api_verification" / timestamp
    variables = {
        "CHAMBER_IP": args.ip,
        "CHAMBER_PORT": args.port,
        "TEMPERATURE_MIN": args.temperature_min,
        "TEMPERATURE_MAX": args.temperature_max,
        "SAFE_TEST_TEMPERATURE": args.safe_test_temperature,
        "ALLOW_CHAMBER_CONTROL": str(args.allow_control),
        "ALLOW_AUXILIARY_OUTPUTS": str(args.allow_auxiliary_outputs),
    }
    command = [
        sys.executable,
        "-m",
        "robot",
        "--pythonpath",
        str(root),
        "--outputdir",
        str(output_dir),
    ]
    for name, value in variables.items():
        command.extend(["--variable", f"{name}:{value}"])
    command.append(str(root / "tests" / "hardware" / "verify_all_api.robot"))
    completed = subprocess.run(command, cwd=root, check=False)
    print(f"Hardware API verification results: {output_dir}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

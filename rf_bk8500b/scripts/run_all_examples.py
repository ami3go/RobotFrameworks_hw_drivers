"""Validate all examples, or execute all of them only after explicit opt-in."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute examples against hardware. Without this flag, Robot dry-run is used.",
    )
    parser.add_argument("--outputdir", default=str(ROOT / "results" / "examples"))
    args = parser.parse_args()

    if args.execute:
        required = ("BK8500B_PORT", "BK8500B_PORT_A", "BK8500B_PORT_B")
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            raise SystemExit("Execution requires environment variables: " + ", ".join(missing))

    command = [sys.executable, "-m", "robot", "--outputdir", args.outputdir]
    if not args.execute:
        command.append("--dryrun")
    command.append(str(ROOT / "examples"))
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

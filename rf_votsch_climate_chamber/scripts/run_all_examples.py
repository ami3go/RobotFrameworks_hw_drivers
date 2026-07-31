#!/usr/bin/env python3
"""Run or dry-run every packaged Robot Framework example."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Parse examples without executing them")
    args = parser.parse_args()
    command = [
        sys.executable,
        "-m",
        "robot",
        "--pythonpath",
        str(ROOT),
        "--outputdir",
        str(ROOT / "results/examples"),
    ]
    if args.dry_run:
        command.append("--dryrun")
    command.extend(str(path) for path in sorted((ROOT / "examples").glob("*.robot")))
    print(" ".join(command))
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())

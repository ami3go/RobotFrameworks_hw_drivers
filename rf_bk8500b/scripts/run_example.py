"""Run one Robot Framework example with explicit instrument-port handling."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def find_example(selector: str) -> Path:
    candidate = Path(selector)
    if candidate.suffix == ".robot":
        direct = candidate if candidate.is_absolute() else EXAMPLES / candidate.name
        if direct.is_file():
            return direct

    matches = sorted(EXAMPLES.glob(f"{selector}*.robot"))
    if not matches:
        available = ", ".join(path.name for path in sorted(EXAMPLES.glob("*.robot")))
        raise SystemExit(f"No example matches {selector!r}. Available: {available}")
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise SystemExit(f"Selector {selector!r} is ambiguous: {names}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one BK8500B Robot Framework example. Example selectors may be 01, 01_identify, or a .robot filename."
    )
    parser.add_argument("example", help="Example number, prefix, or filename")
    parser.add_argument("--port", help="Single-load port; sets BK8500B_PORT")
    parser.add_argument("--port-a", help="First port for the multi-load example")
    parser.add_argument("--port-b", help="Second port for the multi-load example")
    parser.add_argument("--outputdir", default=str(ROOT / "results"), help="Robot output directory")
    parser.add_argument("--dryrun", action="store_true", help="Validate syntax and keyword resolution without hardware access")
    parser.add_argument("robot_args", nargs=argparse.REMAINDER, help="Additional Robot Framework arguments after --")
    args = parser.parse_args()

    suite = find_example(args.example)
    env = os.environ.copy()
    if args.port:
        env["BK8500B_PORT"] = args.port
    if args.port_a:
        env["BK8500B_PORT_A"] = args.port_a
    if args.port_b:
        env["BK8500B_PORT_B"] = args.port_b

    if not args.dryrun:
        if suite.name.startswith("09_"):
            missing = [name for name in ("BK8500B_PORT_A", "BK8500B_PORT_B") if not env.get(name)]
        else:
            missing = [] if env.get("BK8500B_PORT") else ["BK8500B_PORT"]
        if missing:
            raise SystemExit(
                "Missing instrument port configuration: "
                + ", ".join(missing)
                + ". Use command options or environment variables."
            )

    command = [sys.executable, "-m", "robot", "--outputdir", args.outputdir]
    if args.dryrun:
        command.append("--dryrun")
    extra = args.robot_args
    if extra and extra[0] == "--":
        extra = extra[1:]
    command.extend(extra)
    command.append(str(suite))

    print(f"Running {suite.name}")
    print("Command:", " ".join(command))
    return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

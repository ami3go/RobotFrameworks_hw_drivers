#!/usr/bin/env python3
"""List or run the packaged Robot Framework examples.

This wrapper keeps example execution consistent on Windows and Linux. It uses
``python -m robot`` so the same Python interpreter and virtual environment are
used for Robot Framework and the installed library.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = PROJECT_ROOT / "examples"
RESULTS_ROOT = PROJECT_ROOT / "results" / "examples"


def examples() -> list[Path]:
    """Return examples in their numbered filename order."""
    return sorted(EXAMPLES_DIR.glob("*.robot"))


def resolve_example(selector: str) -> Path:
    """Resolve a numeric index, filename, or relative path to one example."""
    available = examples()
    if selector.isdigit():
        number = int(selector)
        if 1 <= number <= len(available):
            return available[number - 1]

    candidate = Path(selector)
    if not candidate.is_absolute():
        direct = EXAMPLES_DIR / candidate
        if direct.exists():
            return direct
        candidate = PROJECT_ROOT / candidate
    if candidate.exists() and candidate.suffix.lower() == ".robot":
        return candidate.resolve()

    names = ", ".join(path.name for path in available)
    raise SystemExit(f"Unknown example {selector!r}. Available examples: {names}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", nargs="?", help="example number, filename, or path")
    parser.add_argument("--list", action="store_true", help="list packaged examples")
    parser.add_argument("--dryrun", action="store_true", help="validate without executing keywords")
    parser.add_argument(
        "--variable",
        action="append",
        default=[],
        metavar="NAME:VALUE",
        help="Robot variable; may be specified more than once",
    )
    parser.add_argument(
        "--loglevel",
        default="INFO",
        help="Robot log level, for example INFO or DEBUG",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    available = examples()

    if args.list or args.example is None:
        for index, path in enumerate(available, start=1):
            print(f"{index:02d}: {path.name}")
        return 0 if args.list else 2

    example = resolve_example(args.example)
    output_dir = RESULTS_ROOT / example.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "robot",
        "--pythonpath",
        str(PROJECT_ROOT),
        "--outputdir",
        str(output_dir),
        "--loglevel",
        args.loglevel,
    ]
    if args.dryrun:
        command.append("--dryrun")
    for variable in args.variable:
        command.extend(["--variable", variable])
    command.append(str(example))

    print("Running:", " ".join(command))
    return subprocess.call(command, cwd=PROJECT_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())

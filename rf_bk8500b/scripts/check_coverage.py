"""Enforce production-package statement and branch coverage thresholds."""
from __future__ import annotations

import json
from pathlib import Path
import sys

MIN_STATEMENT = 95.0
MIN_BRANCH = 90.0
MIN_CODEC_BRANCH = 100.0


def percentage(covered: int, total: int) -> float:
    return 100.0 if total == 0 else covered / total * 100.0


def main(path: str = "coverage.json") -> int:
    report = json.loads(Path(path).read_text(encoding="utf-8"))
    package = {name: data for name, data in report["files"].items() if name.startswith("bk8500b/")}
    statements = sum(data["summary"]["num_statements"] for data in package.values())
    covered_statements = sum(data["summary"]["covered_lines"] for data in package.values())
    branches = sum(data["summary"]["num_branches"] for data in package.values())
    covered_branches = sum(data["summary"]["covered_branches"] for data in package.values())
    statement_pct = percentage(covered_statements, statements)
    branch_pct = percentage(covered_branches, branches)

    codec = package["bk8500b/protocol/legacy_codec.py"]["summary"]
    codec_branch_pct = percentage(codec["covered_branches"], codec["num_branches"])

    print(f"Production package statement coverage: {statement_pct:.2f}%")
    print(f"Production package branch coverage: {branch_pct:.2f}%")
    print(f"Legacy codec branch coverage: {codec_branch_pct:.2f}%")

    failures = []
    if statement_pct < MIN_STATEMENT:
        failures.append(f"statement coverage < {MIN_STATEMENT:.2f}%")
    if branch_pct < MIN_BRANCH:
        failures.append(f"branch coverage < {MIN_BRANCH:.2f}%")
    if codec_branch_pct < MIN_CODEC_BRANCH:
        failures.append(f"legacy codec branch coverage < {MIN_CODEC_BRANCH:.2f}%")
    if failures:
        print("Coverage gate failed: " + "; ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "coverage.json"))

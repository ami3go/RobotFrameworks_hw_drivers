#!/usr/bin/env python3
"""Compare the current public API with an optional previous YAML snapshot."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "api" / "public_api.yaml"
PREVIOUS = ROOT / "api" / "public_api.previous.yaml"


def by_keyword(document: dict[str, object]) -> dict[str, dict[str, object]]:
    return {entry["keyword"]: entry for entry in document["keywords"]}  # type: ignore[index]


def main() -> int:
    current = yaml.safe_load(CURRENT.read_text(encoding="utf-8"))
    if not PREVIOUS.exists():
        print("No previous snapshot; current API is the comparison baseline.")
        return 0
    previous = yaml.safe_load(PREVIOUS.read_text(encoding="utf-8"))
    old = by_keyword(previous)
    new = by_keyword(current)
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(
        name for name in set(old) & set(new) if old[name]["signature"] != new[name]["signature"]
    )
    print("Added:", added)
    print("Removed:", removed)
    print("Changed signatures:", changed)
    return 1 if removed or changed else 0


if __name__ == "__main__":
    raise SystemExit(main())

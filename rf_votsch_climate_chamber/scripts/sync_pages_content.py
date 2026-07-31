#!/usr/bin/env python3
"""Mirror release-controlled guide/history/review Markdown into MkDocs docs.

The root folders are mandatory project artifacts. MkDocs only reads ``docs/``,
so this script keeps the GitHub Pages copies synchronized before validation or
deployment.
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sync_folder(name: str) -> None:
    source = ROOT / name
    target = ROOT / "docs" / name
    target.mkdir(parents=True, exist_ok=True)
    for old in target.glob("*.md"):
        old.unlink()
    for item in source.glob("*.md"):
        shutil.copy2(item, target / item.name)


def main() -> int:
    for folder in ("guide", "history", "review"):
        sync_folder(folder)
    print("GitHub Pages Markdown mirrors are synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

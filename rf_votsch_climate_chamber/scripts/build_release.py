#!/usr/bin/env python3
"""Build the project-standard release ZIP and SHA-256 checksum.

The archive filename contains the release version, while every member is rooted
under the fixed folder ``rf_votsch_climate_chamber/``. This permits a newer
release to replace the existing extracted project folder.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT_NAME = "rf_votsch_climate_chamber"
EXCLUDED_PARTS = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "results",
    "site",
    "build",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_NAMES = {".coverage", ".DS_Store"}


def release_version(root: Path) -> str:
    namespace: dict[str, str] = {}
    exec((root / "votsch_climate_chamber" / "version.py").read_text(encoding="utf-8"), namespace)
    version = namespace.get("RELEASE_VERSION")
    if not isinstance(version, str) or not version.startswith("v"):
        raise RuntimeError("RELEASE_VERSION must be a string such as 'v26.02'")
    return version


def include(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if any(part.endswith(".egg-info") for part in relative.parts):
        return False
    if path.name in EXCLUDED_NAMES:
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if root.name != PROJECT_ROOT_NAME:
        raise SystemExit(f"Run from fixed project root {PROJECT_ROOT_NAME!r}; found {root.name!r}")

    subprocess.run([sys.executable, str(root / "scripts" / "validate_project_layout.py")], check=True)
    subprocess.run([sys.executable, str(root / "scripts" / "validate_ai_contract.py")], check=True)

    version = release_version(root)
    output = root.parent / f"{PROJECT_ROOT_NAME}_{version}.zip"
    checksum_file = root.parent / f"{PROJECT_ROOT_NAME}_{version}_SHA256SUMS.txt"

    if output.exists():
        output.unlink()

    files = sorted(path for path in root.rglob("*") if include(path, root))
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            member = Path(PROJECT_ROOT_NAME) / path.relative_to(root)
            archive.write(path, member.as_posix())

    digest = sha256(output)
    checksum_file.write_text(f"{digest}  {output.name}\n", encoding="utf-8")

    print(f"Created {output}")
    print(f"Files: {len(files)}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

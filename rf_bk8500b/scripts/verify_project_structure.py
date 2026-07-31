"""Verify the project-specific Robot driver package layout."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DIRECTORIES = (
    "BK8500BLibrary",
    "bk8500b",
    "ai",
    "bench",
    "history",
    "review",
    "examples",
    "scripts",
    "guide",
    "docs",
    "tests",
    ".github/workflows",
)
BASE_REQUIRED_FILES = (
    "README.md",
    "PACKAGE_CONTENTS.md",
    "CHANGELOG.md",
    "LICENSE",
    "VERSION",
    "release.json",
    "ai/ai_contract.yaml",
    "ai/ai_contract.lock",
    "ai/rfds017.schema.json",
    "bench/system_ai_contract.yaml",
    "bench/README.md",
    "review/rfds017_rfds018_traceability.md",
    "guide/PYCHARM_SETUP.md",
    "guide/ROBOT_FRAMEWORK_SETUP.md",
    "docs/index.html",
    "docs/AI_CONTRACT.md",
    "docs/RFDS018_BENCH_TEMPLATE.md",
    "scripts/run_example.py",
    "scripts/build_release.py",
    "scripts/verify_ai_contract.py",
)


def main() -> int:
    errors: list[str] = []
    if ROOT.name != "rf_bk8500b":
        errors.append(f"Repository root must be named rf_bk8500b, found {ROOT.name}")

    for relative in REQUIRED_DIRECTORIES:
        if not (ROOT / relative).is_dir():
            errors.append(f"Missing required directory: {relative}")

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d{2}\.\d{2}", version):
        errors.append(f"VERSION must use YY.NN format, found {version!r}")
    version_files = (
        f"history/v{version}.md",
        f"review/v{version}_ai_contract_review.md",
    )
    for relative in (*BASE_REQUIRED_FILES, *version_files):
        if not (ROOT / relative).is_file():
            errors.append(f"Missing required file: {relative}")

    examples = sorted((ROOT / "examples").glob("*.robot"))
    if len(examples) < 10:
        errors.append(f"At least 10 Robot examples are required; found {len(examples)}")

    release = json.loads((ROOT / "release.json").read_text(encoding="utf-8"))
    expected_archive = f"rf_bk8500b_v{version}.zip"
    if release.get("archive_name") != expected_archive:
        errors.append(f"release.json archive_name must be {expected_archive}")
    if release.get("root_folder") != "rf_bk8500b":
        errors.append("release.json root_folder must be rf_bk8500b")
    if release.get("release") != version:
        errors.append(f"release.json release must be {version}")

    if errors:
        print("Project structure verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Project structure verified: {len(examples)} Robot examples, release v{version}, "
        "RFDS-017 and RFDS-018 files present"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

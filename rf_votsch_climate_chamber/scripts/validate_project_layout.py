#!/usr/bin/env python3
"""Validate mandatory Robot Framework Driver project/release content."""

from __future__ import annotations

from pathlib import Path
from typing import Any

EXPECTED_ROOT = "rf_votsch_climate_chamber"
REQUIRED_DIRECTORIES = {
    "ai",
    "history",
    "review",
    "examples",
    "scripts",
    "guide",
    "docs",
    ".github/workflows",
    "votsch_climate_chamber",
    "tests",
}
BASE_REQUIRED_FILES = {
    "README.md",
    "PROJECT_REQUIREMENTS.md",
    "pyproject.toml",
    "mkdocs.yml",
    "system_ai_contract.yaml",
    "ai/ai_contract.yaml",
    "ai/ai_contract.lock",
    "guide/PYCHARM_ROBOT_FRAMEWORK_SETUP.md",
    "guide/AI_CONTRACT_USAGE.md",
    "docs/index.md",
    ".github/workflows/ci.yml",
    ".github/workflows/pages.yml",
    "scripts/run_example.py",
    "scripts/build_release.py",
    "scripts/validate_ai_contract.py",
    "scripts/update_ai_contract_lock.py",
}


def release_version(root: Path) -> str:
    namespace: dict[str, Any] = {}
    exec((root / "votsch_climate_chamber" / "version.py").read_text(encoding="utf-8"), namespace)
    version = namespace.get("RELEASE_VERSION")
    if not isinstance(version, str) or not version.startswith("v"):
        raise RuntimeError("RELEASE_VERSION must be a string such as 'v26.02'")
    return version


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []

    if root.name != EXPECTED_ROOT:
        errors.append(f"project root must be {EXPECTED_ROOT!r}, found {root.name!r}")

    version = release_version(root)
    required_files = set(BASE_REQUIRED_FILES)
    required_files.update(
        {
            f"history/{version}.md",
            f"review/{version}_code_review.md",
            f"review/{version}_requirements_compliance.md",
            f"docs/RELEASE_NOTES_{version}.md",
            f"docs/VALIDATION_REPORT_{version}.md",
        }
    )

    for relative in sorted(REQUIRED_DIRECTORIES):
        if not (root / relative).is_dir():
            errors.append(f"missing required directory: {relative}/")

    for relative in sorted(required_files):
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")

    example_count = len(list((root / "examples").glob("*.robot")))
    if example_count < 10:
        errors.append(f"at least 10 Robot examples are required; found {example_count}")

    history_files = list((root / "history").glob("v*.md"))
    review_files = list((root / "review").glob("v*_code_review.md"))
    if not history_files:
        errors.append("history/ must contain at least one versioned history file")
    if not review_files:
        errors.append("review/ must contain at least one versioned code review")

    if errors:
        print("Project layout validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Project layout validation PASSED")
    print(f"- fixed root: {root.name}")
    print(f"- release: {version}")
    print(f"- Robot examples: {example_count}")
    print(f"- history files: {len(history_files)}")
    print(f"- code review files: {len(review_files)}")
    print("- RFDS-017 and RFDS-018 contract files: present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

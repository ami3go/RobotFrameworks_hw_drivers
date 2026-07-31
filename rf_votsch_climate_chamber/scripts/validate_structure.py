#!/usr/bin/env python3
"""Validate the RFDS-005 flat package and fixed release identity."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "rf_votsch_climate_chamber/__init__.py",
    "rf_votsch_climate_chamber/library.py",
    "rf_votsch_climate_chamber/lifecycle.py",
    "rf_votsch_climate_chamber/plugin.py",
    "rf_votsch_climate_chamber/resources/plugin_manifest.json",
    "ai/ai_contract.yaml",
    "ai/ai_contract.lock",
    "ai/system_ai_contract.template.yaml",
    "api/public_api.yaml",
    "api/public_api.schema.json",
    "config/schema.json",
    "config/default.yaml",
    "robot_resources/common.resource",
    "tests/unit",
    "tests/robot",
    "tests/integration",
    "tests/compatibility",
    "tests/replay",
    "tests/hil",
    "tests/performance",
    "tests/conformance/driver_call_protocol_conformance.robot",
    "examples/index.yaml",
    "scripts",
    "history",
    "review",
    "guide",
    "docs",
    "release",
    "README.md",
    "pyproject.toml",
]

errors: list[str] = []
if ROOT.name != "rf_votsch_climate_chamber":
    errors.append(f"root must be rf_votsch_climate_chamber, got {ROOT.name}")
if (ROOT / "src").exists():
    errors.append("unapproved src/ layout is present")
if (ROOT / "votsch_climate_chamber").exists():
    errors.append("removed legacy Python package votsch_climate_chamber is present")
if (ROOT / "setup.py").exists():
    errors.append("obsolete setup.py is present; pyproject.toml is authoritative")
if (ROOT / "rf_votsch_climate_chamber/base_adapter.py").exists():
    errors.append("removed temporary base_adapter.py is present")
for item in REQUIRED:
    if not (ROOT / item).exists():
        errors.append(f"missing {item}")
robots = list((ROOT / "examples").glob("*.robot"))
if len(robots) < 10:
    errors.append(f"at least 10 examples required, found {len(robots)}")
if errors:
    print("\n".join("FAIL: " + error for error in errors))
    raise SystemExit(1)
print(f"PASS: RFDS structure valid; {len(robots)} Robot examples; fixed root {ROOT.name}")

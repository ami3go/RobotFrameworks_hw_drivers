from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ai_contract_contains_every_public_keyword() -> None:
    contract = json.loads((ROOT / "ai" / "ai_contract.yaml").read_text(encoding="utf-8"))
    capabilities = contract["capabilities"]
    names = [capability["keyword"] for capability in capabilities]
    assert len(names) == 36
    assert len(names) == len(set(names))
    assert "Connect Climate Chamber" in names
    assert "Stop And Disconnect Climate Chamber" in names


def test_system_contract_is_conservative_template() -> None:
    contract = json.loads((ROOT / "system_ai_contract.yaml").read_text(encoding="utf-8"))
    assert contract["identity"]["status"] == "TEMPLATE_REQUIRES_OPERATOR_COMPLETION"
    assert contract["global_safety"]["control_authorization"] == "DENIED_WHILE_ANY_CRITICAL_FIELD_IS_UNKNOWN"
    assert contract["open_questions"]


def test_contract_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_ai_contract.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

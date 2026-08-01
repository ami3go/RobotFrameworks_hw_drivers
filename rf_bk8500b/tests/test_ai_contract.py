from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_validator() -> ModuleType:
    path = ROOT / "scripts" / "verify_ai_contract.py"
    spec = importlib.util.spec_from_file_location("verify_ai_contract", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rfds017_contract_is_fully_conformant() -> None:
    validator = load_validator()
    assert validator.validate_contract() == []


def test_rfds018_bench_template_has_all_required_sections() -> None:
    validator = load_validator()
    assert validator.validate_bench_template() == []


def test_contract_covers_exact_public_keyword_surface() -> None:
    validator = load_validator()
    surface = validator.public_keyword_surface()
    contract = yaml.safe_load((ROOT / "ai" / "ai_contract.yaml").read_text(encoding="utf-8"))
    capabilities = contract["capabilities"]
    assert len(surface) == 80
    assert [(item["keyword"], item["signature"]) for item in capabilities] == surface


def test_interface_lock_matches_current_public_surface() -> None:
    validator = load_validator()
    actual = (ROOT / "ai" / "ai_contract.lock").read_text(encoding="utf-8").strip()
    assert actual == validator.surface_hash()


def test_contract_never_uses_unknown_for_core_safety_classifications() -> None:
    contract = yaml.safe_load((ROOT / "ai" / "ai_contract.yaml").read_text(encoding="utf-8"))
    for capability in contract["capabilities"]:
        assert capability["risk_level"] != "UNKNOWN"
        assert capability["blocking"] != "UNKNOWN"
        assert capability["idempotency"] != "UNKNOWN"
        assert capability["retry"] != "UNKNOWN"

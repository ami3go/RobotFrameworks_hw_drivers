"""RFDS-017 conformance tests.

These enforce the ``conformance.rules`` section of ``ai/ai_contract.yaml``:
the contract and the code must not drift apart silently.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from pathlib import Path

import pytest
import yaml

import bk8500_load
from bk8500_load.library import BK8500Library
from bk8500_load.version import VERSION

ROOT = Path(__file__).resolve().parent.parent
AI_DIR = ROOT / "ai"
CONTRACT_PATH = AI_DIR / "ai_contract.yaml"
LOCK_PATH = AI_DIR / "ai_contract.lock"
ATEST_DIR = ROOT / "atest"


@pytest.fixture(scope="module")
def contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def library_keywords() -> dict[str, list[str]]:
    keywords: dict[str, list[str]] = {}
    for attribute in vars(BK8500Library).values():
        name = getattr(attribute, "robot_name", None)
        if not name:
            continue
        parameters = inspect.signature(attribute).parameters
        keywords[name] = [p for p in parameters if p != "self"]
    return keywords


# ------------------------------------------------------------------ structure


def test_all_mandatory_sections_are_present(contract):
    mandatory = {
        "identity",
        "mental_model",
        "state_machine",
        "resources",
        "dependencies",
        "capabilities",
        "error_catalogue",
        "safety_rules",
        "verification_objectives",
        "setup_teardown_contract",
        "limitations",
        "planning_hints",
        "unknown_handling",
        "conformance",
    }
    assert mandatory <= set(contract)


def test_every_capability_has_all_required_fields(contract):
    required = {
        "keyword",
        "signature",
        "purpose",
        "inputs",
        "outputs",
        "preconditions",
        "postconditions",
        "side_effects",
        "risk_level",
        "timing",
        "stabilization_delay_s",
        "retry_policy",
        "errors",
        "exclusive_resources",
    }
    for capability in contract["capabilities"]:
        missing = required - set(capability)
        assert not missing, f"{capability.get('keyword')} is missing {sorted(missing)}"


def test_risk_levels_use_the_defined_vocabulary(contract):
    allowed = {"none", "low", "medium", "high", "critical"}
    for capability in contract["capabilities"]:
        assert capability["risk_level"] in allowed, capability["keyword"]


# ---------------------------------------------------------------- CR-1 / CR-2


def test_every_contract_capability_exists(contract, library_keywords):
    """CR-1: contract keywords exist in the library with the documented arguments."""
    for capability in contract["capabilities"]:
        name = capability["keyword"]
        assert name in library_keywords, f"Contract documents unknown keyword '{name}'"
        documented = re.findall(r"\s{4}([a-z_]+)(?==|$)", capability["signature"])
        for argument in documented:
            assert argument in library_keywords[name], (
                f"{name}: contract documents argument '{argument}' which the keyword does not accept"
            )


def test_no_undocumented_keywords(contract, library_keywords):
    """CR-2: the library exposes nothing the contract does not describe."""
    documented = {capability["keyword"] for capability in contract["capabilities"]}
    undocumented = set(library_keywords) - documented
    assert not undocumented, f"Keywords missing from the contract: {sorted(undocumented)}"


# ---------------------------------------------------------------- CR-3 / CR-4


def test_error_catalogue_matches_exceptions(contract):
    """CR-3: every catalogued error is a real exported exception class."""
    for entry in contract["error_catalogue"]:
        error_class = getattr(bk8500_load, entry["id"], None)
        assert error_class is not None, f"{entry['id']} is not exported by the package"
        assert issubclass(error_class, bk8500_load.BK8500Error)


def test_capability_errors_are_catalogued(contract):
    """CR-4: capabilities only reference catalogued errors."""
    catalogued = {entry["id"] for entry in contract["error_catalogue"]}
    for capability in contract["capabilities"]:
        for error in capability["errors"]:
            assert error in catalogued, f"{capability['keyword']} references uncatalogued {error}"


# ------------------------------------------------------------------ CR-5 / -6


def test_version_matches_package(contract):
    """CR-5: the contract is generated for the package version it ships with."""
    assert contract["identity"]["version"] == VERSION
    assert contract["contract"]["generated_for_driver_version"] == VERSION


def test_lock_file_matches_contract():
    """CR-6: the lock pins the current contract and keyword surface."""
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    digest = hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest()
    assert lock["contract_sha256"] == digest, (
        "ai_contract.yaml changed without regenerating the lock: run tools/generate_lock.py"
    )
    assert lock["driver_version"] == VERSION


def test_lock_file_matches_keyword_surface(library_keywords):
    """CR-6: a signature change without a lock regeneration is a failure."""
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    surface = sorted(f"{name}({', '.join(arguments)})" for name, arguments in library_keywords.items())
    digest = hashlib.sha256("\n".join(surface).encode("utf-8")).hexdigest()
    assert lock["keyword_surface_sha256"] == digest, (
        "Keyword signatures changed without regenerating the lock: run tools/generate_lock.py"
    )


# ------------------------------------------------------------------- CR-7


def test_verification_objectives_have_tests(contract):
    """CR-7: every verification objective is referenced by a Robot test."""
    suites = "\n".join(path.read_text(encoding="utf-8") for path in ATEST_DIR.rglob("*.robot"))
    for objective in contract["verification_objectives"]:
        assert objective["id"] in suites, f"No Robot test references {objective['id']}"


def test_safety_rules_are_uniquely_identified(contract):
    ids = [rule["id"] for rule in contract["safety_rules"]["hard_rules"]]
    assert len(ids) == len(set(ids))

#!/usr/bin/env python3
"""Validate RFDS-017 and RFDS-018 machine-readable contracts.

The files use JSON syntax, which is a valid YAML 1.2 subset. Keeping the
validator on Python's standard library makes conformance checks available in a
clean release environment before optional documentation dependencies are
installed.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "ai" / "ai_contract.yaml"
LOCK_PATH = ROOT / "ai" / "ai_contract.lock"
SYSTEM_PATH = ROOT / "system_ai_contract.yaml"
SOURCE_PATH = ROOT / "votsch_climate_chamber" / "robot_library.py"
VERSION_PATH = ROOT / "votsch_climate_chamber" / "version.py"

REQUIRED_DRIVER_SECTIONS = {
    "schema",
    "identity",
    "mental_model",
    "state_machine",
    "resources",
    "dependencies",
    "capabilities",
    "errors",
    "safety",
    "verification_objectives",
    "setup_teardown",
    "limitations",
    "planning_hints",
    "unknown_handling",
    "conformance",
}
REQUIRED_CAPABILITY_FIELDS = {
    "keyword",
    "signature",
    "purpose",
    "risk_level",
    "blocking",
    "idempotency",
    "retry",
    "typical_execution_time_s",
    "stabilization_time_s",
    "valid_in_states",
    "resulting_state",
    "arguments",
    "returns",
    "preconditions",
    "postconditions",
    "coupling",
    "side_effects",
    "exclusive_resources",
    "raises",
}
REQUIRED_SYSTEM_SECTIONS = {
    "available_drivers",
    "physical_topology",
    "shared_resources",
    "signal_graph",
    "preferred_measurement_sources",
    "requirement_coverage",
    "test_templates",
    "bench_constraints",
    "scheduling_rules",
    "global_safety",
}
COUPLING_PREFIXES = ("REQUIRES:", "FORBIDS:", "ORDER:", "MUTEX:")


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required contract file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON-compatible YAML in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain one mapping at the root")
    return data


def release_version() -> str:
    namespace: dict[str, Any] = {}
    exec(VERSION_PATH.read_text(encoding="utf-8"), namespace)
    version = namespace.get("RELEASE_VERSION")
    if not isinstance(version, str):
        raise ValueError("RELEASE_VERSION is missing from version.py")
    return version


def keyword_manifest() -> list[tuple[str, str, list[dict[str, Any]]]]:
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    found: list[tuple[str, str, list[dict[str, Any]]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        keyword_name: str | None = None
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and decorator.func.id == "keyword"
                and decorator.args
                and isinstance(decorator.args[0], ast.Constant)
            ):
                keyword_name = str(decorator.args[0].value)
        if keyword_name is None:
            continue

        positional = list(node.args.posonlyargs) + list(node.args.args)
        defaults: list[ast.expr | None] = [None] * (
            len(positional) - len(node.args.defaults)
        ) + list(node.args.defaults)
        arguments: list[dict[str, Any]] = []
        for argument, default in zip(positional, defaults, strict=True):
            if argument.arg == "self":
                continue
            item: dict[str, Any] = {
                "name": argument.arg,
                "python_type": ast.unparse(argument.annotation)
                if argument.annotation
                else "Any",
                "required": default is None,
            }
            if default is not None:
                item["default_expression"] = ast.unparse(default)
            arguments.append(item)
        for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True):
            item = {
                "name": argument.arg,
                "python_type": ast.unparse(argument.annotation)
                if argument.annotation
                else "Any",
                "required": default is None,
            }
            if default is not None:
                item["default_expression"] = ast.unparse(default)
            arguments.append(item)

        signature_parts = []
        for argument_data in arguments:
            text = argument_data["name"]
            if not argument_data["required"]:
                text += "=" + argument_data["default_expression"]
            signature_parts.append(text)
        signature = f"{keyword_name}({', '.join(signature_parts)})"
        found.append((keyword_name, signature, arguments))
    return sorted(found, key=lambda item: item[0])


def manifest_hash(manifest: list[tuple[str, str, list[dict[str, Any]]]]) -> str:
    text = "\n".join(f"{name}|{signature}" for name, signature, _ in manifest) + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate() -> list[str]:
    errors: list[str] = []
    try:
        contract = load_json(CONTRACT_PATH)
        lock = load_json(LOCK_PATH)
        system = load_json(SYSTEM_PATH)
        version = release_version()
    except ValueError as exc:
        return [str(exc)]

    missing = sorted(REQUIRED_DRIVER_SECTIONS - contract.keys())
    if missing:
        errors.append(f"ai_contract.yaml missing sections: {', '.join(missing)}")

    schema = contract.get("schema", {})
    if schema.get("id") != "RFDS-017" or str(schema.get("version")) != "3.0":
        errors.append("ai_contract.yaml must declare RFDS-017 version 3.0")
    if contract.get("identity", {}).get("release_version") != version:
        errors.append("ai_contract identity release_version does not match version.py")

    manifest = keyword_manifest()
    source_by_name = {name: (signature, args) for name, signature, args in manifest}
    capabilities = contract.get("capabilities", [])
    if not isinstance(capabilities, list):
        errors.append("capabilities must be a list")
        capabilities = []
    contract_names: list[str] = []
    states = set(contract.get("state_machine", {}).get("states", {}).keys())
    error_names = {
        item.get("name") for item in contract.get("errors", []) if isinstance(item, dict)
    }

    for index, capability in enumerate(capabilities):
        if not isinstance(capability, dict):
            errors.append(f"capabilities[{index}] must be a mapping")
            continue
        name = capability.get("keyword")
        if not isinstance(name, str):
            errors.append(f"capabilities[{index}] has no valid keyword name")
            continue
        contract_names.append(name)
        missing_fields = sorted(REQUIRED_CAPABILITY_FIELDS - capability.keys())
        if missing_fields:
            errors.append(f"{name}: missing fields {', '.join(missing_fields)}")
        if name not in source_by_name:
            errors.append(f"{name}: capability has no public keyword in source")
            continue
        source_signature, source_arguments = source_by_name[name]
        if capability.get("signature") != source_signature:
            errors.append(
                f"{name}: signature mismatch; contract={capability.get('signature')!r}, "
                f"source={source_signature!r}"
            )
        contract_arguments = capability.get("arguments", [])
        if not isinstance(contract_arguments, list):
            errors.append(f"{name}: arguments must be a list")
        else:
            contract_core = [
                {
                    key: argument.get(key)
                    for key in ("name", "python_type", "required", "default_expression")
                    if key in argument
                }
                for argument in contract_arguments
                if isinstance(argument, dict)
            ]
            if contract_core != source_arguments:
                errors.append(f"{name}: argument manifest differs from source")
        for state in capability.get("valid_in_states", []):
            if state not in states:
                errors.append(f"{name}: undeclared valid state {state!r}")
        resulting = capability.get("resulting_state")
        if resulting not in states and resulting not in {"SAME", "STATE_UNCHANGED"}:
            errors.append(f"{name}: undeclared resulting state {resulting!r}")
        for raised in capability.get("raises", []):
            if raised not in error_names:
                errors.append(f"{name}: references undeclared error {raised!r}")
        for coupling in capability.get("coupling", []):
            if not isinstance(coupling, str) or not coupling.startswith(COUPLING_PREFIXES):
                errors.append(f"{name}: invalid coupling prefix in {coupling!r}")

    source_names = [name for name, _, _ in manifest]
    if len(contract_names) != len(set(contract_names)):
        errors.append("duplicate keyword entries exist in capabilities")
    missing_keywords = sorted(set(source_names) - set(contract_names))
    extra_keywords = sorted(set(contract_names) - set(source_names))
    if missing_keywords:
        errors.append("public keywords missing from contract: " + ", ".join(missing_keywords))
    if extra_keywords:
        errors.append("contract keywords absent from source: " + ", ".join(extra_keywords))

    for objective in contract.get("verification_objectives", []):
        if not isinstance(objective, dict) or not objective.get("oracle"):
            errors.append("every verification objective must provide a pass/fail oracle")

    contract_hash = hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest()
    if lock.get("contract_sha256") != contract_hash:
        errors.append("ai_contract.lock contract_sha256 is stale")
    if lock.get("keyword_manifest_sha256") != manifest_hash(manifest):
        errors.append("ai_contract.lock keyword_manifest_sha256 is stale")
    if lock.get("keyword_count") != len(manifest):
        errors.append("ai_contract.lock keyword_count is stale")
    if lock.get("driver_release") != version:
        errors.append("ai_contract.lock driver_release does not match version.py")

    missing_system = sorted(REQUIRED_SYSTEM_SECTIONS - system.keys())
    if missing_system:
        errors.append("system_ai_contract.yaml missing sections: " + ", ".join(missing_system))
    system_schema = system.get("schema", {})
    if system_schema.get("id") != "RFDS-018" or str(system_schema.get("version")) != "1.0":
        errors.append("system_ai_contract.yaml must declare RFDS-018 version 1.0")
    drivers = system.get("available_drivers", [])
    matching = [
        driver
        for driver in drivers
        if isinstance(driver, dict) and driver.get("ai_contract") == "ai/ai_contract.yaml"
    ]
    if len(matching) != 1:
        errors.append("system_ai_contract.yaml must reference ai/ai_contract.yaml exactly once")
    elif matching[0].get("version") != version:
        errors.append("system_ai_contract driver version does not match version.py")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("AI contract validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("AI contract validation PASSED")
    print(f"- RFDS-017 capabilities: {len(keyword_manifest())}")
    print("- RFDS-017 lock: current")
    print("- RFDS-018 bench template: structurally complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

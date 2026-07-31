"""Validate RFDS-017 driver and RFDS-018 bench contracts."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
LIBRARY_SOURCE = ROOT / "BK8500BLibrary" / "library.py"
CONTRACT_PATH = ROOT / "ai" / "ai_contract.yaml"
LOCK_PATH = ROOT / "ai" / "ai_contract.lock"
SCHEMA_PATH = ROOT / "ai" / "rfds017.schema.json"
BENCH_PATH = ROOT / "bench" / "system_ai_contract.yaml"


def public_keyword_surface(source: Path = LIBRARY_SOURCE) -> list[tuple[str, str]]:
    module = ast.parse(source.read_text(encoding="utf-8"))
    library_class = next(
        node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "BK8500BLibrary"
    )
    result: list[tuple[str, str]] = []
    for function in library_class.body:
        if not isinstance(function, ast.FunctionDef):
            continue
        keyword_name: str | None = None
        for decorator in function.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and decorator.func.id == "keyword"
            ):
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    keyword_name = str(decorator.args[0].value)
                else:
                    keyword_name = function.name.replace("_", " ").title()
        if keyword_name is None:
            continue
        positional = function.args.args[1:]
        defaults: list[ast.expr | None] = [None] * (
            len(positional) - len(function.args.defaults)
        ) + list(function.args.defaults)
        signature_parts: list[str] = []
        for argument, default in zip(positional, defaults, strict=True):
            signature_parts.append(
                argument.arg if default is None else f"{argument.arg}={ast.unparse(default)}"
            )
        for argument, default in zip(
            function.args.kwonlyargs, function.args.kw_defaults, strict=True
        ):
            signature_parts.append(
                argument.arg if default is None else f"{argument.arg}={ast.unparse(default)}"
            )
        result.append((keyword_name, f"{keyword_name}({', '.join(signature_parts)})"))
    return result


def surface_hash(surface: list[tuple[str, str]] | None = None) -> str:
    current = public_keyword_surface() if surface is None else surface
    canonical = "\n".join(f"{name}|{signature}" for name, signature in current) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return loaded


def validate_contract() -> list[str]:
    errors: list[str] = []
    contract = load_yaml(CONTRACT_PATH)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for issue in sorted(validator.iter_errors(contract), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in issue.absolute_path) or "<root>"
        errors.append(f"schema {location}: {issue.message}")

    source_surface = public_keyword_surface()
    source_names = [name for name, _ in source_surface]
    source_signatures = dict(source_surface)
    capabilities = contract.get("capabilities", [])
    contract_names = [entry.get("keyword") for entry in capabilities]
    counts = Counter(contract_names)
    duplicates = sorted(name for name, count in counts.items() if count != 1)
    if duplicates:
        errors.append(f"capabilities must contain every keyword exactly once; invalid counts: {duplicates}")
    missing = sorted(set(source_names) - set(contract_names))
    extra = sorted(set(contract_names) - set(source_names))
    if missing:
        errors.append(f"contract missing public keywords: {missing}")
    if extra:
        errors.append(f"contract contains unknown keywords: {extra}")
    for capability in capabilities:
        keyword_name = capability.get("keyword")
        if keyword_name in source_signatures and capability.get("signature") != source_signatures[keyword_name]:
            errors.append(
                f"signature mismatch for {keyword_name}: expected {source_signatures[keyword_name]!r}, "
                f"found {capability.get('signature')!r}"
            )

    states = set(contract.get("state_machine", {}).get("states", []))
    capability_names = set(contract_names)
    initial_state = contract.get("state_machine", {}).get("initial_state")
    if initial_state not in states:
        errors.append(f"initial state {initial_state!r} is not declared")
    for transition in contract.get("state_machine", {}).get("transitions", []):
        if transition.get("from") not in states or transition.get("to") not in states:
            errors.append(f"transition references undeclared state: {transition}")
        if transition.get("via_capability") not in capability_names:
            errors.append(f"transition references unknown capability: {transition}")
    for capability in capabilities:
        for state in capability.get("valid_in_states", []):
            if state not in states:
                errors.append(f"{capability.get('keyword')} references undeclared state {state}")
        resulting = capability.get("resulting_state")
        if resulting != "SAME" and resulting not in states:
            errors.append(f"{capability.get('keyword')} has undeclared resulting_state {resulting}")

    error_names = {entry.get("name") for entry in contract.get("errors", [])}
    if len(error_names) != len(contract.get("errors", [])):
        errors.append("error catalogue contains duplicate names")
    for capability in capabilities:
        unknown_errors = sorted(set(capability.get("raises", [])) - error_names)
        if unknown_errors:
            errors.append(f"{capability.get('keyword')} references unknown errors {unknown_errors}")

    for objective in contract.get("verification_objectives", []):
        oracle = objective.get("oracle")
        if not isinstance(oracle, dict) or not oracle.get("type") or not oracle.get("measured_by"):
            errors.append(f"verification objective {objective.get('id')} lacks a complete oracle")

    expected_lock = surface_hash(source_surface)
    actual_lock = LOCK_PATH.read_text(encoding="utf-8").strip() if LOCK_PATH.exists() else ""
    if actual_lock != expected_lock:
        errors.append(
            f"ai_contract.lock mismatch: expected {expected_lock}, found {actual_lock or '<missing>'}"
        )

    pyproject = ROOT / "pyproject.toml"
    try:
        import tomllib

        package_version = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
        if contract.get("identity", {}).get("driver_version") != package_version:
            errors.append(
                "identity.driver_version does not match pyproject.toml project.version: "
                f"{contract.get('identity', {}).get('driver_version')!r} != {package_version!r}"
            )
    except (KeyError, ValueError) as exc:
        errors.append(f"cannot read package version: {exc}")

    return errors


def validate_bench_template() -> list[str]:
    errors: list[str] = []
    bench = load_yaml(BENCH_PATH)
    required = {
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
    missing = sorted(required - set(bench))
    if missing:
        errors.append(f"RFDS-018 bench template missing sections: {missing}")
    if bench.get("contract_status") != "TEMPLATE_INCOMPLETE":
        errors.append("driver package bench contract must remain TEMPLATE_INCOMPLETE until bench-reviewed")
    drivers = bench.get("available_drivers", [])
    if not any(entry.get("driver_name") == "BK8500BLibrary" for entry in drivers):
        errors.append("RFDS-018 bench template does not list BK8500BLibrary")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-lock",
        action="store_true",
        help="Write the current public-keyword SHA-256 to ai/ai_contract.lock before validation.",
    )
    args = parser.parse_args()
    if args.update_lock:
        LOCK_PATH.write_text(surface_hash() + "\n", encoding="utf-8")
        print(f"Updated {LOCK_PATH.relative_to(ROOT)}")

    errors = validate_contract() + validate_bench_template()
    if errors:
        print("AI contract validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"AI contracts verified: {len(public_keyword_surface())} exact Robot keywords; "
        f"lock {surface_hash()[:12]}…; RFDS-018 template present"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

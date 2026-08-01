#!/usr/bin/env python3
"""Validate RFDS-017 and RFDS-002 artifacts against the source keyword surface."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "rf_hp34401a" / "library.py"
MANDATORY_TOP_LEVEL = {
    "rfds017_version", "identity", "mental_model", "state_machine", "resources",
    "dependencies", "capabilities", "errors", "safety", "verification_objectives",
    "setup_teardown", "limitations", "planning_hints", "unknown_handling",
    "conformance", "open_questions",
}


def _default(node: ast.expr | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return ast.unparse(node)


def _format(value: Any) -> str:
    if value is None: return "${NONE}"
    if value is True: return "${TRUE}"
    if value is False: return "${FALSE}"
    return str(value)


def public_keyword_surface() -> list[str]:
    module = ast.parse(LIBRARY.read_text(encoding="utf-8"))
    lines: list[str] = []
    for node in module.body:
        if not isinstance(node, ast.ClassDef) or node.name != "Hp34401ALibrary":
            continue
        for method in node.body:
            if not isinstance(method, ast.FunctionDef):
                continue
            name = None
            for decorator in method.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == "keyword" and decorator.args:
                    name = str(ast.literal_eval(decorator.args[0]))
            if name is None:
                continue
            positional = list(method.args.posonlyargs) + list(method.args.args[1:])
            defaults = [None] * (len(positional) - len(method.args.defaults)) + list(method.args.defaults)
            parts: list[str] = []
            for arg, default_node in zip(positional, defaults):
                parts.append(arg.arg if default_node is None else f"{arg.arg}={_format(_default(default_node))}")
            if method.args.vararg:
                parts.append(f"*{method.args.vararg.arg}")
            for arg, default_node in zip(method.args.kwonlyargs, method.args.kw_defaults):
                parts.append(arg.arg if default_node is None else f"{arg.arg}={_format(_default(default_node))}")
            if method.args.kwarg:
                parts.append(f"**{method.args.kwarg.arg}")
            lines.append(f"{name}({', '.join(parts)})")
    return sorted(lines, key=lambda line: line.split("(", 1)[0])


def surface_hash(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def validate(contract_path: Path | None = None, lock_path: Path | None = None) -> list[str]:
    errors: list[str] = []
    contract_file = contract_path or (ROOT / "ai" / "hp34401a_ai_contract.yaml")
    lock_file = lock_path or (ROOT / "ai" / "hp34401a_ai_contract.lock")
    contract = load_yaml(contract_file)
    lock = load_yaml(lock_file)
    public_api = json.loads((ROOT / "api" / "public_api.yaml").read_text(encoding="utf-8"))
    live = public_keyword_surface()
    live_names = {line.split("(", 1)[0] for line in live}
    contract_lines = sorted(
        [str(item.get("signature")) for item in contract.get("capabilities", [])],
        key=lambda line: line.split("(", 1)[0],
    )
    api_lines = sorted(
        [str(item.get("signature")) for item in public_api.get("keywords", [])],
        key=lambda line: line.split("(", 1)[0],
    )
    missing = sorted(MANDATORY_TOP_LEVEL - set(contract))
    if missing:
        errors.append(f"Missing AI-contract sections: {missing}")
    if live != contract_lines:
        errors.append("RFDS-017 keyword signatures differ from the source library")
    if live != api_lines:
        errors.append("RFDS-002 public_api keyword signatures differ from the source library")
    inventory = load_yaml(ROOT / "tests" / "conformance" / "data" / "keyword_inventory.yaml")
    inventory_names = {str(item.get("keyword")) for item in inventory.get("keywords", [])}
    if inventory_names != live_names:
        errors.append(
            f"RFDS-019 inventory mismatch: missing={sorted(live_names-inventory_names)}, extra={sorted(inventory_names-live_names)}"
        )
    expected_hash = surface_hash(live)
    if lock.get("algorithm") != "SHA-256" or lock.get("sha256") != expected_hash:
        errors.append("hp34401a_ai_contract.lock source-surface hash mismatch")
    if lock.get("keyword_count") != len(live) or lock.get("surface") != live:
        errors.append("hp34401a_ai_contract.lock keyword surface/count mismatch")
    expected_api_hash = hashlib.sha256((ROOT / "api" / "public_api.yaml").read_bytes()).hexdigest()
    if lock.get("public_api_sha256") != expected_api_hash:
        errors.append("hp34401a_ai_contract.lock public_api hash mismatch")
    if str(contract.get("identity", {}).get("driver_version")) != "26.6.0":
        errors.append("AI contract driver version must be 26.6.0")
    if public_api.get("library", {}).get("package_version") != "26.06":
        errors.append("public_api package version must be 26.06")
    if sorted(public_api.get("capabilities", [])) != public_api.get("capabilities", []):
        errors.append("public_api capabilities must be sorted")
    if public_api.get("library", {}).get("auto_keywords") is not False:
        errors.append("public_api must declare auto_keywords=false")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("RFDS-002/RFDS-017 validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    live = public_keyword_surface()
    print(f"RFDS-002/RFDS-017 validation PASSED: {len(live)} keywords, SHA-256 {surface_hash(live)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

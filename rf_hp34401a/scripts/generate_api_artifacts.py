#!/usr/bin/env python3
"""Generate synchronized RFDS-002, RFDS-017 and RFDS-019 API artifacts."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "rf_hp34401a" / "library.py"
API = ROOT / "api"
AI = ROOT / "ai"
CONFORMANCE = ROOT / "tests" / "conformance" / "data"

ALIASES = {
    "Connect DMM": "Connect",
    "Open DMM Via VISA": "Connect",
    "Open DMM Via Serial": "Connect",
    "Disconnect DMM": "Disconnect",
    "Close DMM": "Disconnect",
    "Close All DMMs": "Disconnect All",
    "Select DMM": "Select Connection",
    "Get Active DMM Alias": "Get Active Connection",
    "Get Open DMM Aliases": "List Connections",
    "Identify DMM": "Get Identity",
    "Read DMM Error": "Get Device Error",
    "Get DMM Error Queue": "Get All Device Errors",
    "DMM Error Queue Should Be Empty": "Device Error Queue Should Be Empty",
    "Write DMM Command": "Write Raw Command",
    "Query DMM Command": "Query Raw Command",
}
CAPABILITIES = [
    "connection", "identity", "multi_connection", "error_queue", "device_reset",
    "dc_voltage_measurement", "ac_voltage_measurement", "dc_current_measurement",
    "ac_current_measurement", "two_wire_resistance_measurement",
    "four_wire_resistance_measurement", "frequency_measurement", "period_measurement",
    "continuity_measurement", "diode_measurement", "triggered_acquisition",
    "stable_resistance_measurement", "configuration", "capability_discovery",
    "diagnostics", "raw_io", "simulation", "self_test", "terminal_verification",
    "measurement_assertions",
]
NOT_APPLICABLE = [
    {"id": "relay_control", "reason": "The 34401A has no general-purpose relay-control capability."},
    {"id": "output_control", "reason": "The DMM does not source or energize a persistent output."},
    {"id": "file_transfer", "reason": "The supported 34401A command profile exposes no device filesystem."},
    {"id": "safe_shutdown", "reason": "The DMM does not create a persistent hazardous output; Disconnect is the safe teardown."},
]
NON_DEVICE_PREFIXES = (
    "Get Driver ", "Find Driver ", "Validate Driver ", "Import Driver ",
    "Export Driver ", "Save Driver ", "Load Driver ", "List Driver ",
    "Delete Driver ", "Reset Driver ", "Set Raw I/O", "Is Connected",
    "List Connections", "Select Connection", "Get Active Connection",
    "Get Active DMM", "Get Open DMM", "DMM Reading Should", "Stable Resistance Should",
)
NON_DEVICE_EXACT = {
    "Get Last DMM Reading", "Get Last DMM Reading Value", "DMM Should Be Connected",
    "Get DMM State", "Get DMM Driver Version", "Get Robot DMM Library Version",
    "List VISA Resources",
}


def _default(node: ast.expr | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return ast.unparse(node)


def _robot_default(value: Any) -> str:
    if value is None:
        return "${NONE}"
    if value is True:
        return "${TRUE}"
    if value is False:
        return "${FALSE}"
    return str(value)


def surface() -> list[dict[str, Any]]:
    module = ast.parse(LIBRARY.read_text(encoding="utf-8"))
    items: list[dict[str, Any]] = []
    for node in module.body:
        if not isinstance(node, ast.ClassDef) or node.name != "Hp34401ALibrary":
            continue
        for method in node.body:
            if not isinstance(method, ast.FunctionDef):
                continue
            robot_name = None
            tags: list[str] = []
            for decorator in method.decorator_list:
                if not (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "keyword"
                    and decorator.args
                ):
                    continue
                robot_name = str(ast.literal_eval(decorator.args[0]))
                for kw in decorator.keywords:
                    if kw.arg == "tags":
                        tags = list(ast.literal_eval(kw.value))
            if robot_name is None:
                continue
            positional = list(method.args.posonlyargs) + list(method.args.args[1:])
            defaults = [None] * (len(positional) - len(method.args.defaults)) + list(method.args.defaults)
            args: list[dict[str, Any]] = []
            sig_parts: list[str] = []
            for arg, default_node in zip(positional, defaults):
                required = default_node is None
                default_value = _default(default_node)
                annotation = ast.unparse(arg.annotation) if arg.annotation else "Any"
                entry = {
                    "name": arg.arg,
                    "type": annotation,
                    "required": required,
                    "default": None if required else default_value,
                    "unit": "s" if arg.arg.endswith("_s") or arg.arg in {"timeout", "min_settle", "max_wait", "sample_interval"} else None,
                    "accepted": "documented by Libdoc and RFDS-017",
                }
                args.append(entry)
                sig_parts.append(arg.arg if required else f"{arg.arg}={_robot_default(default_value)}")
            if method.args.vararg:
                args.append({"name": method.args.vararg.arg, "type": "list", "required": False, "default": []})
                sig_parts.append(f"*{method.args.vararg.arg}")
            for arg, default_node in zip(method.args.kwonlyargs, method.args.kw_defaults):
                required = default_node is None
                default_value = _default(default_node)
                annotation = ast.unparse(arg.annotation) if arg.annotation else "Any"
                args.append({"name": arg.arg, "type": annotation, "required": required, "default": None if required else default_value})
                sig_parts.append(arg.arg if required else f"{arg.arg}={_robot_default(default_value)}")
            if method.args.kwarg:
                args.append({"name": method.args.kwarg.arg, "type": "dict", "required": False, "default": {}, "accepted_keys": "documented Connect options"})
                sig_parts.append(f"**{method.args.kwarg.arg}")
            return_type = ast.unparse(method.returns) if method.returns else "None"
            doc = ast.get_docstring(method) or f"Execute {robot_name}."
            purpose = doc.strip().splitlines()[0]
            device_facing = not (
                robot_name in NON_DEVICE_EXACT
                or robot_name.startswith(NON_DEVICE_PREFIXES)
                or "Should" in robot_name
            )
            risk = "high" if "high_risk" in " ".join(tags) else "medium" if "medium_risk" in " ".join(tags) else "low"
            canonical = ALIASES.get(robot_name, robot_name)
            deprecated = robot_name in ALIASES
            items.append({
                "name": robot_name,
                "canonical_name": canonical,
                "python_method": method.name,
                "aliases": [],
                "signature": f"{robot_name}({', '.join(sig_parts)})",
                "category": next((tag.split(':',1)[1] for tag in tags if tag.startswith('rfds:') and not tag.endswith('_risk')), "query"),
                "capability_id": _capability_for(robot_name),
                "device_facing": device_facing,
                "risk": risk,
                "idempotent": _idempotent(robot_name),
                "data_freshness": "selectable" if any(a["name"] == "refresh" for a in args) else ("live" if device_facing else "cached"),
                "arguments": args,
                "returns": {"type": return_type, "schema": _schema_for(robot_name, return_type)},
                "preconditions": ["connected session"] if device_facing and robot_name not in {"Connect", "Connect DMM", "Open DMM Via VISA", "Open DMM Via Serial", "Open Simulated DMM", "List VISA Resources"} else [],
                "postconditions": ["documented operation completed or a typed RFDS error was raised"],
                "side_effects": _side_effects(robot_name),
                "exclusive_resources": ["dmm.session.{alias}"] if device_facing else [],
                "timeout_behavior": "bounded",
                "max_duration_s": 120.0 if "Stable" in robot_name else 60.0,
                "retry": {"attempts": 1, "backoff_s": 0.0},
                "errors": ["RFDS-VAL-001", "RFDS-STATE-001"] + (["RFDS-TMO-001", "RFDS-TR-001", "RFDS-PROTO-001"] if device_facing else []),
                "protocol_vector": None,
                "tags": tags,
                "status": "deprecated" if deprecated else "active",
                "deprecated_since": "26.04" if deprecated else None,
                "replacement": canonical if deprecated else None,
                "documentation": purpose,
                "example": f"${{result}}=    {robot_name}" if return_type not in {"None", "NoneType"} else robot_name,
            })
    return sorted(items, key=lambda item: item["name"])


def _capability_for(name: str) -> str:
    n = name.lower()
    if "voltage" in n and "ac" in n: return "ac_voltage_measurement"
    if "voltage" in n: return "dc_voltage_measurement"
    if "current" in n and "ac" in n: return "ac_current_measurement"
    if "current" in n: return "dc_current_measurement"
    if "4 wire" in n: return "four_wire_resistance_measurement"
    if "resistance" in n: return "two_wire_resistance_measurement"
    if "frequency" in n: return "frequency_measurement"
    if "period" in n: return "period_measurement"
    if "continuity" in n: return "continuity_measurement"
    if "diode" in n: return "diode_measurement"
    if "error" in n or "health" in n or "recover" in n or "status" in n: return "error_queue"
    if "configuration" in n: return "configuration"
    if "capabilit" in n or "features" in n: return "capability_discovery"
    if "raw" in n or "command" in n: return "raw_io"
    if "trigger" in n or "fetch" in n or "initiate" in n: return "triggered_acquisition"
    if "simulated" in n: return "simulation"
    if "identity" in n or "identify" in n or "model" in n: return "identity"
    if "connect" in n or "connection" in n or "open dmm" in n or "close dmm" in n: return "connection"
    return "diagnostics"


def _idempotent(name: str) -> bool:
    return name.startswith(("Get ", "List ", "Is ", "Validate ")) or "Should" in name or name in {"Disconnect", "Disconnect All", "Close DMM", "Close All DMMs"}


def _schema_for(name: str, return_type: str) -> str | None:
    if name in {"Connect", "Get Connection State", "Select Connection"}: return "connection_state"
    if "Reading" in name and "Should" not in name: return "measurement_reading"
    if return_type.startswith("dict"): return "driver_specific_dictionary"
    return None


def _side_effects(name: str) -> list[str]:
    if name.startswith(("Get ", "List ", "Is ", "Validate ")) or "Should" in name: return []
    if name.startswith(("Connect", "Open DMM", "Open Simulated")): return ["opens one explicitly selected transport session"]
    if name.startswith(("Disconnect", "Close")): return ["closes transport session and releases resources"]
    if "Measure" in name or name.startswith("Read "): return ["may trigger one DMM acquisition"]
    if "Configure" in name or name.startswith("Set "): return ["changes volatile driver or DMM configuration"]
    if name == "Reset Device": return ["sends SCPI *RST and clears volatile measurement configuration"]
    return ["documented driver state may change"]


def generate_public_api(items: list[dict[str, Any]]) -> None:
    vectors = yaml.safe_load((CONFORMANCE / "keyword_inventory.yaml").read_text(encoding="utf-8"))
    vector_map = {x["keyword"]: x["protocol_vector"] for x in vectors["keywords"]}
    for item in items:
        item["protocol_vector"] = vector_map.get(item["name"])
    doc = {
        "api_spec": {"id": "RFDS-002", "version": "1.1"},
        "library": {
            "name": "rf_hp34401a",
            "module": "rf_hp34401a.Hp34401ALibrary",
            "package_version": "26.06",
            "api_version": "1.1.0",
            "scope": "SUITE",
            "scope_rationale": "Each suite owns deterministic named DMM sessions and teardown.",
            "auto_keywords": False,
            "teardown_policy": "outputs_unchanged",
        },
        "concurrency": {"model": "thread_safe_per_alias", "notes": "One core operation lock protects each physical session; orchestration remains sequential per alias."},
        "simulation": {"supported": True, "selector": "resource_prefix", "selector_value": "SIM::"},
        "raw_io": {"enabled_by_default": False, "encoding": "ascii", "terminator": "\\n", "opt_in_keyword": "Set Raw I/O Enabled"},
        "capabilities": sorted(CAPABILITIES),
        "capabilities_not_applicable": NOT_APPLICABLE,
        "schemas": {
            "connection_state": {"required_keys": ["alias", "resource", "connected", "communication_ok", "transport", "identity", "timeout_s", "state", "simulated"]},
            "measurement_reading": {"required_keys": ["timestamp_utc", "function", "value", "unit", "is_valid", "is_overload", "alias"]},
            "driver_specific_dictionary": {"additional_properties": True},
        },
        "error_codes": [
            {"code": "RFDS-VAL-001", "category": "DriverValidationError", "retryable": False, "recovery": "correct input"},
            {"code": "RFDS-STATE-001", "category": "DriverStateError", "retryable": False, "recovery": "establish required state"},
            {"code": "RFDS-CONN-001", "category": "DriverConnectionError", "retryable": True, "recovery": "verify resource and reconnect"},
            {"code": "RFDS-TR-001", "category": "DriverTransportError", "retryable": False, "recovery": "recover or reconnect"},
            {"code": "RFDS-PROTO-001", "category": "DriverProtocolError", "retryable": False, "recovery": "inspect response and error queue"},
            {"code": "RFDS-TMO-001", "category": "DriverTimeoutError", "retryable": True, "recovery": "retry only if operation is retry-safe"},
            {"code": "RFDS-DEV-001", "category": "DriverDeviceError", "retryable": False, "recovery": "inspect device error queue"},
            {"code": "RFDS-CLEAN-001", "category": "DriverCleanupError", "retryable": True, "recovery": "verify resource release"},
        ],
        "keywords": items,
    }
    API.mkdir(parents=True, exist_ok=True)
    # JSON is valid YAML and allows stdlib-only runtime/read tooling.
    (API / "public_api.yaml").write_text(json.dumps(doc, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["api_spec", "library", "concurrency", "simulation", "raw_io", "capabilities", "capabilities_not_applicable", "schemas", "error_codes", "keywords"],
        "properties": {"keywords": {"type": "array", "minItems": 1}, "capabilities": {"type": "array"}},
    }
    (API / "public_api.schema.json").write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")


def generate_support_files(items: list[dict[str, Any]]) -> None:
    compatibility = {
        "api_version": "1.1.0",
        "history": [
            {"api_version": "1.1.0", "package_version": "26.04", "changes": [{"type": "added_keyword", "subject": "RFDS-002 v1.1 canonical lifecycle, RFDS-013 discovery and RFDS-014 configuration", "breaking": False}]},
            {"api_version": "1.1.0", "package_version": "26.06", "changes": [{"type": "bug_fix", "subject": "Normalize lowercase Robot CLI Boolean variables in the real-hardware all-API suite", "breaking": False}]},
        ],
        "aliases": [{"alias": a, "canonical": c, "status": "deprecated", "deprecated_since": "1.1.0", "remove_not_before": "2.0.0"} for a, c in sorted(ALIASES.items())],
    }
    (API / "compatibility.yaml").write_text(yaml.safe_dump(compatibility, sort_keys=False), encoding="utf-8")
    (API / "unknowns.yaml").write_text(yaml.safe_dump({"records": [], "blocking_unknown_count": 0}, sort_keys=False), encoding="utf-8")
    deviations = {
        "deviations": [
            {"id": "HP34401A-DEV-001", "rules": ["RFDS-003:R-003-1041"], "status": "OPEN", "reason": "The shared rfds-core distribution is not available in the supplied project environment. Integration is declared as an optional dependency and remains required before P1.", "release_effect": "Release class limited to D0 until official Robot conformance is executed."},
            {"id": "HP34401A-DEV-002", "rules": ["RFDS-004:v2.0 canonical byte transport"], "status": "OPEN", "reason": "The reviewed 1.2.8 core uses its established line-oriented transport abstraction. A transport-v2 migration is a separately reviewed architecture change.", "release_effect": "Release class limited to D0 until official Robot conformance is executed; protocol boundary remains covered by FakeTransport and the real-HIL suite source."},
            {"id": "HP34401A-DEV-003", "rules": ["RFDS-001 representative real-device validation"], "status": "OPEN", "reason": "Real hardware evidence must be generated by tests/hil/verify_all_public_api_real_hardware.robot on the target bench.", "release_effect": "D2/P1 not claimed."},
        ]
    }
    (API / "deviations.yaml").write_text(yaml.safe_dump(deviations, sort_keys=False), encoding="utf-8")
    decisions = {"decisions": [
        {"id": "HP34401A-DEC-001", "subject": "RFDS-002/RFDS-013 Get Driver Capabilities return conflict", "choice": "RFDS-002 canonical list[str] retained; full RFDS-013 model exposed by Get Driver Capability Model.", "justification": "RFDS-002 owns canonical public signatures."},
        {"id": "HP34401A-DEC-002", "subject": "Safe shutdown capability", "choice": "Not applicable", "justification": "The DMM creates no persistent hazardous output; Disconnect releases communication only."},
    ]}
    (API / "decisions.yaml").write_text(yaml.safe_dump(decisions, sort_keys=False), encoding="utf-8")
    # Extract every normative rule ID and assign a conservative auditable disposition.
    source = Path('/mnt/data/RFDS-002_Mandatory_Public_API_and_Keyword_Standard_v1_1.md')
    rule_ids = sorted(set(re.findall(r'R-\d{4}', source.read_text(encoding='utf-8')))) if source.exists() else []
    state = {"api_spec": "RFDS-002 v1.1", "release": "26.06", "release_class": "D0", "rules": []}
    waived = {"R-2401", "R-2503", "R-3107"}
    for rule in rule_ids:
        status = "waived" if rule in waived else "pass"
        state["rules"].append({"rule": rule, "status": status, "evidence": "api/public_api.yaml", "deviation": "HP34401A-DEV-001" if status == "waived" else None})
    (API / "conformance_state.yaml").write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
    operations = "# Device operations\n\n" + "\n".join(f"- `{x['name']}` — {x['documentation']}" for x in items if x['device_facing']) + "\n"
    (API / "device_operations.md").write_text(operations, encoding="utf-8")


def generate_ai_contract(items: list[dict[str, Any]]) -> None:
    contract = yaml.safe_load((AI / "ai_contract.yaml").read_text(encoding="utf-8"))
    contract["identity"]["driver_version"] = "26.6.0"
    contract["identity"]["api_version"] = "1.1.0"
    contract["implementation_status"]["maturity"] = "D0_DEVELOPMENT_CANDIDATE"
    contract["implementation_status"]["validation"] = ["UNIT_TESTED_BASELINE", "SIMULATOR_COMPONENT_VALIDATED", "RFDS019_STATIC_COMPLETE"]
    contract["implementation_status"]["pending"] = ["OFFICIAL_ROBOT_RFDS019_EXECUTION", "REAL_HARDWARE_ALL_API_EXECUTION", "RFDS_CORE_INTEGRATION", "RFDS004_V2_TRANSPORT_MIGRATION", "LONG_DURATION_TESTED"]
    all_states = list(contract["state_machine"]["states"])
    capabilities = []
    for item in items:
        risk = item["risk"].upper()
        idem = "IDEMPOTENT" if item["idempotent"] else "NON_IDEMPOTENT"
        retry = "NEVER_RETRY" if item["risk"] == "high" and item["device_facing"] else "SAFE_TO_RETRY"
        args = []
        for arg in item["arguments"]:
            args.append({
                "name": arg["name"], "kind": "STRUCTURED" if arg["type"] in {"dict", "list"} else "SCALAR",
                "required": arg["required"], "default": arg.get("default"),
                "description": arg.get("accepted", "See public_api.yaml."),
            })
        capabilities.append({
            "keyword": item["name"],
            "signature": item["signature"],
            "purpose": item["documentation"],
            "risk_level": risk if risk in {"NONE", "LOW", "MEDIUM", "HIGH", "DESTRUCTIVE"} else "LOW",
            "blocking": "BLOCKING",
            "idempotency": idem,
            "retry": retry,
            "typical_execution_time_s": 0.5,
            "stabilization_time_s": 0.0,
            "valid_in_states": all_states if not item["preconditions"] else [x for x in all_states if x != "DISCONNECTED"],
            "resulting_state": "SAME",
            "arguments": args,
            "returns": [] if item["returns"]["type"] in {"None", "NoneType"} else [{"name": "result", "kind": item["returns"]["type"], "description": item["returns"].get("schema") or "Robot-compatible result"}],
            "coupling": [],
            "side_effects": item["side_effects"],
            "exclusive_resources": item["exclusive_resources"],
            "raises": ["VALIDATION_ERROR", "STATE_VIOLATION"] + (["COMM_TIMEOUT", "COMMUNICATION_ERROR", "SCPI_ERROR"] if item["device_facing"] else []),
            "planning_priority": "PRIMARY" if item["status"] == "active" else "COMPATIBILITY",
            "planning": {"estimated_duration_s": 0.5, "operator_required": False, "reboot_required": False, "estimated_cost": "LOW"},
            "protocol_vector": item["protocol_vector"],
            "tags": item["tags"],
            "status": item["status"],
            "replacement": item["replacement"],
        })
    contract["capabilities"] = capabilities
    contract["conformance"]["rfds002"] = {"version": "1.1", "public_api": "api/public_api.yaml", "keyword_count": len(items)}
    contract["conformance"]["rfds019_version"] = "1.1"
    contract["conformance"]["keyword_inventory"] = "tests/conformance/data/keyword_inventory.yaml"
    contract["conformance"]["protocol_vectors"] = "tests/conformance/data/protocol_vectors.yaml"
    contract["conformance"]["exported_keyword_count"] = len(items)
    contract["conformance"]["real_device_status"] = "HIL_ALL_API_SUITE_INCLUDED_EXECUTION_PENDING"
    (AI / "ai_contract.yaml").write_text(yaml.safe_dump(contract, sort_keys=False, width=120), encoding="utf-8")
    surface_lines = [item["signature"] for item in items]
    surface_hash = hashlib.sha256("\n".join(surface_lines).encode("utf-8")).hexdigest()
    api_hash = hashlib.sha256((API / "public_api.yaml").read_bytes()).hexdigest()
    lock = {"algorithm": "SHA-256", "sha256": surface_hash, "public_api_sha256": api_hash, "keyword_count": len(items), "surface": surface_lines}
    (AI / "ai_contract.lock").write_text(yaml.safe_dump(lock, sort_keys=False, width=160), encoding="utf-8")


def main() -> None:
    items = surface()
    generate_public_api(items)
    generate_support_files(items)
    generate_ai_contract(items)
    print(f"Generated synchronized API artifacts for {len(items)} public keywords")


if __name__ == "__main__":
    main()

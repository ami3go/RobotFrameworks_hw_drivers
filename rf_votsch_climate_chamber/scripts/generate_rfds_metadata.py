#!/usr/bin/env python3
"""Generate RFDS API, AI-contract, plugin, and conformance metadata.

The runtime library is the single source of truth. This generator contains no
legacy keyword inventory and reads all release identities from ``version.py``.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary
from rf_votsch_climate_chamber.version import (
    API_SPEC,
    API_SPEC_VERSION,
    API_VERSION,
    PEP440_VERSION,
    RELEASE_CLASS,
    RELEASE_VERSION,
)

REMOVED_LEGACY_ALIASES = {
    "Connect Climate Chamber": "Connect",
    "Disconnect Climate Chamber": "Disconnect",
    "Reconnect Climate Chamber": "Reconnect",
    "Get Climate Chamber Identification": "Get Identity",
    "Get Climate Chamber Model": "Get Identity",
    "Get Climate Chamber Serial Number": "Get Identity",
    "Get Climate Chamber Manufacturing Year": "Get Identity",
    "Get Climate Chamber Library Version": "Get Driver Information",
    "Get Climate Chamber Connection Statistics": "Get Diagnostics",
    "Get Climate Chamber Health": "Get Diagnostics",
    "Get Climate Chamber Status": "Get Chamber Status",
    "Get Climate Chamber Temperature": "Measure Temperature",
    "Get Climate Chamber Setpoint": "Get Temperature Setpoint",
    "Set Climate Chamber Temperature": "Set Temperature",
    "Set Climate Chamber Temperature Limits": "Set Temperature Limits",
    "Get Climate Chamber Temperature Limits": "Get Temperature Limits",
    "Start Climate Chamber": "Start Chamber",
    "Stop Climate Chamber": "Stop Chamber",
    "Stop And Disconnect Climate Chamber": "Disconnect",
    "Set Climate Chamber Heating Gradient": "Set Heating Gradient",
    "Get Climate Chamber Heating Gradient": "Get Heating Gradient",
    "Set Climate Chamber Cooling Gradient": "Set Cooling Gradient",
    "Get Climate Chamber Cooling Gradient": "Get Cooling Gradient",
    "Set Climate Chamber Dryer": "Set Dryer",
    "Get Climate Chamber Dryer": "Get Dryer",
    "Set Climate Chamber Compressed Air": "Set Compressed Air",
    "Get Climate Chamber Compressed Air": "Get Compressed Air",
    "Wait Until Climate Chamber Is Stable": "Wait For Temperature Stability",
    "Wait For Climate Chamber Dwell": "Wait For Dwell",
    "Climate Chamber Temperature Should Be": "Temperature Should Be",
    "Climate Chamber Temperature Should Be Within": "Temperature Should Be Within",
    "Climate Chamber Setpoint Should Be": "Temperature Setpoint Should Be",
    "Climate Chamber Should Be Connected": "Connection Should Be Available",
    "Climate Chamber Should Be Running": "Chamber Should Be Running",
    "Climate Chamber Should Be Stopped": "Chamber Should Be Stopped",
}

PROTOCOL: dict[str, list[str]] = {
    "Connect": ["TCP OPEN", "99997¶1¶1\\r", "99997¶1¶2\\r", "99997¶1¶3\\r"],
    "Disconnect": [
        "14001¶1¶7¶0\\r",
        "14003¶1¶7\\r",
        "14001¶1¶8¶0\\r",
        "14003¶1¶8\\r",
        "14003¶1¶1\\r",
        "14001¶1¶1¶0\\r",
        "14003¶1¶1\\r",
        "TCP CLOSE",
    ],
    "Disconnect All": [
        "14001¶1¶7¶0\\r",
        "14003¶1¶7\\r",
        "14001¶1¶8¶0\\r",
        "14003¶1¶8\\r",
        "14003¶1¶1\\r",
        "14001¶1¶1¶0\\r",
        "14003¶1¶1\\r",
        "TCP CLOSE",
    ],
    "Check Communication": ["10012¶1\\r"],
    "Get Connection State": ["10012¶1\\r when refresh=true"],
    "Get Identity": ["99997¶1¶1\\r", "99997¶1¶2\\r", "99997¶1¶3\\r when refresh=true"],
    "Reconnect": ["TCP CLOSE", "TCP OPEN", "99997¶1¶1\\r", "99997¶1¶2\\r", "99997¶1¶3\\r"],
    "Set Temperature": ["11001¶1¶1¶<value_c>\\r", "11002¶1¶1\\r"],
    "Get Temperature Setpoint": ["11002¶1¶1\\r"],
    "Measure Temperature": ["11004¶1¶1\\r"],
    "Start Chamber": ["14003¶1¶1\\r", "14001¶1¶1¶1\\r", "14003¶1¶1\\r"],
    "Stop Chamber": ["14003¶1¶1\\r", "14001¶1¶1¶0\\r", "14003¶1¶1\\r"],
    "Get Chamber Running State": ["14003¶1¶1\\r"],
    "Set Temperature And Wait": [
        "11001¶1¶1¶<value_c>\\r",
        "11002¶1¶1\\r",
        "14003¶1¶1\\r",
        "14001¶1¶1¶1\\r",
        "11004¶1¶1\\r repeated",
    ],
    "Wait For Temperature Stability": ["11002¶1¶1\\r when target omitted", "11004¶1¶1\\r repeated"],
    "Wait For Dwell": ["11004¶1¶1\\r repeated"],
    "Set Heating Gradient": ["11068¶1¶1¶<value>\\r", "11066¶1¶1\\r"],
    "Get Heating Gradient": ["11066¶1¶1\\r"],
    "Set Cooling Gradient": ["11072¶1¶1¶<value>\\r", "11070¶1¶1\\r"],
    "Get Cooling Gradient": ["11070¶1¶1\\r"],
    "Set Dryer": ["14001¶1¶8¶<0|1>\\r", "14003¶1¶8\\r"],
    "Get Dryer": ["14003¶1¶8\\r"],
    "Set Compressed Air": ["14001¶1¶7¶<0|1>\\r", "14003¶1¶7\\r"],
    "Get Compressed Air": ["14003¶1¶7\\r"],
    "Get Chamber Status": ["10012¶1\\r"],
    "Safe Shutdown": [
        "14001¶1¶7¶0\\r",
        "14003¶1¶7\\r",
        "14001¶1¶8¶0\\r",
        "14003¶1¶8\\r",
        "14003¶1¶1\\r",
        "14001¶1¶1¶0\\r",
        "14003¶1¶1\\r",
    ],
    "Temperature Should Be": ["11004¶1¶1\\r"],
    "Temperature Should Be Within": ["11004¶1¶1\\r"],
    "Temperature Setpoint Should Be": ["11002¶1¶1\\r"],
    "Chamber Should Be Running": ["14003¶1¶1\\r"],
    "Chamber Should Be Stopped": ["14003¶1¶1\\r"],
    "Connection Should Be Available": ["10012¶1\\r"],
}


def _annotation(value: Any) -> str:
    return str(value).replace("'", "")


def public_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for method_name, function in inspect.getmembers(VotschClimateChamberLibrary, inspect.isfunction):
        keyword_name = getattr(function, "robot_name", None)
        if not keyword_name:
            continue
        signature = inspect.signature(function)
        arguments = []
        for parameter in signature.parameters.values():
            if parameter.name == "self":
                continue
            arguments.append(
                {
                    "name": parameter.name,
                    "kind": str(parameter.kind).split(".")[-1].lower(),
                    "required": parameter.default is inspect.Parameter.empty,
                    "default": None if parameter.default is inspect.Parameter.empty else parameter.default,
                    "annotation": _annotation(parameter.annotation),
                }
            )
        device_facing = keyword_name in PROTOCOL
        entries.append(
            {
                "keyword": keyword_name,
                "canonical_keyword": keyword_name,
                "python_method": method_name,
                "signature": str(signature),
                "arguments": arguments,
                "return_type": _annotation(signature.return_annotation),
                "tags": list(getattr(function, "robot_tags", ())),
                "device_facing": device_facing,
                "deprecated": False,
                "introduced_in": "26.04",
                "protocol_vector": (
                    f"VCC-{keyword_name.upper().replace(' ', '_')}-001" if device_facing else None
                ),
                "documentation": inspect.getdoc(function) or "See generated Libdoc.",
            }
        )
    return sorted(entries, key=lambda item: item["keyword"].casefold())


def write_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=True), encoding="utf-8")


def main() -> int:
    entries = public_entries()
    api = {
        "schema_version": "1.0",
        "driver": "rf_votsch_climate_chamber",
        "release_version": RELEASE_VERSION,
        "api_version": API_VERSION,
        "authority": f"{API_SPEC} v{API_SPEC_VERSION}",
        "library": {
            "import": "rf_votsch_climate_chamber.library",
            "class": "VotschClimateChamberLibrary",
            "scope": "SUITE",
            "auto_keywords": False,
        },
        "keywords": entries,
        "migration": {
            "api_2_removed_in": "26.07",
            "removed_aliases": REMOVED_LEGACY_ALIASES,
            "replacement_policy": "Use canonical RFDS-002 keywords.",
        },
    }
    write_yaml(ROOT / "api/public_api.yaml", api)
    (ROOT / "api/public_api.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": ["schema_version", "driver", "release_version", "api_version", "library", "keywords"],
                "properties": {
                    "keywords": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": [
                                "keyword",
                                "canonical_keyword",
                                "python_method",
                                "signature",
                                "return_type",
                                "device_facing",
                                "deprecated",
                            ],
                        },
                    }
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_yaml(
        ROOT / "api/compatibility.yaml",
        {
            "schema_version": "1.0",
            "release": RELEASE_VERSION,
            "previous_release": "26.07",
            "classification": "behavioral_hardening",
            "previous_api_version": API_VERSION,
            "api_version": API_VERSION,
            "removed_legacy_aliases": REMOVED_LEGACY_ALIASES,
            "authorization": "Explicit user request to remove all legacy code and functions on 2026-07-31.",
        },
    )
    write_yaml(
        ROOT / "api/conformance_state.yaml",
        {
            "schema_version": "1.0",
            "release": RELEASE_VERSION,
            "robot_runtime_execution": "NOT_RUN",
            "reason": "Robot Framework unavailable in build environment",
            "python_simulator_smoke": "PASS",
            "release_class": RELEASE_CLASS,
            "d1_candidate": True,
        },
    )
    write_yaml(
        ROOT / "api/decisions.yaml",
        {
            "decisions": [
                {
                    "id": "ADR-26.07-001",
                    "decision": "Remove API 2 compatibility aliases and duplicate Python package",
                    "reason": "Explicit cleanup request; canonical RFDS-002 API is authoritative",
                    "impact": "API_VERSION incremented to 3.0.0",
                },
                {
                    "id": "ADR-26.07-002",
                    "decision": "Use RFDS-005 flat package layout",
                    "reason": "RFDS-005 owns package layout and prohibits src layout",
                },
                {
                    "id": "ADR-26.08-001",
                    "decision": "Verify setpoint writes using bounded polling instead of one immediate readback",
                    "reason": "Real chamber acknowledged writes before the public setpoint register updated",
                },
                {
                    "id": "ADR-26.08-002",
                    "decision": "Require explicit auxiliary-output channel mappings on real hardware",
                    "reason": "Digital output 8 was rejected on the tested chamber during safe shutdown",
                },
            ]
        },
    )
    write_yaml(
        ROOT / "api/deviations.yaml",
        {
            "deviations": [
                {
                    "id": "DEV-26.04-001",
                    "requirement": "RFDS-003 shared rfds-core dependency",
                    "status": "OPEN",
                    "severity": "MAJOR",
                    "reason": "Approved rfds-core distribution was not supplied",
                    "temporary_control": "Local composed suite lifecycle listener and typed RFDS interfaces",
                    "expiry": "Before P1",
                },
                {
                    "id": "DEV-26.07-001",
                    "requirement": "RFDS-002 minimum deprecation window",
                    "status": "ACCEPTED",
                    "severity": "BREAKING",
                    "reason": "User explicitly directed complete legacy removal",
                    "control": "API major increment, migration table, history, review, and RFDS-019 synchronization",
                },
            ]
        },
    )
    write_yaml(
        ROOT / "api/unknowns.yaml",
        {
            "unknowns": [
                {
                    "id": "UNK-26.04-001",
                    "item": "Qualified chamber model and firmware matrix",
                    "resolution": "Real-device D2/P1 evidence required",
                },
                {
                    "id": "UNK-26.04-002",
                    "item": "Digital output 7/8 mapping across chamber models",
                    "resolution": "Verify against device documentation and hardware before enabling auxiliary outputs",
                },
            ]
        },
    )

    contract: dict[str, Any] = {
        "schema_version": "3.0",
        "contract_id": "rf_votsch_climate_chamber",
        "contract_version": RELEASE_VERSION,
        "driver": {
            "name": "rf_votsch_climate_chamber",
            "version": RELEASE_VERSION,
            "api_version": API_VERSION,
            "release_class": RELEASE_CLASS,
            "transport": ["tcp", "simulator"],
            "device_family": "Vötsch/SimServ-compatible climate chamber",
        },
        "states": [
            "DISCONNECTED",
            "CONNECTING",
            "CONNECTED",
            "CONFIGURED",
            "BUSY",
            "WAITING",
            "CANCELLING",
            "RECOVERING",
            "ERROR",
            "CLOSING",
        ],
        "resources": [{"id": "climate_chamber_session", "type": "exclusive_session", "shareable": False}],
        "capabilities": [],
        "safety": {
            "safe_shutdown_keyword": "Safe Shutdown",
            "temperature_limits": "configured per connection",
            "unknowns_reference": "api/unknowns.yaml",
        },
        "limitations": [
            "Real-device compatibility matrix is UNKNOWN until D2/P1 validation.",
            "Auxiliary output mapping is model-dependent and UNKNOWN without qualification.",
        ],
    }
    for entry in entries:
        risk = next(
            (
                tag.split(":", 1)[1]
                for tag in entry["tags"]
                if tag.startswith("rfds:") and tag.endswith("_risk")
            ),
            "unknown",
        )
        keyword_name = entry["keyword"]
        contract["capabilities"].append(
            {
                "id": "keyword." + keyword_name.lower().replace(" ", "_"),
                "keyword": keyword_name,
                "canonical_keyword": keyword_name,
                "signature": entry["signature"],
                "return_type": entry["return_type"],
                "device_facing": entry["device_facing"],
                "protocol_vector": entry["protocol_vector"],
                "deprecated": False,
                "risk": risk,
                "preconditions": ["connected"] if entry["device_facing"] and keyword_name != "Connect" else [],
                "resources": ["climate_chamber_session"] if entry["device_facing"] else [],
                "side_effects": (
                    "device_or_connection_state_may_change"
                    if any(token in keyword_name for token in ("Set ", "Start", "Stop", "Disconnect", "Safe Shutdown", "Reconnect"))
                    else "none_intended"
                ),
                "timeout": "finite; see signature/configuration",
                "errors": "RFDS-007 DriverError hierarchy",
            }
        )
    write_yaml(ROOT / "ai/votsch_climate_chamber_ai_contract.yaml", contract)
    contract_bytes = (ROOT / "ai/votsch_climate_chamber_ai_contract.yaml").read_bytes()
    lock = {
        "schema_version": "1.0",
        "contract": "ai/votsch_climate_chamber_ai_contract.yaml",
        "sha256": hashlib.sha256(contract_bytes).hexdigest(),
        "release": RELEASE_VERSION,
        "keyword_count": len(entries),
        "public_api_sha256": hashlib.sha256((ROOT / "api/public_api.yaml").read_bytes()).hexdigest(),
    }
    write_yaml(ROOT / "ai/votsch_climate_chamber_ai_contract.lock", lock)

    conformance = ROOT / "tests/conformance"
    inventory = {
        "schema_version": "1.1",
        "driver": "rf_votsch_climate_chamber",
        "generated_from": "api/public_api.yaml",
        "keywords": [
            {key: entry[key] for key in (
                "keyword",
                "canonical_keyword",
                "python_method",
                "arguments",
                "return_type",
                "device_facing",
                "protocol_vector",
                "deprecated",
            )}
            for entry in entries
        ],
    }
    vectors = {"schema_version": "1.1", "transport": "votsch_simserv_tcp", "vectors": []}
    for entry in entries:
        if not entry["device_facing"]:
            continue
        vectors["vectors"].append(
            {
                "id": entry["protocol_vector"],
                "keyword": entry["keyword"],
                "transport": "tcp_or_simulator",
                "expected_outbound": PROTOCOL[entry["keyword"]],
                "expected_inbound": {"response_required": True, "terminator": "\\r", "status_code": "1"},
                "expected_return": {"type": "see public_api.yaml"},
                "timeout_s": 20,
                "oracles": ["outbound_structured", "raw_response", "parsed_value"],
            }
        )
    write_yaml(conformance / "data/keyword_inventory.yaml", inventory)
    write_yaml(conformance / "data/protocol_vectors.yaml", vectors)
    write_yaml(conformance / "data/exclusions.yaml", {"schema_version": "1.1", "exclusions": []})
    write_yaml(
        conformance / "expected/response_schemas/common.yaml",
        {"simserv_response": {"terminator": "CR", "separator": "0xB6", "success_status": 1}},
    )

    schema_hash = hashlib.sha256((ROOT / "config/schema.json").read_bytes()).hexdigest()
    manifest = {
        "schema_version": "1.0",
        "plugin_api_version": "1.0",
        "plugin_id": "votsch.climate_chamber",
        "driver_name": "rf_votsch_climate_chamber",
        "display_name": "Vötsch Climate Chamber Driver",
        "description": "RFDS Robot Framework driver for Vötsch and SimServ-compatible TCP climate chambers.",
        "distribution_name": "rf-votsch-climate-chamber",
        "distribution_version": PEP440_VERSION,
        "provider": "rf_votsch_climate_chamber.plugin:VotschClimateChamberPlugin",
        "robot_library_import": "rf_votsch_climate_chamber.library",
        "robot_library_class": "VotschClimateChamberLibrary",
        "supported_device_families": ["votsch_simserv_climate_chamber"],
        "supported_models": ["UNKNOWN - qualification pending real-device evidence"],
        "supported_transports": ["tcp", "simulator"],
        "capability_descriptor": {
            "kind": "python_object",
            "value": "rf_votsch_climate_chamber.capabilities:get_capability_model",
        },
        "configuration_schema": {
            "kind": "package_resource",
            "package": "rf_votsch_climate_chamber",
            "path": "resources/config.schema.json",
            "canonical_source": "config/schema.json",
            "sha256": schema_hash,
        },
        "ai_contract": {
            "kind": "package_resource",
            "package": "rf_votsch_climate_chamber",
            "path": "resources/votsch_climate_chamber_ai_contract.yaml",
            "canonical_source": "ai/votsch_climate_chamber_ai_contract.yaml",
            "sha256": lock["sha256"],
        },
        "documentation": {"kind": "repository_path", "path": "docs/index.md"},
        "minimum_python": ">=3.11",
        "robot_framework_version": ">=7,<9",
        "rfds_platform_version": ">=1,<2",
        "optional_dependency_groups": ["dev", "docs"],
        "multi_instance": True,
        "thread_safe": False,
        "simulation_supported": True,
        "hardware_discovery_supported": False,
        "load_policy": "explicit",
        "deprecation": {"deprecated": False, "replacement_plugin_id": None, "removal_version": None},
        "manifest_hash_algorithm": "sha256",
    }
    (ROOT / "rf_votsch_climate_chamber/resources/plugin_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Keep human-readable and machine-readable API documentation generated from
    # the same runtime source as RFDS-017 and RFDS-019 metadata.
    lines = [
        f"# Canonical Robot Framework Keywords — v{RELEASE_VERSION}",
        "",
        f"This API contains **{len(entries)} canonical keywords**. API 2 compatibility aliases",
        "were removed in v26.07; see [migration.md](migration.md).",
        "",
    ]
    for entry in entries:
        lines.extend(
            [
                f"## {entry['keyword']}",
                "",
                f"- Python method: `{entry['python_method']}`",
                f"- Signature: `{entry['signature']}`",
                f"- Return type: `{entry['return_type']}`",
                f"- Device-facing: `{'yes' if entry['device_facing'] else 'no'}`",
                f"- Protocol vector: `{entry['protocol_vector'] or 'N/A'}`",
                f"- Tags: `{', '.join(entry['tags']) or 'none'}`",
                "",
                entry['documentation'],
                "",
            ]
        )
    (ROOT / "docs/keywords.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    generated = ROOT / "generated/api_manifest"
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "public_api.json").write_text(
        json.dumps(api, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )

    print(f"Generated {len(entries)} canonical public keywords and {len(vectors['vectors'])} protocol vectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

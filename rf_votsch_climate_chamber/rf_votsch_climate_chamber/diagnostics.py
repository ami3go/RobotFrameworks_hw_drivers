"""Structured diagnostics export with JSON-compatible values."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .converters import sanitize
from .sessions import SessionRegistry


def get_diagnostics(registry: SessionRegistry) -> dict[str, Any]:
    sessions: list[dict[str, Any]] = []
    for state in registry.list_states():
        alias = state["alias"]
        try:
            handle = registry.get(alias, require_connected=False)
            detail = handle.core.diagnostics()
        except Exception as exc:
            detail = {"error": str(exc)}
        sessions.append({"connection": state, "diagnostics": sanitize(detail)})
    return {
        "schema_version": "1.0",
        "driver": "rf_votsch_climate_chamber",
        "active_alias": registry.active_alias,
        "sessions": sessions,
    }


def export_diagnostics(registry: SessionRegistry, destination: str | Path) -> dict[str, Any]:
    payload = get_diagnostics(registry)
    path = Path(destination).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"path": str(path), "bytes": path.stat().st_size, "schema_version": payload["schema_version"]}

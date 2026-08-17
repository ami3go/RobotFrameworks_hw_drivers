"""RFDS-014 JSON configuration manager.

Configuration is validated before application.  Import defaults are validation
only, and profile persistence is explicit.  The manager never contacts chamber
hardware and never writes a physical-device setting.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from copy import deepcopy
from importlib.resources import files
from pathlib import Path
from typing import Any

from .exceptions import DriverConfigurationError, DriverResourceNotFoundError

try:
    import jsonschema
except ImportError:  # pragma: no cover - package dependency supplies it in normal installs.
    jsonschema = None  # type: ignore[assignment]

_PROFILE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
SCHEMA_ID = "rf_votsch_climate_chamber.configuration"
SCHEMA_VERSION = "1.0.0"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class ConfigurationManager:
    def __init__(self, *, managed_root: str | Path | None = None) -> None:
        resource_root = files("rf_votsch_climate_chamber.resources")
        self._schema = json.loads(resource_root.joinpath("config.schema.json").read_text(encoding="utf-8"))
        self._default = json.loads(
            resource_root.joinpath("default_configuration.json").read_text(encoding="utf-8")
        )
        self._effective = deepcopy(self._default)
        if managed_root is None:
            base = Path(os.environ.get("RFDS_CONFIG_HOME", Path.home() / ".config"))
            managed_root = base / "rf_votsch_climate_chamber"
        self._managed_root = Path(managed_root)

    def get_schema(self) -> dict[str, Any]:
        return {
            "schema_id": SCHEMA_ID,
            "schema_version": SCHEMA_VERSION,
            "schema": deepcopy(self._schema),
            "schema_fingerprint": fingerprint(self._schema),
        }

    def get_default(self) -> dict[str, Any]:
        return deepcopy(self._default)

    def get_effective(self, *, include_sources: bool = False) -> dict[str, Any]:
        result = deepcopy(self._effective)
        result["configuration_fingerprint"] = fingerprint(self._effective)
        result["requires_reconnect"] = False
        result["requires_restart"] = False
        if include_sources:
            result["sources"] = {"package_default": True, "instance_override": True}
        return result

    def validate(self, configuration: Any, *, strict: bool = True) -> dict[str, Any]:
        try:
            document, source = self._load_source(configuration)
        except DriverConfigurationError as exc:
            return self._result(valid=False, source=str(configuration), errors=[exc.to_dict()])
        document, removed_annotations = self._strip_runtime_annotations(document)
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        if removed_annotations:
            warnings.append(
                {
                    "path": "",
                    "message": (
                        "runtime annotations were ignored during configuration validation: "
                        + ", ".join(sorted(removed_annotations))
                    ),
                }
            )
        if jsonschema is not None:
            validator = jsonschema.Draft202012Validator(self._schema)
            for error in sorted(validator.iter_errors(document), key=lambda item: list(item.path)):
                errors.append({"path": "/" + "/".join(str(part) for part in error.path), "message": error.message})
        else:
            for key in ("schema_version", "driver", "profile", "settings", "extensions", "metadata"):
                if key not in document:
                    errors.append({"path": f"/{key}", "message": "required property is missing"})
            if strict:
                warnings.append({"path": "", "message": "jsonschema dependency unavailable; structural validation only"})
        safety = document.get("settings", {}).get("safety", {}) if isinstance(document, dict) else {}
        minimum = safety.get("temperature_min_c")
        maximum = safety.get("temperature_max_c")
        if isinstance(minimum, (int, float)) and isinstance(maximum, (int, float)) and minimum >= maximum:
            errors.append({"path": "/settings/safety", "message": "temperature_min_c must be lower than temperature_max_c"})
        auxiliary = document.get("settings", {}).get("auxiliary_outputs", {}) if isinstance(document, dict) else {}
        dryer_channel = auxiliary.get("dryer_output_channel")
        air_channel = auxiliary.get("compressed_air_output_channel")
        if dryer_channel is not None and air_channel is not None and dryer_channel == air_channel:
            errors.append(
                {
                    "path": "/settings/auxiliary_outputs",
                    "message": "dryer and compressed-air outputs must not use the same channel",
                }
            )
        return self._result(
            valid=not errors,
            source=source,
            errors=errors,
            warnings=warnings,
            configuration=document if not errors else None,
        )

    def import_configuration(
        self,
        source: Any,
        *,
        apply: bool = False,
        persist: bool = False,
        profile_name: str | None = None,
        strict: bool = True,
    ) -> dict[str, Any]:
        result = self.validate(source, strict=strict)
        result.update({"applied": False, "persisted": False, "profile_name": profile_name})
        if not result["valid"]:
            return result
        document = result.pop("configuration")
        if apply:
            self._effective = deepcopy(document)
            result["applied"] = True
            result["status"] = "APPLIED"
        if persist:
            if profile_name is None:
                raise DriverConfigurationError("profile_name is required when persist=True", operation="Import Driver Configuration")
            self._write_profile(profile_name, document, overwrite=False)
            result["persisted"] = True
        return result

    def export_configuration(
        self,
        destination: str | Path | None = None,
        *,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        document = deepcopy(self._effective)
        text = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        written_path: str | None = None
        if destination is not None:
            path = Path(destination).expanduser().resolve()
            if path.exists() and not overwrite:
                raise DriverConfigurationError(
                    f"destination already exists: {path}",
                    operation="Export Driver Configuration",
                )
            path.parent.mkdir(parents=True, exist_ok=True)
            self._atomic_write(path, text)
            written_path = str(path)
        return {
            "status": "EXPORTED",
            "valid": True,
            "configuration": document,
            "json": text,
            "destination": written_path,
            "configuration_fingerprint": fingerprint(document),
        }

    def save_profile(self, profile_name: str, *, overwrite: bool = False, set_active: bool = False) -> dict[str, Any]:
        path = self._write_profile(profile_name, self._effective, overwrite=overwrite)
        if set_active:
            self._managed_root.mkdir(parents=True, exist_ok=True)
            self._atomic_write(self._managed_root / "active_profile.txt", profile_name + "\n")
        return {"status": "SAVED", "profile_name": profile_name, "path": str(path), "set_active": set_active}

    def load_profile(self, profile_name: str, *, apply: bool = False) -> dict[str, Any]:
        path = self._profile_path(profile_name)
        if not path.exists():
            raise DriverResourceNotFoundError(f"configuration profile {profile_name!r} does not exist", operation="Load Driver Configuration")
        return self.import_configuration(path, apply=apply, profile_name=profile_name)

    def list_profiles(self) -> list[dict[str, Any]]:
        if not self._managed_root.exists():
            return []
        active_path = self._managed_root / "active_profile.txt"
        active = active_path.read_text(encoding="utf-8").strip() if active_path.exists() else None
        result = []
        for path in sorted(self._managed_root.glob("*.json")):
            result.append({"profile_name": path.stem, "path": str(path), "active": path.stem == active})
        return result

    def delete_profile(self, profile_name: str, *, confirm: bool = False) -> dict[str, Any]:
        if not confirm:
            raise DriverConfigurationError("confirm=True is required to delete a profile", operation="Delete Driver Configuration Profile")
        path = self._profile_path(profile_name)
        if not path.exists():
            return {"status": "NOT_FOUND", "profile_name": profile_name, "deleted": False}
        path.unlink()
        return {"status": "DELETED", "profile_name": profile_name, "deleted": True}

    def reset(self, *, apply: bool = False) -> dict[str, Any]:
        result = {
            "status": "VALID",
            "valid": True,
            "applied": False,
            "configuration": deepcopy(self._default),
            "configuration_fingerprint": fingerprint(self._default),
        }
        if apply:
            self._effective = deepcopy(self._default)
            result["applied"] = True
            result["status"] = "APPLIED"
        return result

    @staticmethod
    def _strip_runtime_annotations(document: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        """Remove read-only fields added by ``Get Driver Configuration``.

        RFDS configuration documents must be round-trippable.  Earlier releases
        added runtime annotations at the document root, but then rejected those
        same fields because the JSON schema forbids unknown properties.  Import
        now accepts the library's own exported representation while keeping the
        persisted configuration schema strict.
        """
        normalized = deepcopy(document)
        removed: list[str] = []
        for key in ("configuration_fingerprint", "requires_reconnect", "requires_restart", "sources"):
            if key in normalized:
                normalized.pop(key, None)
                removed.append(key)
        return normalized, removed

    def _load_source(self, source: Any) -> tuple[dict[str, Any], str]:
        if isinstance(source, dict):
            return deepcopy(source), "<memory>"
        if isinstance(source, Path) or (isinstance(source, str) and Path(source).expanduser().exists()):
            path = Path(source).expanduser().resolve()
            try:
                return json.loads(path.read_text(encoding="utf-8")), str(path)
            except (OSError, json.JSONDecodeError) as exc:
                raise DriverConfigurationError(f"cannot read JSON configuration from {path}: {exc}", operation="configuration import") from exc
        if isinstance(source, str):
            try:
                value = json.loads(source)
            except json.JSONDecodeError as exc:
                raise DriverConfigurationError(f"configuration text is not valid JSON: {exc}", operation="configuration import") from exc
            if not isinstance(value, dict):
                raise DriverConfigurationError("configuration root must be a JSON object", operation="configuration import")
            return value, "<json-text>"
        raise DriverConfigurationError(f"unsupported configuration source type: {type(source).__name__}", operation="configuration import")

    def _profile_path(self, profile_name: str) -> Path:
        if not _PROFILE_PATTERN.fullmatch(profile_name):
            raise DriverConfigurationError("profile_name contains unsupported characters", operation="configuration profile")
        return self._managed_root / f"{profile_name}.json"

    def _write_profile(self, profile_name: str, document: dict[str, Any], *, overwrite: bool) -> Path:
        path = self._profile_path(profile_name)
        if path.exists() and not overwrite:
            raise DriverConfigurationError(f"configuration profile {profile_name!r} already exists", operation="Save Driver Configuration")
        path.parent.mkdir(parents=True, exist_ok=True)
        self._atomic_write(path, json.dumps(document, indent=2, sort_keys=True) + "\n")
        return path

    @staticmethod
    def _atomic_write(path: Path, text: str) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(text)
            temp_path = Path(handle.name)
        temp_path.replace(path)

    @staticmethod
    def _result(
        *,
        valid: bool,
        source: str,
        errors: list[dict[str, Any]],
        warnings: list[dict[str, Any]] | None = None,
        configuration: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "status": "VALID" if valid else "INVALID",
            "valid": valid,
            "errors": errors,
            "warnings": list(warnings or []),
            "source": source,
            "schema_id": SCHEMA_ID,
            "source_schema_version": SCHEMA_VERSION,
            "target_schema_version": SCHEMA_VERSION,
            "changed_paths": [],
            "requires_reconnect": False,
            "requires_restart": False,
            "device_persistent_changes": [],
            "confirmation_required": False,
            "configuration_fingerprint": None if configuration is None else fingerprint(configuration),
        }
        if configuration is not None:
            result["configuration"] = configuration
        return result

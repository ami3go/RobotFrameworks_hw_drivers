"""RFDS-014 host-side JSON configuration support.

This module performs no hardware access and uses only the Python standard
library so configuration import/export remains available without optional
packages.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from .exceptions import DriverConfigurationError, DriverValidationError

_SCHEMA_ID = "rf_hp34401a.configuration"
_SCHEMA_VERSION = "1.0.0"
_RFDS014_VERSION = "1.0"


def _resource_dir() -> Path:
    return Path(__file__).resolve().parent / "resources" / "configuration"


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _profile_root() -> Path:
    override = os.environ.get("RF_HP34401A_PROFILE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "RFDS" / "rf_hp34401a" / "profiles"
    return Path.home() / ".config" / "rfds" / "rf_hp34401a" / "profiles"


def _safe_profile_name(name: str) -> str:
    text = str(name).strip()
    if not text or len(text) > 64:
        raise DriverValidationError("Profile name must contain 1 to 64 characters")
    if text in {".", ".."} or text.startswith("."):
        raise DriverValidationError("Profile name may not be hidden or relative")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    if any(char not in allowed for char in text):
        raise DriverValidationError(
            "Profile name may contain only letters, digits, underscore, hyphen and period"
        )
    return text


class ConfigurationManager:
    """Validate, merge, import, export, and explicitly persist driver profiles."""

    def __init__(self) -> None:
        self._schema = self._load_json(_resource_dir() / "schema.json")
        self._default = self._load_json(_resource_dir() / "default.json")
        self._effective = deepcopy(self._default)
        self._sources: dict[str, str] = {"settings": "PACKAGE_DEFAULT"}
        self.validate(self._default, strict=True)

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DriverConfigurationError(f"Cannot load configuration file {path}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise DriverConfigurationError(f"Configuration file {path} must contain a JSON object")
        return loaded

    def schema(self) -> dict[str, Any]:
        return deepcopy(self._schema)

    def default(self) -> dict[str, Any]:
        return deepcopy(self._default)

    def effective(self, *, include_sources: bool = False) -> dict[str, Any]:
        result = deepcopy(self._effective)
        if include_sources:
            result.setdefault("metadata", {})["resolved_sources"] = deepcopy(self._sources)
        return result

    def validate(self, document: Mapping[str, Any], *, strict: bool = True) -> dict[str, Any]:
        if not isinstance(document, Mapping):
            raise DriverValidationError("Driver configuration must be a JSON object")
        data = deepcopy(dict(document))
        required = {"rfds014_version", "schema_id", "schema_version", "driver", "profile", "settings"}
        missing = sorted(required - data.keys())
        if missing:
            raise DriverValidationError(f"Configuration is missing required keys: {missing}")
        if data.get("rfds014_version") != _RFDS014_VERSION:
            raise DriverValidationError(
                f"Unsupported rfds014_version {data.get('rfds014_version')!r}; expected {_RFDS014_VERSION}"
            )
        if data.get("schema_id") != _SCHEMA_ID:
            raise DriverValidationError(
                f"Configuration schema_id must be {_SCHEMA_ID!r}"
            )
        if data.get("schema_version") != _SCHEMA_VERSION:
            raise DriverValidationError(
                f"Unsupported schema_version {data.get('schema_version')!r}; expected {_SCHEMA_VERSION}"
            )
        driver = data.get("driver")
        if not isinstance(driver, Mapping) or driver.get("driver_name") != "rf_hp34401a":
            raise DriverValidationError("Configuration driver.driver_name must be 'rf_hp34401a'")
        profile = data.get("profile")
        if not isinstance(profile, Mapping):
            raise DriverValidationError("Configuration profile must be an object")
        _safe_profile_name(str(profile.get("name", "")))
        settings = data.get("settings")
        if not isinstance(settings, Mapping):
            raise DriverValidationError("Configuration settings must be an object")
        permitted_sections = {"transport", "timeouts", "retry", "logging", "simulation", "safety", "device"}
        if strict:
            unknown = sorted(set(settings) - permitted_sections)
            if unknown:
                raise DriverValidationError(f"Unknown configuration settings sections: {unknown}")
        timeouts = settings.get("timeouts", {})
        if not isinstance(timeouts, Mapping):
            raise DriverValidationError("settings.timeouts must be an object")
        for key in ("communication_s", "self_test_s", "long_measurement_s"):
            if key in timeouts:
                value = timeouts[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                    raise DriverValidationError(f"settings.timeouts.{key} must be a positive number")
        simulation = settings.get("simulation", {})
        if not isinstance(simulation, Mapping):
            raise DriverValidationError("settings.simulation must be an object")
        if "enabled" in simulation and not isinstance(simulation["enabled"], bool):
            raise DriverValidationError("settings.simulation.enabled must be a Boolean")
        transport = settings.get("transport", {})
        if not isinstance(transport, Mapping):
            raise DriverValidationError("settings.transport must be an object")
        if transport.get("resource") not in (None, "", "${DMM_RESOURCE}"):
            # Resource values are allowed but never treated as secrets or auto-opened.
            if not isinstance(transport.get("resource"), str):
                raise DriverValidationError("settings.transport.resource must be a string or null")
        return data

    def apply(self, document: Mapping[str, Any], *, strict: bool = True) -> dict[str, Any]:
        candidate = self.validate(document, strict=strict)
        self._effective = candidate
        self._sources = {"settings": "RUNTIME_IMPORT"}
        return self.effective(include_sources=True)

    def import_json(
        self,
        source: str | Path | Mapping[str, Any],
        *,
        validate_only: bool = False,
        strict: bool = True,
    ) -> dict[str, Any]:
        if isinstance(source, Mapping):
            data = dict(source)
        else:
            text = str(source).strip()
            try:
                if text.startswith("{") or text.startswith("["):
                    data = json.loads(text)
                else:
                    path = Path(text).expanduser()
                    data = self._load_json(path) if path.exists() else json.loads(text)
            except (json.JSONDecodeError, OSError) as exc:
                raise DriverConfigurationError(f"Invalid configuration JSON or path: {exc}") from exc
        validated = self.validate(data, strict=strict)
        return validated if validate_only else self.apply(validated, strict=strict)

    def export_json(
        self,
        destination: str | Path | None = None,
        *,
        indent: int = 2,
    ) -> str:
        text = json.dumps(self._effective, indent=int(indent), sort_keys=True, ensure_ascii=False) + "\n"
        if destination is not None:
            path = Path(destination).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            self._atomic_write(path, text)
        return text

    def fingerprint(self) -> str:
        semantic = {"settings": self._effective.get("settings", {})}
        return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()

    def save_profile(self, name: str, *, overwrite: bool = False) -> str:
        profile_name = _safe_profile_name(name)
        root = _profile_root()
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{profile_name}.json"
        if path.exists() and not overwrite:
            raise DriverConfigurationError(
                f"Configuration profile {profile_name!r} already exists; set overwrite=true explicitly"
            )
        document = deepcopy(self._effective)
        document.setdefault("profile", {})["name"] = profile_name
        document["profile"]["scope"] = "USER"
        self._atomic_write(
            path,
            json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        )
        return str(path)

    def load_profile(self, name: str, *, validate_only: bool = False) -> dict[str, Any]:
        profile_name = _safe_profile_name(name)
        path = _profile_root() / f"{profile_name}.json"
        if not path.exists():
            raise DriverConfigurationError(f"Configuration profile {profile_name!r} does not exist")
        return self.import_json(path, validate_only=validate_only)

    def list_profiles(self) -> list[str]:
        root = _profile_root()
        if not root.exists():
            return []
        return sorted(path.stem for path in root.glob("*.json") if path.is_file())

    def delete_profile(self, name: str) -> None:
        profile_name = _safe_profile_name(name)
        path = _profile_root() / f"{profile_name}.json"
        if path.exists():
            path.unlink()

    def reset(self) -> dict[str, Any]:
        self._effective = deepcopy(self._default)
        self._sources = {"settings": "PACKAGE_DEFAULT"}
        return self.effective(include_sources=True)

    @staticmethod
    def _atomic_write(path: Path, text: str) -> None:
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        except Exception:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise

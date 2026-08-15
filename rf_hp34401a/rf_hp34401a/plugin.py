"""Side-effect-free RFDS-015 plugin provider."""

from __future__ import annotations

import importlib.util
import json
import platform
from pathlib import Path
from typing import Any, Mapping

from .version import __version__


class Hp34401APluginProvider:
    """Expose driver metadata without constructing or connecting the driver."""

    @classmethod
    def _manifest(cls) -> dict[str, Any]:
        path = Path(__file__).resolve().parent / "resources" / "plugin_manifest.json"
        return json.loads(path.read_text(encoding="utf-8"))

    @classmethod
    def get_descriptor(cls) -> dict[str, Any]:
        descriptor = cls._manifest()
        descriptor["installed_driver_version"] = __version__
        return descriptor

    @classmethod
    def validate_environment(cls) -> dict[str, Any]:
        checks = [
            {"id": "python", "status": "PASS", "value": platform.python_version()},
            {
                "id": "robotframework",
                "status": "PASS" if importlib.util.find_spec("robot") else "FAIL",
                "required": True,
            },
            {
                "id": "rfds-core",
                "status": "PASS" if importlib.util.find_spec("rfds_core") else "FAIL",
                "required": True,
                "requirement": ">=1.0,<2.0",
            },
            {
                "id": "pyvisa",
                "status": "PASS" if importlib.util.find_spec("pyvisa") else "WARNING",
                "required": False,
                "capability": "VISA_GPIB",
            },
            {
                "id": "pyserial",
                "status": "PASS" if importlib.util.find_spec("serial") else "WARNING",
                "required": False,
                "capability": "SERIAL_RS232",
            },
        ]
        return {
            "status": "FAIL" if any(c["status"] == "FAIL" for c in checks) else "PASS",
            "checks": checks,
        }

    @classmethod
    def create_library(cls, configuration: Mapping[str, Any] | None = None) -> Any:
        # Delayed import preserves metadata-only discovery and import safety.
        from .library import Hp34401ALibrary

        library = Hp34401ALibrary()
        if configuration is not None:
            library.import_driver_configuration(configuration)
        return library

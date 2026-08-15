"""Side-effect-free RFDS-015 plugin provider."""

from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import platform
import re
from pathlib import Path
from typing import Any, Mapping

from .version import __version__

_RFDS_CORE_REQUIREMENT = ">=1.0,<2.0"


def _rfds_core_check() -> dict[str, Any]:
    """Return a side-effect-free rfds-core compatibility check.

    RFDS-003 requires the effective shared-core version to be resolved at
    runtime.  The currently approved compatibility window is the complete 1.x
    series, so validation deliberately rejects missing, malformed, pre-1.0,
    and 2.x+ installations instead of merely checking that ``rfds_core`` can
    be imported.
    """

    check: dict[str, Any] = {
        "id": "rfds-core",
        "status": "FAIL",
        "required": True,
        "requirement": _RFDS_CORE_REQUIREMENT,
        "installed_version": None,
    }
    if importlib.util.find_spec("rfds_core") is None:
        check["reason"] = "rfds_core module is not importable"
        return check
    try:
        installed = importlib.metadata.version("rfds-core")
    except importlib.metadata.PackageNotFoundError:
        check["reason"] = "rfds_core is importable but rfds-core distribution metadata is missing"
        return check

    check["installed_version"] = installed
    match = re.match(r"^\s*(\d+)(?:\.(\d+))?", installed)
    if match is None:
        check["reason"] = f"cannot parse installed rfds-core version {installed!r}"
        return check

    major = int(match.group(1))
    minor = int(match.group(2) or 0)
    compatible = major == 1 and minor >= 0
    check["status"] = "PASS" if compatible else "FAIL"
    if not compatible:
        check["reason"] = (
            f"installed rfds-core {installed} does not satisfy {_RFDS_CORE_REQUIREMENT}"
        )
    return check


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
            _rfds_core_check(),
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

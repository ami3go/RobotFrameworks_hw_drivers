"""RFDS-015 plugin provider for the climate-chamber library.

Provider inspection and library construction are deliberately hardware-free.
Connections are opened only by the public ``Connect`` keyword.
"""

from __future__ import annotations

import json
import platform
import sys
from importlib.resources import files
from typing import Any

from .library import VotschClimateChamberLibrary
from .robot_compat import ROBOT_AVAILABLE


class VotschClimateChamberPlugin:
    """Side-effect-free RFDS driver-plugin provider."""

    @classmethod
    def get_descriptor(cls) -> dict[str, Any]:
        path = files("rf_votsch_climate_chamber").joinpath("resources/plugin_manifest.json")
        return json.loads(path.read_text(encoding="utf-8"))

    @classmethod
    def validate_environment(cls) -> dict[str, Any]:
        return {
            "compatible": sys.version_info >= (3, 11),
            "python_version": platform.python_version(),
            "robot_framework_available": ROBOT_AVAILABLE,
            "problems": [] if sys.version_info >= (3, 11) else ["Python 3.11 or newer is required"],
        }

    @classmethod
    def create_library(cls, *, config: dict[str, Any] | None = None) -> VotschClimateChamberLibrary:
        settings = dict(config or {})
        return VotschClimateChamberLibrary(
            default_resource=settings.get("default_resource"),
            default_timeout_s=settings.get("default_timeout_s", 5.0),
            managed_configuration_root=settings.get("managed_configuration_root"),
        )

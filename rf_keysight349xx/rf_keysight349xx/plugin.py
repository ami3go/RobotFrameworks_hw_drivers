"""RFDS plugin provider.  All descriptor operations are hardware-I/O free."""
from __future__ import annotations

from .capabilities import CAPABILITY_IDS
from .library import Keysight349xxLibrary
from .version import __version__


class Keysight349xxPluginProvider:
    def get_descriptor(self) -> dict:
        return {
            "plugin_id": "keysight.349xx",
            "driver_name": "rf_keysight349xx",
            "version": __version__,
            "models": ["34970A", "34972A"],
            "capability_ids": list(CAPABILITY_IDS),
            "simulation_supported": True,
        }

    def validate_environment(self) -> dict:
        return {
            "ok": True,
            "notes": [
                "Simulator requires no optional dependency.",
                "VISA hardware requires pyvisa and an installed VISA backend.",
                "D0 uses DEV-RFDSCORE-001 compatibility base pending shared rfds-core availability.",
            ],
        }

    def create_library(self, **kwargs):
        return Keysight349xxLibrary(**kwargs)

    def discover_hardware(self):
        # Discovery is intentionally not guessed in D0.  VISA enumeration will be
        # added through the approved RFDS transport discovery contract.
        return []

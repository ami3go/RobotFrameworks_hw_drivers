"""Initial configuration helpers."""
from __future__ import annotations

from copy import deepcopy

DEFAULT_CONFIGURATION = {
    "default_timeout_s": 5.0,
    "default_resource": None,
    "allow_raw_io": False,
    "simulation": {
        "default_model": "34972A",
        "default_modules": {"100": "34901A", "200": "0", "300": "34907A"},
    },
}


def get_default_configuration() -> dict:
    return deepcopy(DEFAULT_CONFIGURATION)

"""Static capability declaration available without connecting hardware."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

CAPABILITY_IDS = tuple(
    sorted(
        {
            "connection",
            "digital_io",
            "identity",
            "multi_connection",
            "safe_shutdown",
            "simulation",
            "temperature_control",
            "temperature_measurement",
        }
    )
)

CAPABILITY_MODEL: list[dict[str, Any]] = [
    {
        "capability_id": "connection.session",
        "display_name": "Connection lifecycle",
        "category": "connection",
        "support": "SUPPORTED",
        "availability": "AVAILABLE",
        "risk": "LOW",
        "keywords": ["Connect", "Disconnect", "Check Communication"],
    },
    {
        "capability_id": "identity.read",
        "display_name": "Read chamber identity",
        "category": "identity",
        "support": "SUPPORTED",
        "availability": "REQUIRES_CONNECTION",
        "risk": "NONE",
        "keywords": ["Get Identity"],
    },
    {
        "capability_id": "source.temperature.set",
        "display_name": "Temperature setpoint control",
        "category": "temperature_control",
        "support": "SUPPORTED",
        "availability": "REQUIRES_CONNECTION",
        "risk": "HIGH",
        "keywords": ["Set Temperature", "Get Temperature Setpoint", "Get Temperature Limits"],
        "unit": "c",
    },
    {
        "capability_id": "measure.temperature",
        "display_name": "Live chamber temperature measurement",
        "category": "temperature_measurement",
        "support": "SUPPORTED",
        "availability": "REQUIRES_CONNECTION",
        "risk": "NONE",
        "keywords": ["Measure Temperature"],
        "unit": "c",
    },
    {
        "capability_id": "io.auxiliary_outputs",
        "display_name": "Dryer, compressed-air and fan outputs",
        "category": "digital_io",
        "support": "CONDITIONAL",
        "availability": "REQUIRES_CONNECTION_AND_CONFIGURED_CHANNEL_MAPPING",
        "risk": "MEDIUM",
        "keywords": [
            "Set Dryer",
            "Get Dryer",
            "Set Compressed Air",
            "Get Compressed Air",
            "Set Fan",
            "Get Fan",
        ],
        "configuration": "settings.auxiliary_outputs",
    },
    {
        "capability_id": "safety.safe_shutdown",
        "display_name": "Safe thermal shutdown",
        "category": "safe_shutdown",
        "support": "SUPPORTED",
        "availability": "REQUIRES_CONNECTION",
        "risk": "HIGH",
        "keywords": ["Safe Shutdown"],
        "behavior": "Stops the chamber and disables only explicitly configured auxiliary outputs.",
    },
    {
        "capability_id": "simulation.protocol",
        "display_name": "Deterministic protocol simulator",
        "category": "simulation",
        "support": "SUPPORTED",
        "availability": "AVAILABLE",
        "risk": "NONE",
        "keywords": ["Connect"],
    },
]


def get_capability_ids() -> list[str]:
    return list(CAPABILITY_IDS)


def get_capability_model() -> list[dict[str, Any]]:
    return deepcopy(CAPABILITY_MODEL)

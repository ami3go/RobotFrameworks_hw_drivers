"""Model rating fallbacks and capability construction."""
from __future__ import annotations

from .enums import Protocol
from .measurements import InstrumentCapabilities, InstrumentIdentity


_MODEL_RATINGS: dict[str, tuple[float, float, float]] = {
    "8500B": (150.0, 30.0, 300.0),
    "8502B": (500.0, 15.0, 300.0),
    "8510B": (120.0, 120.0, 600.0),
    "8514B": (120.0, 240.0, 1500.0),
    "8542B": (150.0, 30.0, 150.0),
}


def normalize_model(model: str) -> str:
    token = model.strip().upper().replace("BK", "").replace("B&K", "")
    token = token.replace("PRECISION", "").strip(" -_")
    for known in _MODEL_RATINGS:
        if known in token:
            return known
    return model.strip()


def known_model(model: str) -> bool:
    return normalize_model(model) in _MODEL_RATINGS


def build_capabilities(identity: InstrumentIdentity, protocol: Protocol) -> InstrumentCapabilities:
    model = normalize_model(identity.model)
    ratings = _MODEL_RATINGS.get(model, (0.0, 0.0, 0.0))
    common = {
        "identity",
        "status",
        "measurement",
        "fixed_modes",
        "ranges",
        "slew",
        "remote_sense",
        "dynamic",
        "led",
        "ocp_test",
        "peak",
        "timing",
    }
    experimental = {"legacy_list", "battery", "autotest"}
    if protocol is Protocol.LEGACY:
        common = {"legacy_raw", "legacy_ratings"}
    return InstrumentCapabilities(
        model=model,
        firmware_revision=identity.firmware_revision,
        protocol=protocol,
        maximum_voltage_v=ratings[0],
        maximum_current_a=ratings[1],
        maximum_power_w=ratings[2],
        minimum_voltage_v=None,
        minimum_resistance_ohm=None,
        maximum_resistance_ohm=None,
        supported_features=frozenset(common),
        experimental_features=frozenset(experimental),
        evidence_ids=("MANUAL-2019-07-23",),
    )

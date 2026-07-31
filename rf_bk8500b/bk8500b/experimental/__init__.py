"""Explicitly unstable battery and autotest APIs.

No operation in this namespace is promoted to stable before real-hardware
protocol captures resolve command IDs, field widths, scaling, and response codes.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..exceptions import UnsupportedFeatureError


@dataclass(frozen=True, slots=True)
class ExperimentalFeatureMarker:
    experimental: bool = True
    reason: str = "HIL evidence required"


class BatteryController:
    experimental = True

    def __init__(self, *args, **kwargs) -> None:
        raise UnsupportedFeatureError(
            "Battery mode is experimental and blocked pending hardware validation"
        )


class AutoTestController:
    experimental = True

    def __init__(self, *args, **kwargs) -> None:
        raise UnsupportedFeatureError(
            "Autotest is experimental and blocked pending hardware validation"
        )


__all__ = ["ExperimentalFeatureMarker", "BatteryController", "AutoTestController"]

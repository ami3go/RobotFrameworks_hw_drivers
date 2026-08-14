"""Typed core driver for PicoScope oscilloscopes, across multiple SDK series (ps2000a, ps3000a, ...)."""

from .driver import PicoScope
from .enums import Channel, Coupling, MeasurementType, ProbeType, Range, TriggerDirection, WaveType
from .exceptions import (
    PicoScopeConnectionError,
    PicoScopeDeviceError,
    PicoScopeError,
    PicoScopeTimeoutError,
    PicoScopeValidationError,
)
from .measurements import compute_delay, compute_measurements, compute_phase
from .models import (
    AWGSettings,
    ChannelSettings,
    ConnectionState,
    InstrumentIdentity,
    Measurements,
    TimebaseSettings,
    TriggerSettings,
    Waveform,
)
from .simulator import SimulatedBackend, SimulatedBus

__version__ = "26.2"

__all__ = [
    "AWGSettings",
    "Channel",
    "ChannelSettings",
    "ConnectionState",
    "Coupling",
    "InstrumentIdentity",
    "MeasurementType",
    "Measurements",
    "PicoScope",
    "PicoScopeConnectionError",
    "PicoScopeDeviceError",
    "PicoScopeError",
    "PicoScopeTimeoutError",
    "PicoScopeValidationError",
    "ProbeType",
    "Range",
    "SimulatedBackend",
    "SimulatedBus",
    "TimebaseSettings",
    "TriggerDirection",
    "TriggerSettings",
    "WaveType",
    "Waveform",
    "compute_delay",
    "compute_measurements",
    "compute_phase",
    "__version__",
]

"""Typed core driver for the PicoScope 2000A-family (ps2000a) oscilloscopes."""

from .driver import PicoScope2000A
from .enums import Channel, Coupling, MeasurementType, ProbeType, Range, TriggerDirection, WaveType
from .exceptions import (
    PicoScope2000AConnectionError,
    PicoScope2000ADeviceError,
    PicoScope2000AError,
    PicoScope2000ATimeoutError,
    PicoScope2000AValidationError,
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

__version__ = "26.1"

__all__ = [
    "AWGSettings",
    "Channel",
    "ChannelSettings",
    "ConnectionState",
    "Coupling",
    "InstrumentIdentity",
    "MeasurementType",
    "Measurements",
    "PicoScope2000A",
    "PicoScope2000AConnectionError",
    "PicoScope2000ADeviceError",
    "PicoScope2000AError",
    "PicoScope2000ATimeoutError",
    "PicoScope2000AValidationError",
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

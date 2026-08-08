"""Typed core driver for SLCAN (serial-line CAN) interface adapters.

Framework-agnostic (no Robot Framework dependency): ``driver.py`` owns SLCAN
command construction/parsing and the background reader thread that makes
receiving unsolicited CAN frames possible; ``transport.py``/``simulator.py``
provide the real-serial and simulated backends; ``evidence.py`` is the
optional RFDS-008 structured-logging/diagnostics engine both this package and
the Robot Framework adapter (``rf_slcan``) use. See ``docs/logging_and_evidence.md``.
"""

from .driver import SlcanAdapter
from .enums import Bitrate, ChannelMode
from .exceptions import (
    SlcanBusError,
    SlcanConfigurationError,
    SlcanConnectionError,
    SlcanDeviceError,
    SlcanError,
    SlcanProtocolError,
    SlcanTimeoutError,
    SlcanValidationError,
)
from .models import AdapterIdentity, AdapterStatus, CanFrame, ConnectionState
from .simulator import SimSlcanAdapter

__version__ = "26.2"

__all__ = [
    "AdapterIdentity",
    "AdapterStatus",
    "Bitrate",
    "CanFrame",
    "ChannelMode",
    "ConnectionState",
    "SimSlcanAdapter",
    "SlcanAdapter",
    "SlcanBusError",
    "SlcanConfigurationError",
    "SlcanConnectionError",
    "SlcanDeviceError",
    "SlcanError",
    "SlcanProtocolError",
    "SlcanTimeoutError",
    "SlcanValidationError",
    "__version__",
]

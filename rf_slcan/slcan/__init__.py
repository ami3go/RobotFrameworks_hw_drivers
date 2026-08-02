"""Typed core driver for SLCAN (serial-line CAN) interface adapters."""

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

__version__ = "26.1"

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

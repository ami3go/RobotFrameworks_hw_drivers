"""RFDS-007 exception hierarchy for the SLCAN core driver.

Every exception is rooted in :class:`SlcanError`. Nothing in this package
raises a bare built-in exception at a public boundary.
"""

from __future__ import annotations


class SlcanError(Exception):
    """Base class for all errors raised by :mod:`slcan`."""


class SlcanConfigurationError(SlcanError):
    """A connection or driver configuration value is invalid."""


class SlcanValidationError(SlcanError):
    """A keyword/method argument failed validation before any device I/O."""


class SlcanConnectionError(SlcanError):
    """The transport could not be opened, or is not open when required."""


class SlcanTimeoutError(SlcanError):
    """A command acknowledgement or received frame did not arrive in time."""


class SlcanProtocolError(SlcanError):
    """A line from the adapter was malformed or inconsistent with the protocol."""


class SlcanDeviceError(SlcanError):
    """The adapter rejected a command (BEL/NACK response)."""


class SlcanBusError(SlcanError):
    """The CAN bus itself reports a fault (bus-off, error-passive, arbitration
    lost) via the adapter's status flags.

    Distinct from :class:`SlcanDeviceError`: this is a bus condition, not a
    rejection of the command that was just sent.
    """

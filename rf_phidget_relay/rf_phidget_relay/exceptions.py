"""Driver-specific exception hierarchy for the Phidget relay library.

Every exception is rooted in :class:`PhidgetRelayError` (RFDS-007) while also
inheriting the closest matching built-in so existing ``except ValueError`` /
``except RuntimeError`` / ``except AssertionError`` callers keep working
unchanged. This mirrors the ``BK8500VerificationError(BK8500Error,
AssertionError)`` pattern already used in ``rf_bk8500_load``.
"""

from __future__ import annotations


class PhidgetRelayError(Exception):
    """Base class for all errors raised by :mod:`rf_phidget_relay`."""


class PhidgetRelayDependencyError(PhidgetRelayError, RuntimeError):
    """A required dependency (the Phidget22 SDK) is not available."""


class PhidgetRelayConfigurationError(PhidgetRelayError, ValueError):
    """Connection-time configuration (serial numbers, timeout) is invalid."""


class PhidgetRelayValidationError(PhidgetRelayError, ValueError):
    """A keyword argument value is invalid."""


class PhidgetRelayArgumentTypeError(PhidgetRelayError, TypeError):
    """A keyword argument has the wrong type."""


class PhidgetRelayStateError(PhidgetRelayError, RuntimeError):
    """The relay bank is not in the required connection state for this call."""


class PhidgetRelayHardwareError(PhidgetRelayError, RuntimeError):
    """The Phidget22 SDK reported a failure while attaching or writing an output."""


class PhidgetRelayVerificationError(PhidgetRelayError, AssertionError):
    """A ``Relay Should Be Open/Closed`` verification keyword failed."""

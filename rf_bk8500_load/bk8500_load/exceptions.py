"""Error catalogue for the BK8500 driver.

Every exception raised by the driver or the Robot Framework library derives
from :class:`BK8500Error`, so a test can catch the whole family. The class
names are stable API and are referenced by ``ai/ai_contract.yaml``.
"""

from __future__ import annotations


class BK8500Error(Exception):
    """Base class for all driver errors."""


class BK8500ConfigurationError(BK8500Error):
    """Driver configured with an unusable port, model or baud rate."""


class BK8500ConnectionError(BK8500Error):
    """Serial port could not be opened, or is not open when required."""


class BK8500TimeoutError(BK8500Error):
    """No response, or a short response, within the configured timeout."""


class BK8500ProtocolError(BK8500Error):
    """A frame was received but is malformed (start byte, checksum, length)."""


class BK8500CommandError(BK8500Error):
    """The instrument rejected the command with a non-success status byte."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class BK8500ValidationError(BK8500Error):
    """A parameter was rejected by the driver before it reached the wire."""


class BK8500StateError(BK8500Error):
    """The requested operation is not legal in the current instrument state."""


class BK8500SafetyError(BK8500Error):
    """A safety rule of the driver would be violated by this operation."""


class BK8500ProtectionError(BK8500Error):
    """The instrument reports an active protection fault (OV/OC/OP/OT/reverse)."""

    def __init__(self, message: str, faults: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.faults = faults


class BK8500VerificationError(BK8500Error, AssertionError):
    """A verification keyword's pass/fail oracle evaluated to fail.

    Derives from :class:`AssertionError` so Robot Framework reports it as a
    normal test failure rather than an unexpected driver error.
    """

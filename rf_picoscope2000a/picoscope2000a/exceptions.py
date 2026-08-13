"""RFDS-007-style exception hierarchy for the PicoScope 2000A core driver.

Every exception is rooted in :class:`PicoScope2000AError`. Nothing in this
package raises a bare built-in exception at a public boundary.
"""

from __future__ import annotations


class PicoScope2000AError(Exception):
    """Base class for all errors raised by :mod:`picoscope2000a`."""


class PicoScope2000AValidationError(PicoScope2000AError):
    """A keyword/method argument failed validation before any device I/O."""


class PicoScope2000AConnectionError(PicoScope2000AError):
    """The backend could not be opened, or is not open when required."""


class PicoScope2000ADeviceError(PicoScope2000AError):
    """The instrument (or SDK call) reported an error, or lacks a required capability."""


class PicoScope2000ATimeoutError(PicoScope2000AError):
    """A block capture did not become ready within its timeout."""

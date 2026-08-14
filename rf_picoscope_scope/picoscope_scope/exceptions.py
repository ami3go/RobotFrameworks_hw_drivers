"""RFDS-007-style exception hierarchy for the PicoScope core driver.

Every exception is rooted in :class:`PicoScopeError`. Nothing in this
package raises a bare built-in exception at a public boundary.
"""

from __future__ import annotations


class PicoScopeError(Exception):
    """Base class for all errors raised by :mod:`picoscope_scope`."""


class PicoScopeValidationError(PicoScopeError):
    """A keyword/method argument failed validation before any device I/O."""


class PicoScopeConnectionError(PicoScopeError):
    """The backend could not be opened, or is not open when required."""


class PicoScopeDeviceError(PicoScopeError):
    """The instrument (or SDK call) reported an error, or lacks a required capability."""


class PicoScopeTimeoutError(PicoScopeError):
    """A block capture did not become ready within its timeout."""

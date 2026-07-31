"""Driver exception hierarchy.

Exceptions carry a small immutable context mapping to make unattended logs useful
without exposing transport or lock objects.
"""
from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any


class BK8500BError(Exception):
    def __init__(
        self,
        message: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.context = MappingProxyType(dict(context or {}))


class ConfigurationError(BK8500BError):
    pass


class InvalidStateTransitionError(BK8500BError):
    pass


class LockTimeoutError(BK8500BError):
    pass


class UnsupportedModelError(BK8500BError):
    pass


class UnsupportedFeatureError(BK8500BError):
    pass


class TransportError(BK8500BError):
    pass


class PortBusyError(TransportError):
    pass


class ConnectionLostError(TransportError):
    pass


class ReadTimeoutError(TransportError):
    pass


class WriteTimeoutError(TransportError):
    pass


class ProtocolError(BK8500BError):
    pass


class SCPIProtocolError(ProtocolError):
    pass


class LegacyProtocolError(ProtocolError):
    pass


class ChecksumError(LegacyProtocolError):
    pass


class FrameSyncError(LegacyProtocolError):
    pass


class MalformedResponseError(ProtocolError):
    pass


class ResponseTooLargeError(ProtocolError):
    pass


class DeviceError(BK8500BError):
    pass


class SCPICommandError(DeviceError):
    pass


class ProtectionTrippedError(DeviceError):
    pass


class DeviceRejectedCommandError(DeviceError):
    pass


class InstrumentRangeError(BK8500BError):
    pass


class UnsafeOperationError(BK8500BError):
    pass


class IndeterminateCommandOutcome(BK8500BError):
    """The driver cannot prove whether a state-changing command took effect."""

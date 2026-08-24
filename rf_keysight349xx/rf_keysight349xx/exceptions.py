"""Stable public driver exception hierarchy.

The public names follow RFDS-002 v1.1.  Errors carry a stable code and structured
context while preserving normal Python exception chaining.
"""
from __future__ import annotations

from typing import Any


class DriverError(Exception):
    default_code = "RFDS-INT-001"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        operation: str | None = None,
        alias: str | None = None,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code or self.default_code
        self.operation = operation
        self.alias = alias
        self.retryable = bool(retryable)
        self.details = dict(details or {})
        super().__init__(f"[{self.code}] {message}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "category": type(self).__name__,
            "message": str(self),
            "operation": self.operation,
            "alias": self.alias,
            "retryable": self.retryable,
            "details": dict(self.details),
        }


class DriverValidationError(DriverError):
    default_code = "RFDS-ARG-005"


class DriverStateError(DriverError):
    default_code = "RFDS-STA-002"


class DriverConnectionError(DriverError):
    default_code = "RFDS-CON-001"


class DriverTimeoutError(DriverConnectionError):
    default_code = "RFDS-TMO-001"


class DriverProtocolError(DriverError):
    default_code = "RFDS-PRT-001"


class DriverResponseError(DriverProtocolError):
    default_code = "RFDS-PRT-003"


class DriverDeviceError(DriverError):
    default_code = "RFDS-DEV-002"


class DriverSafetyError(DriverError):
    default_code = "RFDS-SAF-001"


class DriverNotSupportedError(DriverError):
    default_code = "RFDS-DEV-004"


class DriverConcurrencyError(DriverError):
    default_code = "RFDS-RES-002"

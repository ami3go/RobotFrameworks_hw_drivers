"""Canonical RFDS driver exception hierarchy.

Every public failure carries a stable code and JSON-compatible context.  The
string representation follows RFDS-007 so Robot Framework receives an
immediately actionable message without a Python traceback.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class DriverError(Exception):
    """Root of every public driver exception."""

    default_code = "RFDS-INT-002"
    default_retryable = False
    default_recovery: str | None = None

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        retryable: bool | None = None,
        severity: str = "ERROR",
        details: Mapping[str, object] | None = None,
        recovery_action: str | None = None,
        operation: str | None = None,
        keyword: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.code = code or self.default_code
        self.message = str(message)
        self.retryable = self.default_retryable if retryable is None else bool(retryable)
        self.severity = severity
        self.details = dict(details or {})
        self.recovery_action = recovery_action if recovery_action is not None else self.default_recovery
        self.operation = operation
        self.keyword = keyword
        self.cause = cause
        super().__init__(self.to_robot_message())
        if cause is not None:
            self.__cause__ = cause

    def to_robot_message(self) -> str:
        operation = self.keyword or self.operation or "Driver operation"
        context = "; ".join(f"{key}={value}" for key, value in sorted(self.details.items()))
        context_text = f" {context}." if context else ""
        recovery = self.recovery_action or "none"
        retryable = "yes" if self.retryable else "no"
        return (
            f"[{self.code}] {operation} failed: {self.message}.{context_text} "
            f"Retryable={retryable}. Recovery={recovery}."
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "severity": self.severity,
            "details": dict(self.details),
            "recovery_action": self.recovery_action,
            "operation": self.operation,
            "keyword": self.keyword,
            "cause_type": None if self.cause is None else type(self.cause).__name__,
            "cause_message": None if self.cause is None else str(self.cause),
        }

    def __str__(self) -> str:
        return self.to_robot_message()


class DriverConfigurationError(DriverError):
    default_code = "RFDS-CFG-002"


class DriverValidationError(DriverError):
    default_code = "RFDS-ARG-005"


class DriverArgumentTypeError(DriverValidationError):
    default_code = "RFDS-ARG-001"


class DriverArgumentValueError(DriverValidationError):
    default_code = "RFDS-ARG-002"


class DriverRangeError(DriverValidationError):
    default_code = "RFDS-ARG-003"


class DriverUnsupportedValueError(DriverValidationError):
    default_code = "RFDS-ARG-004"


class DriverStateError(DriverError):
    default_code = "RFDS-STA-002"


class DriverPreconditionError(DriverStateError):
    default_code = "RFDS-STA-001"


class DriverOperationUncertainError(DriverStateError):
    default_code = "RFDS-STA-003"


class DriverConnectionError(DriverError):
    default_code = "RFDS-CON-002"
    default_retryable = True
    default_recovery = "verify the endpoint and reconnect"


class DriverTransportError(DriverError):
    default_code = "RFDS-TRN-004"
    default_retryable = True


class DriverTransportOpenError(DriverConnectionError):
    default_code = "RFDS-CON-001"


class DriverTransportClosedError(DriverTransportError):
    default_code = "RFDS-TRN-003"


class DriverWriteError(DriverTransportError):
    default_code = "RFDS-TRN-001"


class DriverReadError(DriverTransportError):
    default_code = "RFDS-TRN-002"


class DriverTimeoutError(DriverTransportError, TimeoutError):
    default_code = "RFDS-TMO-001"


class DriverProtocolError(DriverError):
    default_code = "RFDS-PRT-003"


class DriverMalformedResponseError(DriverProtocolError):
    default_code = "RFDS-PRT-001"


class DriverIncompleteResponseError(DriverProtocolError):
    default_code = "RFDS-PRT-002"


class DriverUnexpectedResponseError(DriverProtocolError):
    default_code = "RFDS-PRT-003"


class DriverChecksumError(DriverProtocolError):
    default_code = "RFDS-PRT-004"


class DriverProtocolSyncError(DriverProtocolError):
    default_code = "RFDS-PRT-005"


class DriverDeviceError(DriverError):
    default_code = "RFDS-DEV-002"


class DriverCommandRejectedError(DriverDeviceError):
    default_code = "RFDS-DEV-001"


class DriverDeviceBusyError(DriverDeviceError):
    default_code = "RFDS-DEV-003"
    default_retryable = True


class DriverUnsupportedOperationError(DriverDeviceError):
    default_code = "RFDS-DEV-004"


class DriverIdentityError(DriverDeviceError):
    default_code = "RFDS-DEV-005"


class DriverResourceError(DriverError):
    default_code = "RFDS-RES-001"


class DriverResourceNotFoundError(DriverResourceError):
    default_code = "RFDS-RES-001"


class DriverResourceBusyError(DriverResourceError):
    default_code = "RFDS-RES-002"
    default_retryable = True


class DriverResourceConflictError(DriverResourceError):
    default_code = "RFDS-RES-003"


class DriverSafetyError(DriverError):
    default_code = "RFDS-SAF-001"


class DriverUnsafeOperationError(DriverSafetyError):
    default_code = "RFDS-SAF-001"


class DriverInterlockError(DriverSafetyError):
    default_code = "RFDS-SAF-002"


class DriverLimitViolationError(DriverSafetyError):
    default_code = "RFDS-SAF-003"


class DriverDependencyError(DriverError):
    default_code = "RFDS-DEP-001"


class DriverInternalError(DriverError):
    default_code = "RFDS-INT-002"


class DriverCancelledError(DriverError):
    default_code = "RFDS-STA-002"


class DriverCleanupError(DriverError):
    default_code = "RFDS-INT-001"

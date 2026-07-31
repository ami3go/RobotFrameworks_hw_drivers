"""Validated immutable configuration models."""
from __future__ import annotations

from dataclasses import dataclass, field
import math

from .enums import Protocol
from .exceptions import ConfigurationError


def _finite_positive(name: str, value: float, *, allow_zero: bool = False) -> None:
    if not math.isfinite(value):
        raise ConfigurationError(f"{name} must be finite", context={name: value})
    if value < 0 or (value == 0 and not allow_zero):
        op = "non-negative" if allow_zero else "positive"
        raise ConfigurationError(f"{name} must be {op}", context={name: value})


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_read_attempts: int = 2
    max_write_attempts: int = 1
    initial_backoff_s: float = 0.05
    maximum_backoff_s: float = 0.5
    jitter_fraction: float = 0.10

    def __post_init__(self) -> None:
        if self.max_read_attempts < 1:
            raise ConfigurationError("max_read_attempts must be >= 1")
        if self.max_write_attempts != 1:
            raise ConfigurationError(
                "max_write_attempts must remain 1; blind write retries are prohibited"
            )
        _finite_positive("initial_backoff_s", self.initial_backoff_s, allow_zero=True)
        _finite_positive("maximum_backoff_s", self.maximum_backoff_s, allow_zero=True)
        if self.maximum_backoff_s < self.initial_backoff_s:
            raise ConfigurationError("maximum_backoff_s must be >= initial_backoff_s")
        if not math.isfinite(self.jitter_fraction) or not 0 <= self.jitter_fraction <= 1:
            raise ConfigurationError("jitter_fraction must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class ReconnectPolicy:
    enabled: bool = False
    max_attempts: int = 3
    total_deadline_s: float = 15.0
    require_serial_match: bool = True
    restore_configuration: bool = False

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ConfigurationError("max_attempts must be >= 1")
        _finite_positive("total_deadline_s", self.total_deadline_s)


@dataclass(frozen=True, slots=True)
class SafetyPolicy:
    require_off_before_reconfiguration: bool = True
    verify_critical_writes: bool = True
    block_unknown_model_hazards: bool = True
    require_enable_token: bool = False
    turn_input_off_on_close: bool = True
    allow_short: bool = False
    allow_broadcast_writes: bool = False


@dataclass(frozen=True, slots=True)
class DriverConfig:
    port: str
    protocol: Protocol = Protocol.SCPI
    address: int = 0
    baud_rate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    stopbits: float = 1
    dtr: bool = True
    rts: bool = True
    connect_timeout_s: float = 3.0
    read_timeout_s: float = 2.0
    write_timeout_s: float = 2.0
    query_timeout_s: float = 2.0
    long_operation_timeout_s: float = 120.0
    lock_timeout_s: float = 5.0
    close_timeout_s: float = 5.0
    minimum_command_interval_s: float = 0.02
    scpi_write_terminator: bytes = b"\n"
    scpi_read_terminator: bytes = b"\n"
    maximum_scpi_response_bytes: int = 4096
    maximum_error_queue_entries: int = 32
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    reconnect: ReconnectPolicy = field(default_factory=ReconnectPolicy)
    safety: SafetyPolicy = field(default_factory=SafetyPolicy)

    def __post_init__(self) -> None:
        if not isinstance(self.port, str) or not self.port.strip():
            raise ConfigurationError("port must be a non-empty string")
        if not isinstance(self.protocol, Protocol):
            try:
                object.__setattr__(self, "protocol", Protocol(self.protocol))
            except (TypeError, ValueError) as exc:
                raise ConfigurationError("invalid protocol") from exc
        if not 0 <= self.address <= 31:
            raise ConfigurationError("address must be in [0, 31]")
        if self.baud_rate <= 0:
            raise ConfigurationError("baud_rate must be positive")
        if self.bytesize not in (5, 6, 7, 8):
            raise ConfigurationError("bytesize must be 5, 6, 7, or 8")
        if self.parity.upper() not in {"N", "E", "O", "M", "S"}:
            raise ConfigurationError("parity must be N, E, O, M, or S")
        if self.stopbits not in (1, 1.5, 2):
            raise ConfigurationError("stopbits must be 1, 1.5, or 2")
        for name in (
            "connect_timeout_s",
            "read_timeout_s",
            "write_timeout_s",
            "query_timeout_s",
            "long_operation_timeout_s",
            "lock_timeout_s",
            "close_timeout_s",
        ):
            _finite_positive(name, float(getattr(self, name)))
        _finite_positive(
            "minimum_command_interval_s",
            self.minimum_command_interval_s,
            allow_zero=True,
        )
        for name in ("scpi_write_terminator", "scpi_read_terminator"):
            term = getattr(self, name)
            if not isinstance(term, bytes) or not 1 <= len(term) <= 4:
                raise ConfigurationError(f"{name} must be 1 to 4 bytes")
        if self.maximum_scpi_response_bytes < 16:
            raise ConfigurationError("maximum_scpi_response_bytes must be >= 16")
        if not 1 <= self.maximum_error_queue_entries <= 1024:
            raise ConfigurationError("maximum_error_queue_entries must be in [1, 1024]")

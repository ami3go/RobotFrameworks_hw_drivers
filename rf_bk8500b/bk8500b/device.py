"""Canonical synchronous high-level driver for B&K Precision 8500B loads."""
from __future__ import annotations

from datetime import datetime, timezone
import math
import time
from typing import Any

from .capabilities import build_capabilities, known_model
from .config import DriverConfig
from .diagnostics import AuditSink, MetricsSink
from .enums import (
    CommandOutcome,
    DynamicMode,
    OperatingMode,
    ProtectionFlag,
    Protocol,
    RiskClass,
    SessionState,
    TriggerEdge,
)
from .exceptions import (
    BK8500BError,
    ConfigurationError,
    IndeterminateCommandOutcome,
    InstrumentRangeError,
    InvalidStateTransitionError,
    MalformedResponseError,
    ProtectionTrippedError,
    UnsupportedFeatureError,
    UnsupportedModelError,
    UnsafeOperationError,
)
from .execution import CommandExecutor
from .measurements import (
    AppliedSetpoint,
    InstrumentCapabilities,
    InstrumentIdentity,
    LEDConfig,
    ListConfig,
    ListRunResult,
    Measurement,
    OCPTestConfig,
    OCPTestResult,
    SafeEnableConfig,
    SafetyToken,
    SCPIErrorEntry,
    SelfTestResult,
    SlewRate,
    TimingTestConfig,
    TimingTestResult,
    TransientConfig,
)
from .protocol import LegacyProtocol, SCPICommand, SCPIProtocol, decode_frame
from .protocol.scpi import format_number, parse_bool, parse_error, parse_float, parse_identity, parse_int
from .state_machine import SessionStateMachine
from .status import DiagnosticSnapshot, DeviceStatus, HealthReport, MeasurementSnapshot, SafeEnableResult
from .transport import SerialTransport, Transport


class BK8500B:
    def __init__(
        self,
        config: DriverConfig,
        *,
        transport: Transport | None = None,
        audit_sink: AuditSink | None = None,
        metrics_sink: MetricsSink | None = None,
    ) -> None:
        if not isinstance(config, DriverConfig):
            raise ConfigurationError("config must be a DriverConfig instance")
        self.config = config
        self._transport = transport or SerialTransport(config)
        self._executor = CommandExecutor(
            config,
            self._transport,
            audit_sink=audit_sink,
            metrics_sink=metrics_sink,
        )
        self._scpi = SCPIProtocol(config, self._executor)
        self._legacy = LegacyProtocol(config, self._executor)
        self._states = SessionStateMachine()
        self._active_protocol = config.protocol
        self._identity: InstrumentIdentity | None = None
        self._capabilities: InstrumentCapabilities | None = None
        self._status_cache: DeviceStatus | None = None
        self._last_error: str | None = None
        self._consecutive_health_failures = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def connect(self) -> None:
        if self.session_state is not SessionState.DISCONNECTED:
            if self.connected and self._identity is not None:
                return
            raise InvalidStateTransitionError(
                "connect() requires DISCONNECTED state",
                context={"state": self.session_state.value},
            )
        self._states.transition(SessionState.CONNECTING)
        try:
            self._transport.open()
            self._states.transition(SessionState.IDENTIFYING)
            if self.config.protocol is Protocol.AUTO:
                self._active_protocol = self._auto_detect_protocol()
            else:
                self._active_protocol = self.config.protocol
            if self._active_protocol is Protocol.SCPI:
                self._identity = self._identify_scpi()
                self._capabilities = build_capabilities(self._identity, Protocol.SCPI)
                self._states.transition(SessionState.CONNECTED_UNSYNCHRONIZED)
                self.synchronize_state()
            elif self._active_protocol is Protocol.LEGACY:
                rating_frame = self._legacy.read_ratings_experimental()
                self._identity = InstrumentIdentity(
                    manufacturer="B&K Precision",
                    model="8500B-series legacy",
                    serial_number="",
                    firmware_revision="",
                    raw=rating_frame.raw.hex(),
                )
                self._capabilities = build_capabilities(self._identity, Protocol.LEGACY)
                self._states.transition(SessionState.CONNECTED_UNSYNCHRONIZED)
                self._states.transition(SessionState.DEGRADED)
                self._last_error = (
                    "Legacy high-level control is blocked until response-layout HIL evidence exists"
                )
            else:
                raise ConfigurationError("Protocol.AUTO must resolve before use")
        except Exception as exc:
            self._last_error = f"{type(exc).__name__}: {exc}"
            try:
                self._states.fail()
            except InvalidStateTransitionError:
                pass
            try:
                self._transport.close()
            finally:
                if self.session_state is SessionState.FAILED:
                    self._states.transition(SessionState.CLOSING)
                    self._states.transition(SessionState.DISCONNECTED)
            raise

    def close(self) -> None:
        if self.session_state is SessionState.DISCONNECTED:
            return
        if self.session_state is not SessionState.CLOSING:
            self._states.transition(SessionState.CLOSING)
        try:
            if (
                self.config.safety.turn_input_off_on_close
                and self._transport.is_open
                and self._active_protocol is Protocol.SCPI
            ):
                try:
                    self._scpi.write(
                        SCPICommand(
                            "INPut OFF",
                            "close.input_off",
                            risk=RiskClass.HAZARDOUS,
                        ),
                        timeout_s=min(self.config.write_timeout_s, self.config.close_timeout_s),
                    )
                except BK8500BError as exc:
                    self._last_error = f"Best-effort close input-off failed: {exc}"
            self._transport.close()
            self._invalidate_cache()
            self._states.transition(SessionState.DISCONNECTED)
        except Exception:
            self._states.fail()
            raise

    def reconnect(self) -> None:
        policy = self.config.reconnect
        if not policy.enabled:
            raise InvalidStateTransitionError("Reconnect policy is disabled")
        if self.session_state not in {SessionState.CONNECTED_READY, SessionState.DEGRADED}:
            raise InvalidStateTransitionError(
                "reconnect() requires CONNECTED_READY or DEGRADED state"
            )
        old_identity = self._identity
        self._states.transition(SessionState.RECONNECTING)
        deadline = time.monotonic() + policy.total_deadline_s
        last_error: Exception | None = None
        for attempt in range(policy.max_attempts):
            if time.monotonic() >= deadline:
                break
            try:
                self._transport.close()
                self._transport.open()
                self._invalidate_cache()
                self._states.transition(SessionState.CONNECTED_UNSYNCHRONIZED)
                if self._active_protocol is Protocol.SCPI:
                    new_identity = self._identify_scpi()
                    if (
                        policy.require_serial_match
                        and old_identity is not None
                        and old_identity.serial_number
                        and new_identity.serial_number != old_identity.serial_number
                    ):
                        raise UnsupportedModelError(
                            "Reconnect reached a different instrument",
                            context={
                                "expected_serial": old_identity.serial_number,
                                "actual_serial": new_identity.serial_number,
                            },
                        )
                    self._identity = new_identity
                    self._capabilities = build_capabilities(new_identity, self._active_protocol)
                    self.synchronize_state()
                    return
                self._states.transition(SessionState.DEGRADED)
                return
            except Exception as exc:
                last_error = exc
                if self.session_state is SessionState.CONNECTED_UNSYNCHRONIZED:
                    self._states.transition(SessionState.DEGRADED)
                if self.session_state is SessionState.DEGRADED and attempt + 1 < policy.max_attempts:
                    self._states.transition(SessionState.RECONNECTING)
                time.sleep(min(0.5 * (2**attempt), max(0.0, deadline - time.monotonic())))
        self._states.fail()
        assert last_error is not None
        raise last_error

    def synchronize_state(self) -> DeviceStatus:
        if self.session_state not in {
            SessionState.CONNECTED_UNSYNCHRONIZED,
            SessionState.CONNECTED_READY,
            SessionState.DEGRADED,
        }:
            raise InvalidStateTransitionError("State synchronization is not allowed now")
        if self._active_protocol is not Protocol.SCPI:
            raise UnsupportedFeatureError("Legacy state synchronization awaits HIL evidence")
        status = self._read_device_status(synchronized=True)
        self._status_cache = status
        if self.session_state is not SessionState.CONNECTED_READY:
            self._states.transition(SessionState.CONNECTED_READY)
        return status

    def health_check(self) -> HealthReport:
        started = time.monotonic()
        try:
            self._require_connected()
            if self._active_protocol is Protocol.SCPI:
                self.read_status_byte()
            else:
                self._legacy.read_ratings_experimental()
            latency = time.monotonic() - started
            self._consecutive_health_failures = 0
            if self.session_state is SessionState.DEGRADED and self._active_protocol is Protocol.SCPI:
                self.synchronize_state()
            return HealthReport(
                healthy=True,
                session_state=self.session_state,
                identity=self._identity,
                latency_s=latency,
                consecutive_failures=0,
                message="Device responded",
            )
        except Exception as exc:
            self._consecutive_health_failures += 1
            self._last_error = f"{type(exc).__name__}: {exc}"
            if (
                self._consecutive_health_failures >= 3
                and self.session_state is SessionState.CONNECTED_READY
            ):
                self._states.transition(SessionState.DEGRADED)
            return HealthReport(
                healthy=False,
                session_state=self.session_state,
                identity=self._identity,
                latency_s=None,
                consecutive_failures=self._consecutive_health_failures,
                message=str(exc),
            )

    def diagnostic_snapshot(self) -> DiagnosticSnapshot:
        partial = False
        notes: list[str] = []
        status = self._status_cache
        if self.connected and self._active_protocol is Protocol.SCPI:
            try:
                status = self.get_device_status()
            except Exception as exc:
                partial = True
                notes.append(f"status query failed: {type(exc).__name__}: {exc}")
        return DiagnosticSnapshot(
            created_utc=datetime.now(timezone.utc),
            session_state=self.session_state,
            protocol=self._active_protocol,
            connected=self.connected,
            identity=self._identity,
            status=status,
            last_error=self._last_error,
            counters=dict(self._executor.counters),
            partial=partial,
            notes=tuple(notes),
        )

    @property
    def connected(self) -> bool:
        return self._transport.is_open and self.session_state in {
            SessionState.IDENTIFYING,
            SessionState.CONNECTED_UNSYNCHRONIZED,
            SessionState.CONNECTED_READY,
            SessionState.DEGRADED,
            SessionState.RECONNECTING,
        }

    @property
    def session_state(self) -> SessionState:
        return self._states.state

    def __enter__(self) -> "BK8500B":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internal protocol helpers
    # ------------------------------------------------------------------
    def _auto_detect_protocol(self) -> Protocol:
        try:
            identity = self._identify_scpi()
            self._identity = identity
            return Protocol.SCPI
        except BK8500BError as scpi_error:
            self._last_error = f"SCPI probe failed: {scpi_error}"
            self._transport.close()
            self._transport.open()
            self._transport.reset_input_buffer()
            try:
                self._legacy.read_ratings_experimental()
                return Protocol.LEGACY
            except BK8500BError as legacy_error:
                raise MalformedResponseError(
                    "Protocol auto-detection failed",
                    context={"scpi": str(scpi_error), "legacy": str(legacy_error)},
                ) from legacy_error

    def _require_connected(self) -> None:
        if not self.connected:
            raise InvalidStateTransitionError(
                "Operation requires an open connected session",
                context={"state": self.session_state.value},
            )

    def _require_ready(self, *, hazardous: bool = False) -> None:
        if self.session_state is not SessionState.CONNECTED_READY:
            raise InvalidStateTransitionError(
                "Device-control operation requires CONNECTED_READY",
                context={"state": self.session_state.value},
            )
        if self._active_protocol is not Protocol.SCPI:
            raise UnsupportedFeatureError(
                "Stable high-level legacy control is blocked pending HIL evidence"
            )
        if hazardous and self.config.safety.block_unknown_model_hazards:
            if self._identity is None or not known_model(self._identity.model):
                raise UnsupportedModelError(
                    "Hazardous operation blocked for an unknown model",
                    context={"model": None if self._identity is None else self._identity.model},
                )

    def _ensure_off_for_reconfiguration(self) -> None:
        if (
            self.config.safety.require_off_before_reconfiguration
            and self.get_input_enabled()
        ):
            raise UnsafeOperationError(
                "Input must be OFF before reconfiguration",
                context={"policy": "require_off_before_reconfiguration"},
            )

    def _validate_token(self, token: SafetyToken | None, purpose: str, *, required: bool = True) -> None:
        if not required:
            return
        if token is None or not token.is_valid_for(purpose):
            raise UnsafeOperationError(
                f"A valid safety token for {purpose!r} is required"
            )

    def _cmd(
        self,
        text: str,
        operation: str,
        *,
        risk: RiskClass = RiskClass.CONFIGURATION,
        timeout_s: float | None = None,
    ) -> str:
        return self._scpi.write(
            SCPICommand(text, operation, risk=risk),
            timeout_s=timeout_s,
        )

    def _q_text(
        self,
        text: str,
        operation: str,
        *,
        timeout_s: float | None = None,
        retryable: bool = True,
        destructive: bool = False,
    ) -> str:
        return self._scpi.query_text(
            SCPICommand(
                text,
                operation,
                risk=RiskClass.READ_ONLY,
                is_query=True,
                retryable=retryable,
                destructive_read=destructive,
            ),
            timeout_s=timeout_s,
        )

    def _q_float(self, text: str, operation: str, **kwargs: Any) -> float:
        return parse_float(self._q_text(text, operation, **kwargs))

    def _q_int(self, text: str, operation: str, **kwargs: Any) -> int:
        return parse_int(self._q_text(text, operation, **kwargs))

    def _identify_scpi(self) -> InstrumentIdentity:
        raw = self._q_text("*IDN?", "identify", retryable=True)
        return parse_identity(raw)

    def _invalidate_cache(self) -> None:
        self._status_cache = None
        self._capabilities = None

    def _validate_setpoint(self, name: str, value: float, maximum: float | None) -> None:
        if not math.isfinite(value) or value < 0:
            raise InstrumentRangeError(f"{name} must be finite and non-negative")
        if maximum is not None and maximum > 0 and value > maximum:
            raise InstrumentRangeError(
                f"{name} exceeds instrument rating",
                context={"value": value, "maximum": maximum},
            )

    def _set_and_verify(
        self,
        *,
        command: str,
        query: str,
        operation: str,
        value: float,
        unit: str,
        maximum: float | None = None,
        verify: bool | None = None,
    ) -> AppliedSetpoint:
        self._require_ready()
        self._ensure_off_for_reconfiguration()
        self._validate_setpoint(operation, value, maximum)
        wire = format_number(value)
        self._cmd(f"{command} {wire}", operation)
        do_verify = self.config.safety.verify_critical_writes if verify is None else verify
        if do_verify:
            try:
                applied = self._q_float(query, f"{operation}.verify")
            except BK8500BError as exc:
                raise IndeterminateCommandOutcome(
                    f"{operation} was sent but readback verification failed",
                    context={"operation": operation, "requested": value},
                ) from exc
            tolerance = max(abs(value) * 1e-6, 1e-9)
            if abs(applied - value) > tolerance:
                raise MalformedResponseError(
                    f"Verification mismatch for {operation}",
                    context={"requested": value, "readback": applied},
                )
            return AppliedSetpoint(value, applied, unit, wire, True)
        return AppliedSetpoint(value, value, unit, wire, False)

    # ------------------------------------------------------------------
    # Identification and capabilities
    # ------------------------------------------------------------------
    def identify(self) -> InstrumentIdentity:
        self._require_connected()
        if self._identity is not None:
            return self._identity
        if self._active_protocol is Protocol.SCPI:
            self._identity = self._identify_scpi()
            return self._identity
        raise UnsupportedFeatureError("Legacy identity does not provide model/serial fields")

    def get_scpi_version(self) -> str:
        self._require_ready()
        return self._q_text("SYSTem:VERSion?", "system.version")

    def get_capabilities(self, *, refresh: bool = False) -> InstrumentCapabilities:
        self._require_connected()
        if refresh or self._capabilities is None:
            self._capabilities = build_capabilities(self.identify(), self._active_protocol)
        return self._capabilities

    # ------------------------------------------------------------------
    # Common and status operations
    # ------------------------------------------------------------------
    def clear_status(self) -> None:
        self._require_ready()
        self._cmd("*CLS", "common.clear_status")

    def set_event_status_enable(self, value: int) -> None:
        self._require_ready()
        if not 0 <= value <= 255:
            raise InstrumentRangeError("Event status enable must be in [0, 255]")
        self._cmd(f"*ESE {value}", "common.set_ese")

    def get_event_status_enable(self) -> int:
        self._require_ready()
        return parse_int(self._q_text("*ESE?", "common.get_ese"), minimum=0, maximum=255)

    def read_event_status_register(self) -> int:
        self._require_ready()
        return parse_int(
            self._q_text("*ESR?", "common.read_esr", retryable=False, destructive=True),
            minimum=0,
            maximum=255,
        )

    def operation_complete(self, *, timeout_s: float | None = None) -> None:
        self._require_ready()
        result = parse_int(
            self._q_text("*OPC?", "common.opc", timeout_s=timeout_s),
            minimum=0,
            maximum=1,
        )
        if result != 1:
            raise MalformedResponseError("*OPC? did not return 1")

    def is_operation_complete(self, *, timeout_s: float | None = None) -> bool:
        self.operation_complete(timeout_s=timeout_s)
        return True

    def set_power_on_status_clear(self, enabled: bool) -> None:
        self._require_ready()
        self._cmd(f"*PSC {1 if enabled else 0}", "common.set_psc")

    def get_power_on_status_clear(self) -> bool:
        self._require_ready()
        return parse_bool(self._q_text("*PSC?", "common.get_psc"))

    def save_state(self, slot: int) -> None:
        self._require_ready(hazardous=True)
        if not 0 <= slot <= 99:
            raise InstrumentRangeError("Save slot must be in [0, 99]")
        self._cmd(f"*SAV {slot}", "common.save_state", risk=RiskClass.HAZARDOUS)

    def recall_state(self, slot: int) -> None:
        self._require_ready(hazardous=True)
        if not 0 <= slot <= 9:
            raise InstrumentRangeError("Recall slot must be in [0, 9]")
        self._cmd(f"*RCL {slot}", "common.recall_state", risk=RiskClass.HAZARDOUS)
        self._status_cache = None
        self._states.transition(SessionState.DEGRADED)

    def reset_device(self) -> None:
        self._require_ready(hazardous=True)
        self._cmd("*RST", "common.reset", risk=RiskClass.HAZARDOUS)
        self._status_cache = None
        self._states.transition(SessionState.DEGRADED)

    def set_service_request_enable(self, value: int) -> None:
        self._require_ready()
        if not 0 <= value <= 255:
            raise InstrumentRangeError("Service request enable must be in [0, 255]")
        self._cmd(f"*SRE {value}", "common.set_sre")

    def get_service_request_enable(self) -> int:
        self._require_ready()
        return parse_int(self._q_text("*SRE?", "common.get_sre"), minimum=0, maximum=255)

    def read_status_byte(self) -> int:
        self._require_connected()
        return parse_int(self._q_text("*STB?", "common.read_stb"), minimum=0, maximum=255)

    def self_test(self, *, timeout_s: float | None = None) -> SelfTestResult:
        self._require_ready()
        raw = self._q_text(
            "*TST?",
            "common.self_test",
            timeout_s=self.config.long_operation_timeout_s if timeout_s is None else timeout_s,
            retryable=False,
        )
        code = parse_int(raw)
        return SelfTestResult(code=code, passed=code == 0, raw=raw)

    # ------------------------------------------------------------------
    # Input, mode, range, setpoint, and sense operations
    # ------------------------------------------------------------------
    def get_input_enabled(self) -> bool:
        self._require_connected()
        return parse_bool(self._q_text("INPut?", "input.get"))

    def set_input_enabled(self, enabled: bool, *, token: SafetyToken | None = None) -> None:
        self._require_ready(hazardous=enabled)
        if enabled and self.config.safety.require_enable_token:
            self._validate_token(token, "enable_input")
        self._cmd(
            f"INPut {'ON' if enabled else 'OFF'}",
            "input.enable" if enabled else "input.disable",
            risk=RiskClass.HAZARDOUS,
        )
        if self.config.safety.verify_critical_writes:
            try:
                actual = self.get_input_enabled()
            except BK8500BError as exc:
                raise IndeterminateCommandOutcome(
                    "Input state command was sent but verification failed",
                    context={"requested": enabled},
                ) from exc
            if actual is not enabled:
                raise MalformedResponseError(
                    "Input state verification failed",
                    context={"requested": enabled, "actual": actual},
                )
        self._status_cache = None

    def get_short_enabled(self) -> bool:
        self._require_connected()
        return parse_bool(self._q_text("INPut:SHORt?", "short.get"))

    def set_short_enabled(self, enabled: bool, *, token: SafetyToken) -> None:
        self._require_ready(hazardous=True)
        if not self.config.safety.allow_short:
            raise UnsafeOperationError("Short-circuit mode is disabled by SafetyPolicy")
        self._validate_token(token, "enable_short")
        self._cmd(
            f"INPut:SHORt {'ON' if enabled else 'OFF'}",
            "short.enable" if enabled else "short.disable",
            risk=RiskClass.HAZARDOUS,
        )
        if self.config.safety.verify_critical_writes:
            try:
                actual = self.get_short_enabled()
            except BK8500BError as exc:
                raise IndeterminateCommandOutcome(
                    "Short-circuit command was sent but verification failed",
                    context={"requested": enabled},
                ) from exc
            if actual is not enabled:
                raise MalformedResponseError("Short-circuit state verification failed")

    def get_operating_mode(self) -> OperatingMode:
        self._require_connected()
        return OperatingMode.from_response(self._q_text("FUNCtion?", "mode.get"))

    def set_operating_mode(self, mode: OperatingMode) -> None:
        self._require_ready()
        self._ensure_off_for_reconfiguration()
        if not isinstance(mode, OperatingMode):
            raise TypeError("mode must be OperatingMode")
        self._cmd(f"FUNCtion {mode.scpi_token}", "mode.set")
        if self.config.safety.verify_critical_writes and self.get_operating_mode() is not mode:
            raise MalformedResponseError("Operating mode verification failed")

    def get_current_setpoint(self) -> float:
        self._require_connected()
        return self._q_float("CURRent?", "current.get")

    def set_current_setpoint(self, amperes: float) -> AppliedSetpoint:
        cap = self.get_capabilities()
        return self._set_and_verify(command="CURRent", query="CURRent?", operation="current.set", value=amperes, unit="A", maximum=cap.maximum_current_a)

    def get_voltage_setpoint(self) -> float:
        self._require_connected()
        return self._q_float("VOLTage?", "voltage.get")

    def set_voltage_setpoint(self, volts: float) -> AppliedSetpoint:
        cap = self.get_capabilities()
        return self._set_and_verify(command="VOLTage", query="VOLTage?", operation="voltage.set", value=volts, unit="V", maximum=cap.maximum_voltage_v)

    def get_power_setpoint(self) -> float:
        self._require_connected()
        return self._q_float("POWer?", "power.get")

    def set_power_setpoint(self, watts: float) -> AppliedSetpoint:
        cap = self.get_capabilities()
        return self._set_and_verify(command="POWer", query="POWer?", operation="power.set", value=watts, unit="W", maximum=cap.maximum_power_w)

    def get_resistance_setpoint(self) -> float:
        self._require_connected()
        return self._q_float("RESistance?", "resistance.get")

    def set_resistance_setpoint(self, ohms: float) -> AppliedSetpoint:
        return self._set_and_verify(command="RESistance", query="RESistance?", operation="resistance.set", value=ohms, unit="ohm")

    def get_current_range(self) -> float:
        self._require_connected()
        return self._q_float("CURRent:RANGe?", "current_range.get")

    def set_current_range(self, amperes: float) -> AppliedSetpoint:
        cap = self.get_capabilities()
        return self._set_and_verify(command="CURRent:RANGe", query="CURRent:RANGe?", operation="current_range.set", value=amperes, unit="A", maximum=cap.maximum_current_a)

    def get_voltage_range(self) -> float:
        self._require_connected()
        return self._q_float("VOLTage:RANGe?", "voltage_range.get")

    def set_voltage_range(self, volts: float) -> AppliedSetpoint:
        cap = self.get_capabilities()
        return self._set_and_verify(command="VOLTage:RANGe", query="VOLTage:RANGe?", operation="voltage_range.set", value=volts, unit="V", maximum=cap.maximum_voltage_v)

    def get_voltage_autorange(self) -> bool:
        self._require_connected()
        return parse_bool(self._q_text("VOLTage:RANGe:AUTO?", "voltage_autorange.get"))

    def set_voltage_autorange(self, enabled: bool) -> None:
        self._require_ready()
        self._ensure_off_for_reconfiguration()
        self._cmd(f"VOLTage:RANGe:AUTO {'ON' if enabled else 'OFF'}", "voltage_autorange.set")
        if self.config.safety.verify_critical_writes and self.get_voltage_autorange() is not enabled:
            raise MalformedResponseError("Voltage autorange verification failed")

    def get_current_slew(self) -> SlewRate:
        self._require_connected()
        return SlewRate(
            rise_a_per_us=self._q_float("CURRent:SLEW:RISE?", "slew.get_rise"),
            fall_a_per_us=self._q_float("CURRent:SLEW:FALL?", "slew.get_fall"),
        )

    def set_current_slew(self, value: float) -> AppliedSetpoint:
        return self._set_and_verify(command="CURRent:SLEW", query="CURRent:SLEW?", operation="slew.set_both", value=value, unit="A/us")

    def set_current_slew_rise(self, value: float) -> AppliedSetpoint:
        return self._set_and_verify(command="CURRent:SLEW:RISE", query="CURRent:SLEW:RISE?", operation="slew.set_rise", value=value, unit="A/us")

    def set_current_slew_fall(self, value: float) -> AppliedSetpoint:
        return self._set_and_verify(command="CURRent:SLEW:FALL", query="CURRent:SLEW:FALL?", operation="slew.set_fall", value=value, unit="A/us")

    def get_remote_sense(self) -> bool:
        self._require_connected()
        return parse_bool(self._q_text("SYSTem:SENSe?", "remote_sense.get"))

    def set_remote_sense(self, enabled: bool) -> None:
        self._require_ready()
        self._ensure_off_for_reconfiguration()
        self._cmd(f"SYSTem:SENSe {'ON' if enabled else 'OFF'}", "remote_sense.set")
        if self.config.safety.verify_critical_writes and self.get_remote_sense() is not enabled:
            raise MalformedResponseError("Remote-sense verification failed")

    def get_load_on_voltage(self) -> float:
        self._require_connected()
        return self._q_float("VOLTage:ON?", "load_on_voltage.get")

    def set_load_on_voltage(self, volts: float) -> AppliedSetpoint:
        cap = self.get_capabilities()
        return self._set_and_verify(command="VOLTage:ON", query="VOLTage:ON?", operation="load_on_voltage.set", value=volts, unit="V", maximum=cap.maximum_voltage_v)

    def get_load_off_voltage(self) -> float:
        self._require_connected()
        return self._q_float("VOLTage:OFF?", "load_off_voltage.get")

    def set_load_off_voltage(self, volts: float) -> AppliedSetpoint:
        cap = self.get_capabilities()
        return self._set_and_verify(command="VOLTage:OFF", query="VOLTage:OFF?", operation="load_off_voltage.set", value=volts, unit="V", maximum=cap.maximum_voltage_v)

    # ------------------------------------------------------------------
    # Measurements
    # ------------------------------------------------------------------
    def _measurement(self, command: str, operation: str, unit: str) -> Measurement:
        self._require_connected()
        raw = self._q_text(command, operation)
        return Measurement.now(parse_float(raw), unit, self._active_protocol, raw=raw)

    def measure_voltage(self) -> Measurement:
        return self._measurement("MEASure:VOLTage?", "measure.voltage", "V")

    def measure_voltage_maximum(self) -> Measurement:
        return self._measurement("MEASure:VOLTage:MAXimum?", "measure.voltage_max", "V")

    def measure_voltage_minimum(self) -> Measurement:
        return self._measurement("MEASure:VOLTage:MINimum?", "measure.voltage_min", "V")

    def measure_voltage_peak_to_peak(self) -> Measurement:
        return self._measurement("MEASure:VOLTage:PTPeak?", "measure.voltage_ptp", "V")

    def measure_current(self) -> Measurement:
        return self._measurement("MEASure:CURRent?", "measure.current", "A")

    def measure_current_maximum(self) -> Measurement:
        return self._measurement("MEASure:CURRent:MAXimum?", "measure.current_max", "A")

    def measure_current_minimum(self) -> Measurement:
        return self._measurement("MEASure:CURRent:MINimum?", "measure.current_min", "A")

    def measure_current_peak_to_peak(self) -> Measurement:
        return self._measurement("MEASure:CURRent:PTPeak?", "measure.current_ptp", "A")

    def measure_power(self) -> Measurement:
        return self._measurement("MEASure:POWer?", "measure.power", "W")

    def measure_resistance(self) -> Measurement:
        return self._measurement("MEASure:RESistance?", "measure.resistance", "ohm")

    def measure_all(self) -> MeasurementSnapshot:
        status: DeviceStatus | None
        try:
            status = self.get_device_status()
        except BK8500BError:
            status = None
        resistance: Measurement | None
        try:
            resistance = self.measure_resistance()
        except BK8500BError:
            resistance = None
        return MeasurementSnapshot(
            voltage=self.measure_voltage(),
            current=self.measure_current(),
            power=self.measure_power(),
            resistance=resistance,
            status=status,
        )

    # ------------------------------------------------------------------
    # Compound safe enable
    # ------------------------------------------------------------------
    def configure_and_enable(
        self,
        config: SafeEnableConfig,
        *,
        token: SafetyToken | None = None,
    ) -> SafeEnableResult:
        self._require_ready(hazardous=True)
        if not isinstance(config, SafeEnableConfig):
            raise TypeError("config must be SafeEnableConfig")
        if self.config.safety.require_enable_token:
            self._validate_token(token, "enable_input")
        # Validate every unsupported/invalid field before the first write.
        if config.voltage_limit_v is not None:
            raise UnsupportedFeatureError(
                "SafeEnableConfig.voltage_limit_v has no verified generic SCPI protection command"
            )
        if config.resistance_limit_ohm is not None:
            raise UnsupportedFeatureError(
                "SafeEnableConfig.resistance_limit_ohm has no verified generic protection command"
            )
        caps = self.get_capabilities()
        maximum = {
            OperatingMode.CURRENT: caps.maximum_current_a,
            OperatingMode.VOLTAGE: caps.maximum_voltage_v,
            OperatingMode.POWER: caps.maximum_power_w,
            OperatingMode.RESISTANCE: None,
        }.get(config.mode)
        if config.mode not in {
            OperatingMode.CURRENT,
            OperatingMode.VOLTAGE,
            OperatingMode.POWER,
            OperatingMode.RESISTANCE,
        }:
            raise UnsupportedFeatureError("configure_and_enable supports fixed modes only")
        self._validate_setpoint("safe enable setpoint", config.setpoint, maximum)
        if config.current_limit_a is not None:
            self._validate_setpoint("current_limit_a", config.current_limit_a, caps.maximum_current_a)
        if config.power_limit_w is not None:
            self._validate_setpoint("power_limit_w", config.power_limit_w, caps.maximum_power_w)

        applied: AppliedSetpoint | None = None
        off_after_failure: bool | None = None
        try:
            if self.get_input_enabled():
                self.set_input_enabled(False)
            if config.current_limit_a is not None:
                self.set_current_protection(config.current_limit_a)
            if config.power_limit_w is not None:
                self.set_power_protection(config.power_limit_w)
            self.set_remote_sense(config.remote_sense)
            self.set_operating_mode(config.mode)
            setter = {
                OperatingMode.CURRENT: self.set_current_setpoint,
                OperatingMode.VOLTAGE: self.set_voltage_setpoint,
                OperatingMode.POWER: self.set_power_setpoint,
                OperatingMode.RESISTANCE: self.set_resistance_setpoint,
            }[config.mode]
            applied = setter(config.setpoint)
            status_before = self.get_device_status()
            if status_before.protection_flags:
                raise ProtectionTrippedError(
                    "Protection is active; input enable blocked",
                    context={"flags": int(status_before.protection_flags)},
                )
            self.set_input_enabled(True, token=token)
            status = self.get_device_status()
            if status.input_enabled is not True:
                raise MalformedResponseError("Input did not verify ON after safe enable")
            return SafeEnableResult(
                input_enabled=True,
                input_off_after_failure=None,
                applied_setpoint=applied,
                status=status,
                audit_event_id=self._executor.last_audit_event_id or "",
            )
        except Exception as exc:
            try:
                self._cmd("INPut OFF", "safe_enable.rollback_off", risk=RiskClass.HAZARDOUS)
                off_after_failure = not self.get_input_enabled()
            except Exception:
                off_after_failure = None
            if isinstance(exc, BK8500BError):
                raise type(exc)(
                    str(exc),
                    context={**dict(exc.context), "input_off_after_failure": off_after_failure},
                ) from exc
            raise

    # ------------------------------------------------------------------
    # Advanced configurations
    # ------------------------------------------------------------------
    def configure_transient(self, config: TransientConfig) -> None:
        self._require_ready()
        self._ensure_off_for_reconfiguration()
        if not isinstance(config, TransientConfig):
            raise TypeError("config must be TransientConfig")
        for name, value in (
            ("high_level", config.high_level),
            ("low_level", config.low_level),
            ("high_dwell_s", config.high_dwell_s),
            ("low_dwell_s", config.low_dwell_s),
            ("slew_a_per_us", config.slew_a_per_us),
        ):
            if not math.isfinite(value) or value < 0:
                raise InstrumentRangeError(f"{name} must be finite and non-negative")
        commands = (
            ("DYNamic:HIGH", config.high_level),
            ("DYNamic:HIGH:DWELl", config.high_dwell_s),
            ("DYNamic:LOW", config.low_level),
            ("DYNamic:LOW:DWELl", config.low_dwell_s),
            ("DYNamic:SLEW", config.slew_a_per_us),
        )
        for command, value in commands:
            self._cmd(f"{command} {format_number(value)}", f"transient.{command.lower()}")
        self._cmd(f"DYNamic:MODE {config.mode.value}", "transient.mode")

    def get_transient_config(self) -> TransientConfig:
        self._require_connected()
        mode_raw = self._q_text("DYNamic:MODE?", "transient.get_mode").upper()
        mode = next((item for item in DynamicMode if mode_raw.startswith(item.value[:4].upper())), None)
        if mode is None:
            raise MalformedResponseError("Unknown dynamic mode response", context={"raw": mode_raw})
        return TransientConfig(
            high_level=self._q_float("DYNamic:HIGH?", "transient.get_high"),
            high_dwell_s=self._q_float("DYNamic:HIGH:DWELl?", "transient.get_high_dwell"),
            low_level=self._q_float("DYNamic:LOW?", "transient.get_low"),
            low_dwell_s=self._q_float("DYNamic:LOW:DWELl?", "transient.get_low_dwell"),
            slew_a_per_us=self._q_float("DYNamic:SLEW?", "transient.get_slew"),
            mode=mode,
        )

    def configure_led(self, config: LEDConfig) -> None:
        self._require_ready()
        self._ensure_off_for_reconfiguration()
        if not 0.001 <= config.resistance_coefficient <= 1.0:
            raise InstrumentRangeError("LED resistance coefficient must be in [0.001, 1]")
        self._validate_setpoint("LED voltage", config.voltage_v, self.get_capabilities().maximum_voltage_v)
        self._validate_setpoint("LED current", config.current_a, self.get_capabilities().maximum_current_a)
        self._cmd(f"LED:VOLTage {format_number(config.voltage_v)}", "led.voltage")
        self._cmd(f"LED:CURRent {format_number(config.current_a)}", "led.current")
        self._cmd(f"LED:RCOeff {format_number(config.resistance_coefficient)}", "led.coefficient")

    def get_led_config(self) -> LEDConfig:
        self._require_connected()
        return LEDConfig(
            voltage_v=self._q_float("LED:VOLTage?", "led.get_voltage"),
            current_a=self._q_float("LED:CURRent?", "led.get_current"),
            resistance_coefficient=self._q_float("LED:RCOeff?", "led.get_coefficient"),
        )

    def configure_ocp_test(self, config: OCPTestConfig) -> None:
        self._require_ready()
        self._ensure_off_for_reconfiguration()
        caps = self.get_capabilities()
        self._validate_setpoint("OCP start", config.start_current_a, caps.maximum_current_a)
        self._validate_setpoint("OCP end", config.end_current_a, caps.maximum_current_a)
        if config.end_current_a < config.start_current_a:
            raise InstrumentRangeError("OCP end current must be >= start current")
        if not 1 <= config.steps <= 1000:
            raise InstrumentRangeError("OCP steps must be in [1, 1000]")
        if not math.isfinite(config.dwell_s) or not 0.00001 <= config.dwell_s <= 0.99999:
            raise InstrumentRangeError("OCP dwell must be in [0.00001, 0.99999] seconds")
        self._validate_setpoint("OCP trigger voltage", config.trigger_voltage_v, caps.maximum_voltage_v)
        for command, value in (
            ("OCP:ISTart", config.start_current_a),
            ("OCP:IEND", config.end_current_a),
            ("OCP:STEP", float(config.steps)),
            ("OCP:DWELl", config.dwell_s),
            ("OCP:VTRig", config.trigger_voltage_v),
        ):
            self._cmd(f"{command} {format_number(value)}", f"ocp.configure.{command.lower()}")

    def run_ocp_test(self, *, timeout_s: float | None = None) -> OCPTestResult:
        raise UnsupportedFeatureError(
            "OCP completion semantics are BLOCKED until hardware validation defines start/completion evidence"
        )

    def configure_timing_test(self, config: TimingTestConfig) -> None:
        self._require_ready()
        self._ensure_off_for_reconfiguration()
        if config.mode not in {
            OperatingMode.CURRENT,
            OperatingMode.VOLTAGE,
            OperatingMode.POWER,
            OperatingMode.RESISTANCE,
        }:
            raise UnsupportedFeatureError("Timing test supports fixed load modes only")
        if not all(math.isfinite(v) for v in (config.value, config.start_level, config.end_level)):
            raise InstrumentRangeError("Timing values must be finite")
        commands = (
            f"TIMing:LOAD:SETTing {'ON' if config.load_setting_enabled else 'OFF'}",
            f"TIMing:LOAD:MODE {config.mode.value}",
            f"TIMing:LOAD:VALue {format_number(config.value)}",
            f"TIMing:TSTart:SOURce {config.start_source.value}",
            f"TIMing:TSTart:EDGE {config.start_edge.value}",
            f"TIMing:TSTart:LEVel {format_number(config.start_level)}",
            f"TIMing:TEND:SOURce {config.end_source.value}",
            f"TIMing:TEND:EDGE {config.end_edge.value}",
            f"TIMing:TEND:LEVel {format_number(config.end_level)}",
        )
        for index, command in enumerate(commands):
            self._cmd(command, f"timing.configure.{index}")

    def run_timing_test(self, *, timeout_s: float | None = None) -> TimingTestResult:
        raise UnsupportedFeatureError(
            "Timing-test completion semantics are BLOCKED until HIL validation"
        )

    def configure_list(self, config: ListConfig) -> None:
        raise UnsupportedFeatureError(
            "Legacy list configuration is EXPERIMENTAL and blocked from the stable API until HIL validation"
        )

    def run_list(self, *, timeout_s: float | None = None) -> ListRunResult:
        raise UnsupportedFeatureError(
            "Legacy list execution is EXPERIMENTAL and blocked from the stable API until HIL validation"
        )

    def trigger(self) -> None:
        self._require_ready(hazardous=True)
        self._cmd("*TRG", "trigger", risk=RiskClass.NON_IDEMPOTENT)

    def clear_protection(self, *, token: SafetyToken) -> None:
        self._require_ready(hazardous=True)
        self._validate_token(token, "clear_protection")
        self._cmd("PROTection:CLEar", "protection.clear", risk=RiskClass.HAZARDOUS)
        self._status_cache = None

    # ------------------------------------------------------------------
    # Status and errors
    # ------------------------------------------------------------------
    @staticmethod
    def _decode_protection(condition: int) -> tuple[ProtectionFlag, int]:
        mapping = {
            0: ProtectionFlag.REVERSE_VOLTAGE,
            1: ProtectionFlag.OVER_CURRENT,
            3: ProtectionFlag.OVER_POWER,
            4: ProtectionFlag.OVER_TEMPERATURE,
            8: ProtectionFlag.REMOTE_SENSE_DISCONNECTED,
            11: ProtectionFlag.UNREGULATED,
            13: ProtectionFlag.OVER_VOLTAGE,
        }
        flags = ProtectionFlag.NONE
        known_mask = 0
        for bit, flag in mapping.items():
            known_mask |= 1 << bit
            if condition & (1 << bit):
                flags |= flag
        return flags, condition & ~known_mask

    def _read_device_status(self, *, synchronized: bool) -> DeviceStatus:
        input_enabled = self.get_input_enabled()
        short_enabled = self.get_short_enabled()
        mode = self.get_operating_mode()
        status_byte = self.read_status_byte()
        questionable = self.read_questionable_condition()
        operation = self.read_operation_condition()
        flags, unknown = self._decode_protection(questionable)
        return DeviceStatus(
            input_enabled=input_enabled,
            short_enabled=short_enabled,
            operating_mode=mode,
            status_byte=status_byte,
            questionable_condition=questionable,
            operation_condition=operation,
            protection_flags=flags,
            unknown_bits=unknown,
            synchronized=synchronized,
        )

    def get_device_status(self) -> DeviceStatus:
        self._require_connected()
        status = self._read_device_status(synchronized=self.session_state is SessionState.CONNECTED_READY)
        self._status_cache = status
        return status

    def read_questionable_event(self) -> int:
        self._require_connected()
        return self._q_int("STATus:QUEStionable:EVENt?", "status.questionable_event", retryable=False, destructive=True)

    def read_questionable_condition(self) -> int:
        self._require_connected()
        return self._q_int("STATus:QUEStionable:CONDition?", "status.questionable_condition")

    def set_questionable_enable(self, value: int) -> None:
        self._require_ready()
        if not 0 <= value <= 32767:
            raise InstrumentRangeError("Questionable enable must be in [0, 32767]")
        self._cmd(f"STATus:QUEStionable:ENABle {value}", "status.set_questionable_enable")

    def get_questionable_enable(self) -> int:
        self._require_connected()
        return self._q_int("STATus:QUEStionable:ENABle?", "status.get_questionable_enable")

    def read_operation_event(self) -> int:
        self._require_connected()
        return self._q_int("STATus:OPERation:EVENt?", "status.operation_event", retryable=False, destructive=True)

    def read_operation_condition(self) -> int:
        self._require_connected()
        return self._q_int("STATus:OPERation:CONDition?", "status.operation_condition")

    def set_operation_enable(self, value: int) -> None:
        self._require_ready()
        if not 0 <= value <= 65535:
            raise InstrumentRangeError("Operation enable must be in [0, 65535]")
        self._cmd(f"STATus:OPERation:ENABle {value}", "status.set_operation_enable")

    def get_operation_enable(self) -> int:
        self._require_connected()
        return self._q_int("STATus:OPERation:ENABle?", "status.get_operation_enable")

    def read_next_error(self) -> SCPIErrorEntry:
        self._require_connected()
        return parse_error(
            self._q_text(
                "SYSTem:ERRor?",
                "system.next_error",
                retryable=False,
                destructive=True,
            )
        )

    def drain_error_queue(self, *, maximum: int | None = None) -> tuple[SCPIErrorEntry, ...]:
        limit = self.config.maximum_error_queue_entries if maximum is None else maximum
        if not 1 <= limit <= self.config.maximum_error_queue_entries:
            raise InstrumentRangeError(
                "maximum must be between 1 and configured maximum_error_queue_entries"
            )
        result: list[SCPIErrorEntry] = []
        for _ in range(limit):
            entry = self.read_next_error()
            if entry.code == 0:
                return tuple(result)
            result.append(entry)
        return tuple(result)

    # ------------------------------------------------------------------
    # Additional documented SCPI command coverage
    # ------------------------------------------------------------------
    def set_peak_enabled(self, enabled: bool) -> None:
        self._require_ready()
        self._cmd(f"PEAK {'ON' if enabled else 'OFF'}", "peak.set_state")

    def clear_peak(self) -> None:
        self._require_ready()
        self._cmd("PEAK CLEar", "peak.clear")

    def read_peak_voltage_maximum(self) -> Measurement:
        return self._measurement("PEAK:VOLTage:MAXimum?", "peak.voltage_max", "V")

    def read_peak_voltage_minimum(self) -> Measurement:
        return self._measurement("PEAK:VOLTage:MINimum?", "peak.voltage_min", "V")

    def read_peak_current_maximum(self) -> Measurement:
        return self._measurement("PEAK:CURRent:MAXimum?", "peak.current_max", "A")

    def read_peak_current_minimum(self) -> Measurement:
        return self._measurement("PEAK:CURRent:MINimum?", "peak.current_min", "A")

    def set_current_protection(self, amperes: float) -> AppliedSetpoint:
        cap = self.get_capabilities()
        return self._set_and_verify(
            command="CURRent:PROTection",
            query="CURRent:PROTection?",
            operation="current_protection.set",
            value=amperes,
            unit="A",
            maximum=cap.maximum_current_a,
        )

    def get_current_protection(self) -> float:
        self._require_connected()
        return self._q_float("CURRent:PROTection?", "current_protection.get")

    def set_power_protection(self, watts: float) -> AppliedSetpoint:
        cap = self.get_capabilities()
        return self._set_and_verify(
            command="POWer:PROTection",
            query="POWer:PROTection?",
            operation="power_protection.set",
            value=watts,
            unit="W",
            maximum=cap.maximum_power_w,
        )

    def get_power_protection(self) -> float:
        self._require_connected()
        return self._q_float("POWer:PROTection?", "power_protection.get")

    def set_dynamic_slew_rise(self, value: float) -> AppliedSetpoint:
        return self._set_and_verify(
            command="DYNamic:SLEW:RISE",
            query="DYNamic:SLEW:RISE?",
            operation="dynamic_slew.set_rise",
            value=value,
            unit="A/us",
        )

    def set_dynamic_slew_fall(self, value: float) -> AppliedSetpoint:
        return self._set_and_verify(
            command="DYNamic:SLEW:FALL",
            query="DYNamic:SLEW:FALL?",
            operation="dynamic_slew.set_fall",
            value=value,
            unit="A/us",
        )

    def set_ocp_test_enabled(self, enabled: bool) -> None:
        self._require_ready(hazardous=enabled)
        self._cmd(
            f"OCP {'ON' if enabled else 'OFF'}",
            "ocp.start" if enabled else "ocp.stop",
            risk=RiskClass.NON_IDEMPOTENT if enabled else RiskClass.HAZARDOUS,
        )

    def get_ocp_test_enabled(self) -> bool:
        self._require_connected()
        return parse_bool(self._q_text("OCP?", "ocp.get_state", retryable=False))

    def read_ocp_result(self) -> OCPTestResult:
        self._require_connected()
        ocp = self._q_float("OCP:RESult?", "ocp.result")
        raw = self._q_text("OCP:RESult:PMAX?", "ocp.pmax")
        parts = [part.strip() for part in raw.replace(",", " ").split() if part.strip()]
        if len(parts) != 3:
            raise MalformedResponseError(
                "OCP:RESult:PMAX? must return power, voltage, and current",
                context={"raw": raw},
            )
        values = [parse_float(part) for part in parts]
        return OCPTestResult(ocp, values[0], values[1], values[2])

    def set_local(self) -> None:
        self._require_ready()
        self._cmd("SYSTem:LOCal", "system.local")
        self._states.transition(SessionState.DEGRADED)

    def set_remote(self) -> None:
        self._require_ready()
        self._cmd("SYSTem:REMote", "system.remote")

    def set_remote_with_local_lockout(self) -> None:
        self._require_ready(hazardous=True)
        self._cmd("SYSTem:RWLock", "system.remote_lock", risk=RiskClass.HAZARDOUS)

    def set_voltage_time_low_threshold(self, volts: float) -> AppliedSetpoint:
        cap = self.get_capabilities()
        return self._set_and_verify(
            command="TIME:VOLTage:LOW",
            query="TIME:VOLTage:LOW?",
            operation="rise_fall.low_threshold",
            value=volts,
            unit="V",
            maximum=cap.maximum_voltage_v,
        )

    def set_voltage_time_high_threshold(self, volts: float) -> AppliedSetpoint:
        cap = self.get_capabilities()
        return self._set_and_verify(
            command="TIME:VOLTage:HIGH",
            query="TIME:VOLTage:HIGH?",
            operation="rise_fall.high_threshold",
            value=volts,
            unit="V",
            maximum=cap.maximum_voltage_v,
        )

    def read_voltage_rise_time(self) -> Measurement:
        return self._measurement("TIME:VOLTage:UP?", "rise_fall.rise_time", "s")

    def read_voltage_fall_time(self) -> Measurement:
        return self._measurement("TIME:VOLTage:DOWN?", "rise_fall.fall_time", "s")

    def set_timing_enabled(self, enabled: bool) -> None:
        self._require_ready(hazardous=enabled)
        self._cmd(
            f"TIMing {'ON' if enabled else 'OFF'}",
            "timing.start" if enabled else "timing.stop",
            risk=RiskClass.NON_IDEMPOTENT if enabled else RiskClass.HAZARDOUS,
        )

    def get_timing_enabled(self) -> bool:
        self._require_connected()
        return parse_bool(self._q_text("TIMing?", "timing.get_state", retryable=False))

    def read_timing_result(self) -> TimingTestResult:
        self._require_connected()
        return TimingTestResult(self._q_float("TIMing:RESult?", "timing.result", retryable=False))

    # ------------------------------------------------------------------
    # Raw access
    # ------------------------------------------------------------------
    def write_raw_scpi(self, command: str, *, timeout_s: float | None = None) -> None:
        self._require_connected()
        if self._active_protocol is not Protocol.SCPI:
            raise UnsupportedFeatureError("Raw SCPI requires an SCPI session")
        self._invalidate_cache()
        self._cmd(command, "raw.scpi.write", risk=RiskClass.HAZARDOUS, timeout_s=timeout_s)
        if self.session_state is SessionState.CONNECTED_READY:
            self._states.transition(SessionState.DEGRADED)

    def query_raw_scpi(self, command: str, *, timeout_s: float | None = None) -> str:
        self._require_connected()
        if self._active_protocol is not Protocol.SCPI:
            raise UnsupportedFeatureError("Raw SCPI requires an SCPI session")
        self._invalidate_cache()
        result = self._q_text(command, "raw.scpi.query", timeout_s=timeout_s, retryable=False)
        if self.session_state is SessionState.CONNECTED_READY:
            self._states.transition(SessionState.DEGRADED)
        return result

    def transact_raw_legacy(self, frame: bytes, *, timeout_s: float | None = None) -> bytes:
        self._require_connected()
        if self._active_protocol is not Protocol.LEGACY:
            raise UnsupportedFeatureError(
                "Raw legacy transactions require a legacy session; in-session protocol mixing is prohibited"
            )
        decoded = decode_frame(frame)
        if decoded.address == 0xFF and not self.config.safety.allow_broadcast_writes:
            raise UnsafeOperationError("Broadcast legacy transactions are disabled by SafetyPolicy")
        self._invalidate_cache()
        response = self._legacy.transact(
            frame,
            operation="raw.legacy.transact",
            timeout_s=timeout_s,
            retryable=False,
        )
        if self.session_state is SessionState.CONNECTED_READY:
            self._states.transition(SessionState.DEGRADED)
        return response.raw

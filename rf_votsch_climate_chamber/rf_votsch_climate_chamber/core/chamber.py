"""Device-semantic service for a Vötsch/SimServ climate chamber.

The core deliberately knows nothing about Robot Framework.  It validates
thermal safety limits, maps high-level operations to protocol commands, and
uses the injected RFDS-004 transport for every device-facing operation.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from ..converters import to_float, to_int
from ..exceptions import (
    DriverError,
    DriverLimitViolationError,
    DriverProtocolError,
    DriverSafetyError,
    DriverStateError,
    DriverTimeoutError,
    DriverTransportError,
    DriverUnsupportedOperationError,
)
from ..models import InstrumentIdentity
from ..protocol.simserv import build_named_frame, format_float, parse_response
from ..transports.base import BaseTransport
from ..transports.models import ReadRequest, ReplayPolicy
from ..transports.tracing import MemoryTraceObserver


class ClimateChamberCore:
    """Validated high-level chamber operations over an injected transport."""

    def __init__(
        self,
        transport: BaseTransport,
        *,
        temperature_min_c: float = -40.0,
        temperature_max_c: float = 180.0,
        timeout_s: float = 5.0,
        response_timeout_s: float | None = None,
        query_retries: int = 1,
        retry_delay_s: float = 0.25,
        verify_writes: bool = True,
        setpoint_verify_tolerance_c: float = 0.05,
        setpoint_verify_timeout_s: float = 15.0,
        setpoint_verify_poll_interval_s: float = 0.25,
        state_change_timeout_s: float = 15.0,
        dryer_output_channel: int | None = None,
        compressed_air_output_channel: int | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.transport = transport
        self.temperature_min_c = to_float(temperature_min_c, "temperature_min_c")
        self.temperature_max_c = to_float(temperature_max_c, "temperature_max_c")
        if self.temperature_min_c >= self.temperature_max_c:
            raise DriverLimitViolationError(
                "temperature_min_c must be lower than temperature_max_c",
                operation="Configure Temperature Limits",
                details={"min_c": self.temperature_min_c, "max_c": self.temperature_max_c},
            )
        self.timeout_s = to_float(timeout_s, "timeout_s")
        self.response_timeout_s = self.timeout_s if response_timeout_s is None else to_float(response_timeout_s, "response_timeout_s")
        if self.timeout_s <= 0 or self.response_timeout_s <= 0:
            raise DriverLimitViolationError("communication timeouts must be > 0 s", operation="configure")
        self.query_retries = to_int(query_retries, "query_retries", minimum=0)
        self.retry_delay_s = to_float(retry_delay_s, "retry_delay_s")
        if self.retry_delay_s < 0:
            raise DriverLimitViolationError("retry_delay_s must be >= 0 s", operation="configure")
        self.verify_writes = bool(verify_writes)
        self.setpoint_verify_tolerance_c = to_float(setpoint_verify_tolerance_c, "setpoint_verify_tolerance_c")
        self.setpoint_verify_timeout_s = to_float(setpoint_verify_timeout_s, "setpoint_verify_timeout_s")
        self.setpoint_verify_poll_interval_s = to_float(
            setpoint_verify_poll_interval_s, "setpoint_verify_poll_interval_s"
        )
        if self.setpoint_verify_tolerance_c <= 0:
            raise DriverLimitViolationError(
                "setpoint_verify_tolerance_c must be > 0 °C", operation="configure"
            )
        if self.setpoint_verify_timeout_s <= 0:
            raise DriverLimitViolationError(
                "setpoint_verify_timeout_s must be > 0 s", operation="configure"
            )
        if self.setpoint_verify_poll_interval_s <= 0:
            raise DriverLimitViolationError(
                "setpoint_verify_poll_interval_s must be > 0 s", operation="configure"
            )
        self.state_change_timeout_s = to_float(state_change_timeout_s, "state_change_timeout_s")
        self.dryer_output_channel = self._validate_optional_output_channel(
            dryer_output_channel, "dryer_output_channel"
        )
        self.compressed_air_output_channel = self._validate_optional_output_channel(
            compressed_air_output_channel, "compressed_air_output_channel"
        )
        if (
            self.dryer_output_channel is not None
            and self.dryer_output_channel == self.compressed_air_output_channel
        ):
            # One physical output cannot drive two independent loads: the two
            # features would silently alias, and Safe Shutdown would report
            # having switched both off after touching only one.
            raise DriverLimitViolationError(
                "dryer and compressed-air outputs must use different channels",
                operation="Configure Auxiliary Outputs",
                details={
                    "dryer_output_channel": self.dryer_output_channel,
                    "compressed_air_output_channel": self.compressed_air_output_channel,
                },
                recovery_action=(
                    "confirm the physical mapping and give each auxiliary output its own "
                    "channel, or leave the unused one unset"
                ),
            )
        self._sleep = sleep
        self._monotonic = monotonic
        self._operation_lock = threading.RLock()
        self._cancel_event = threading.Event()
        self._identity: InstrumentIdentity | None = None
        self._trace = MemoryTraceObserver()
        self.transport.add_trace_observer(self._trace)
        self._operations_started = 0
        self._operations_succeeded = 0
        self._operations_failed = 0
        self._last_error: dict[str, Any] | None = None

    @property
    def is_connected(self) -> bool:
        return self.transport.is_open

    @property
    def identity_cache(self) -> InstrumentIdentity | None:
        return self._identity

    def connect(self) -> InstrumentIdentity:
        with self._operation_lock:
            self.transport.open()
            try:
                self.check_communication()
                self._identity = self.read_identity(refresh=True)
                return self._identity
            except Exception:
                self.transport.close(timeout_s=self.timeout_s)
                raise

    def disconnect(self) -> None:
        self._cancel_event.set()
        self.transport.close(timeout_s=self.timeout_s)

    def reconnect(self) -> InstrumentIdentity:
        with self._operation_lock:
            self.transport.reconnect(timeout_s=self.timeout_s)
            self._cancel_event.clear()
            self.check_communication()
            self._identity = self.read_identity(refresh=True)
            return self._identity

    def cancel(self) -> None:
        self._cancel_event.set()
        self.transport.cancel()

    def set_timeout(self, timeout_s: float) -> float:
        value = to_float(timeout_s, "timeout_s")
        if value <= 0:
            raise DriverLimitViolationError("timeout_s must be > 0 s", operation="Set Communication Timeout")
        self.timeout_s = value
        self.response_timeout_s = value
        if hasattr(self.transport, "timeout_s"):
            self.transport.timeout_s = value  # type: ignore[attr-defined]
        return value

    def get_timeout(self) -> float:
        return float(self.timeout_s)

    def check_communication(self) -> bool:
        self._query("GET CHAMBER STATUS", retry_safe=True, operation_id="Check Communication")
        return True

    def _query(
        self,
        command_name: str,
        *arguments: object,
        retry_safe: bool,
        operation_id: str,
        timeout_s: float | None = None,
    ) -> list[str]:
        if not self.transport.is_open:
            raise DriverStateError(
                "driver is not connected",
                code="RFDS-CON-002",
                operation=operation_id,
                recovery_action="call Connect first",
            )
        attempts = 1 + (self.query_retries if retry_safe else 0)
        frame = build_named_frame(command_name, *arguments)
        request = ReadRequest(terminator=b"\r", max_bytes=4096)
        last_error: DriverError | None = None
        self._operations_started += 1
        for attempt in range(1, attempts + 1):
            try:
                raw = self.transport.transact(
                    frame,
                    request,
                    timeout_s=self.response_timeout_s if timeout_s is None else timeout_s,
                    replay_policy=ReplayPolicy.SAFE_QUERY if retry_safe else ReplayPolicy.NEVER,
                    operation_id=operation_id,
                )
                result = parse_response(command_name, tuple(arguments), raw)
                self._operations_succeeded += 1
                return result
            except (DriverTransportError, DriverTimeoutError, DriverProtocolError) as exc:
                last_error = exc
                self._last_error = exc.to_dict()
                if attempt >= attempts or not retry_safe:
                    self._operations_failed += 1
                    raise
                self._sleep(self.retry_delay_s)
                self.transport.reconnect(timeout_s=self.timeout_s)
        self._operations_failed += 1
        assert last_error is not None
        raise last_error

    def read_identity(self, *, refresh: bool = False) -> InstrumentIdentity:
        if self._identity is not None and not refresh:
            return self._identity
        model = self._query("GET CHAMBER INFO", 1, retry_safe=True, operation_id="Get Identity")[0]
        year = self._query("GET CHAMBER INFO", 2, retry_safe=True, operation_id="Get Identity")[0]
        serial = self._query("GET CHAMBER INFO", 3, retry_safe=True, operation_id="Get Identity")[0]
        text = f"Vötsch climate chamber, {model}, serial {serial}, manufactured {year}"
        self._identity = InstrumentIdentity(
            identity=text,
            manufacturer="Vötsch",
            model=model,
            serial_number=serial,
            manufacturing_year=year,
            raw=text,
        )
        return self._identity

    def get_status(self) -> str:
        return self._query("GET CHAMBER STATUS", retry_safe=True, operation_id="Get Chamber Status")[0]

    def measure_temperature_c(self) -> float:
        return float(
            self._query(
                "GET CONTROL_VARIABLE ACTUAL_VALUE",
                1,
                retry_safe=True,
                operation_id="Measure Temperature",
            )[0]
        )

    def get_temperature_setpoint_c(self) -> float:
        return float(
            self._query(
                "GET CONTROL_VARIABLE SET_POINT",
                1,
                retry_safe=True,
                operation_id="Get Temperature Setpoint",
            )[0]
        )

    def set_temperature_c(self, value_c: float) -> None:
        value = to_float(value_c, "value_c")
        if not self.temperature_min_c <= value <= self.temperature_max_c:
            raise DriverLimitViolationError(
                "requested temperature is outside configured safety limits",
                operation="Set Temperature",
                details={
                    "requested_c": value,
                    "configured_min_c": self.temperature_min_c,
                    "configured_max_c": self.temperature_max_c,
                },
            )
        with self._operation_lock:
            self._query(
                "SET CONTROL_VARIABLE SET_POINT",
                1,
                format_float(value),
                retry_safe=False,
                operation_id="Set Temperature",
            )
            if self.verify_writes:
                self._wait_for_setpoint_readback(value)

    def _wait_for_setpoint_readback(self, requested_c: float) -> float:
        """Poll setpoint readback until the chamber reports the requested value.

        Some SimServ chamber controllers acknowledge the write before the public
        readback register is updated.  A single immediate query therefore creates
        false failures on real hardware.  Verification remains strict, but is now
        bounded and eventual rather than instantaneous.
        """
        started = self._monotonic()
        deadline = started + self.setpoint_verify_timeout_s
        attempts = 0
        actual = self.get_temperature_setpoint_c()
        while True:
            attempts += 1
            if abs(actual - requested_c) <= self.setpoint_verify_tolerance_c:
                return actual
            now = self._monotonic()
            if now >= deadline:
                raise DriverSafetyError(
                    "setpoint readback verification timed out",
                    operation="Set Temperature",
                    details={
                        "requested_c": requested_c,
                        "reported_c": actual,
                        "tolerance_c": self.setpoint_verify_tolerance_c,
                        "verification_timeout_s": self.setpoint_verify_timeout_s,
                        "verification_attempts": attempts,
                        "elapsed_s": now - started,
                    },
                    recovery_action=(
                        "inspect chamber local-control mode and setpoint permissions; "
                        "increase setpoint_verify_timeout_s only when the controller is known to update slowly"
                    ),
                )
            self._sleep(min(self.setpoint_verify_poll_interval_s, max(0.0, deadline - now)))
            actual = self.get_temperature_setpoint_c()

    def get_temperature_limits(self) -> dict[str, Any]:
        return {
            "quantity": "temperature",
            "unit": "c",
            "min": self.temperature_min_c,
            "max": self.temperature_max_c,
            "resolution": 0.01,
            "configured_min": self.temperature_min_c,
            "configured_max": self.temperature_max_c,
            "channel": "1",
        }

    def set_temperature_limits(self, minimum_c: float, maximum_c: float) -> dict[str, Any]:
        minimum = to_float(minimum_c, "minimum_c")
        maximum = to_float(maximum_c, "maximum_c")
        if minimum >= maximum:
            raise DriverLimitViolationError(
                "minimum_c must be lower than maximum_c",
                operation="Set Temperature Limits",
                details={"minimum_c": minimum, "maximum_c": maximum},
            )
        self.temperature_min_c = minimum
        self.temperature_max_c = maximum
        return self.get_temperature_limits()

    def get_running(self) -> bool:
        return self._get_digital_output(1, "Get Chamber Running State")

    def start(self) -> None:
        with self._operation_lock:
            if self.get_running():
                return
            self._query("START MANUAL_MODE", 1, 1, retry_safe=False, operation_id="Start Chamber")
            if self.verify_writes:
                self._wait_for_state(self.get_running, True, "Start Chamber")

    def stop(self) -> None:
        with self._operation_lock:
            if not self.get_running():
                return
            self._query("START MANUAL_MODE", 1, 0, retry_safe=False, operation_id="Stop Chamber")
            if self.verify_writes:
                self._wait_for_state(self.get_running, False, "Stop Chamber")

    def _wait_for_state(self, getter: Callable[[], bool], expected: bool, operation: str) -> None:
        deadline = self._monotonic() + self.state_change_timeout_s
        last_error: DriverError | None = None
        while self._monotonic() < deadline:
            try:
                if getter() is expected:
                    return
            except DriverError as exc:
                last_error = exc
            self._sleep(0.25)
        details = {"expected": expected, "timeout_s": self.state_change_timeout_s}
        if last_error is not None:
            details["last_error"] = last_error.to_dict()
        raise DriverTimeoutError(
            "device state did not reach the requested value",
            operation=operation,
            details=details,
        )

    @staticmethod
    def _validate_optional_output_channel(channel: int | None, name: str) -> int | None:
        if channel is None:
            return None
        value = to_int(channel, name, minimum=2)
        return value

    @staticmethod
    def _require_output_channel(channel: int | None, feature: str, operation: str) -> int:
        if channel is None:
            raise DriverUnsupportedOperationError(
                f"{feature} output is not configured for this chamber profile",
                operation=operation,
                details={"feature": feature, "configured_channel": None},
                recovery_action=(
                    f"confirm the physical mapping, then configure {feature}_output_channel "
                    "in settings.auxiliary_outputs or as a Connect option"
                ),
            )
        return channel

    def _get_digital_output(self, channel: int, operation: str) -> bool:
        value = self._query(
            "GET DIGITAL_OUT VALUE", channel, retry_safe=True, operation_id=operation
        )[0]
        if value not in {"0", "1"}:
            raise DriverProtocolError(
                f"digital output returned {value!r}; expected '0' or '1'",
                operation=operation,
            )
        return value == "1"

    def _set_digital_output(self, channel: int, enabled: bool, operation: str) -> None:
        with self._operation_lock:
            self._query(
                "SET DIGITAL_OUT VALUE",
                channel,
                1 if enabled else 0,
                retry_safe=False,
                operation_id=operation,
            )
            if self.verify_writes:
                self._wait_for_digital_output_readback(channel, enabled, operation)

    def _wait_for_digital_output_readback(
        self, channel: int, requested: bool, operation: str
    ) -> None:
        """Poll a digital output's readback until it reports the requested state.

        Same controller behaviour that ``_wait_for_setpoint_readback`` above
        already compensates for: the SimServ acknowledgement for 14001 can land
        before the 14003 readback register reflects the new state, and a relay
        output additionally needs time to physically settle. A single immediate
        query therefore produced false ``RFDS-SAF-001`` failures on real
        hardware. Verification stays strict, but is bounded and eventual.
        """
        started = self._monotonic()
        deadline = started + self.state_change_timeout_s
        attempts = 0
        actual = self._get_digital_output(channel, operation)
        while True:
            attempts += 1
            if actual is requested:
                return
            now = self._monotonic()
            if now >= deadline:
                raise DriverSafetyError(
                    "digital-output readback verification failed",
                    operation=operation,
                    details={
                        "channel": channel,
                        "requested": requested,
                        "reported": actual,
                        "verification_timeout_s": self.state_change_timeout_s,
                        "verification_attempts": attempts,
                        "elapsed_s": now - started,
                    },
                    recovery_action=(
                        "confirm the physical mapping of this output channel and that the "
                        "chamber grants remote control of it; increase state_change_timeout_s "
                        "only when the output is known to switch slowly"
                    ),
                )
            self._sleep(min(self.setpoint_verify_poll_interval_s, max(0.0, deadline - now)))
            actual = self._get_digital_output(channel, operation)

    def get_dryer(self) -> bool:
        channel = self._require_output_channel(self.dryer_output_channel, "dryer", "Get Dryer")
        return self._get_digital_output(channel, "Get Dryer")

    def set_dryer(self, enabled: bool) -> None:
        channel = self._require_output_channel(self.dryer_output_channel, "dryer", "Set Dryer")
        self._set_digital_output(channel, bool(enabled), "Set Dryer")

    def get_compressed_air(self) -> bool:
        channel = self._require_output_channel(
            self.compressed_air_output_channel, "compressed_air", "Get Compressed Air"
        )
        return self._get_digital_output(channel, "Get Compressed Air")

    def set_compressed_air(self, enabled: bool) -> None:
        channel = self._require_output_channel(
            self.compressed_air_output_channel, "compressed_air", "Set Compressed Air"
        )
        self._set_digital_output(channel, bool(enabled), "Set Compressed Air")

    def get_heating_gradient_c_per_min(self) -> float:
        return float(self._query("GET GRADIENT_UP VALUE", 1, retry_safe=True, operation_id="Get Heating Gradient")[0])

    def set_heating_gradient_c_per_min(self, value_c_per_min: float) -> None:
        value = to_float(value_c_per_min, "value_c_per_min")
        if not 0.01 <= value <= 5.0:
            raise DriverLimitViolationError(
                "heating gradient must be between 0.01 and 5.0 °C/min",
                operation="Set Heating Gradient",
                details={"value_c_per_min": value},
            )
        self._query("SET GRADIENT_UP VALUE", 1, format_float(value), retry_safe=False, operation_id="Set Heating Gradient")
        if self.verify_writes and abs(self.get_heating_gradient_c_per_min() - value) > 0.05:
            raise DriverSafetyError("heating-gradient readback verification failed", operation="Set Heating Gradient")

    def get_cooling_gradient_c_per_min(self) -> float:
        return float(self._query("GET GRADIENT_DOWN VALUE", 1, retry_safe=True, operation_id="Get Cooling Gradient")[0])

    def set_cooling_gradient_c_per_min(self, value_c_per_min: float) -> None:
        value = to_float(value_c_per_min, "value_c_per_min")
        if not 0.01 <= value <= 3.5:
            raise DriverLimitViolationError(
                "cooling gradient must be between 0.01 and 3.5 °C/min",
                operation="Set Cooling Gradient",
                details={"value_c_per_min": value},
            )
        self._query("SET GRADIENT_DOWN VALUE", 1, format_float(value), retry_safe=False, operation_id="Set Cooling Gradient")
        if self.verify_writes and abs(self.get_cooling_gradient_c_per_min() - value) > 0.05:
            raise DriverSafetyError("cooling-gradient readback verification failed", operation="Set Cooling Gradient")

    def wait_for_temperature(
        self,
        target_c: float,
        *,
        tolerance_c: float = 0.8,
        stable_samples: int = 3,
        poll_interval_s: float = 10.0,
        settle_timeout_s: float = 14_400.0,
        progress: Callable[[dict[str, Any]], None] | None = None,
    ) -> float:
        target = to_float(target_c, "target_c")
        tolerance = to_float(tolerance_c, "tolerance_c")
        samples = to_int(stable_samples, "stable_samples", minimum=1)
        poll = to_float(poll_interval_s, "poll_interval_s")
        timeout = to_float(settle_timeout_s, "settle_timeout_s")
        if tolerance < 0 or poll <= 0 or timeout <= 0:
            raise DriverLimitViolationError("wait parameters are outside allowed bounds", operation="Wait For Temperature Stability")
        self._cancel_event.clear()
        started = self._monotonic()
        deadline = started + timeout
        stable = 0
        last = self.measure_temperature_c()
        while True:
            if self._cancel_event.is_set():
                raise DriverStateError("temperature wait was cancelled", operation="Wait For Temperature Stability")
            now = self._monotonic()
            if now >= deadline:
                raise DriverTimeoutError(
                    "temperature did not stabilize before the deadline",
                    operation="Wait For Temperature Stability",
                    details={
                        "target_c": target,
                        "last_temperature_c": last,
                        "tolerance_c": tolerance,
                        "stable_samples": stable,
                        "required_stable_samples": samples,
                        "timeout_s": timeout,
                    },
                )
            last = self.measure_temperature_c()
            stable = stable + 1 if abs(last - target) <= tolerance else 0
            state = {
                "target_c": target,
                "temperature_c": last,
                "tolerance_c": tolerance,
                "stable_count": stable,
                "stable_samples": samples,
                "elapsed_s": now - started,
            }
            if progress is not None:
                progress(state)
            if stable >= samples:
                return last
            self._sleep(min(poll, max(0.0, deadline - self._monotonic())))

    def dwell(
        self,
        duration_s: float,
        *,
        poll_interval_s: float = 60.0,
        progress: Callable[[dict[str, Any]], None] | None = None,
    ) -> float:
        duration = to_float(duration_s, "duration_s")
        poll = to_float(poll_interval_s, "poll_interval_s")
        if duration < 0 or poll <= 0:
            raise DriverLimitViolationError("dwell duration must be >= 0 and poll interval > 0", operation="Wait For Dwell")
        self._cancel_event.clear()
        started = self._monotonic()
        deadline = started + duration
        last = self.measure_temperature_c()
        while self._monotonic() < deadline:
            if self._cancel_event.is_set():
                raise DriverStateError("dwell was cancelled", operation="Wait For Dwell")
            last = self.measure_temperature_c()
            remaining = max(0.0, deadline - self._monotonic())
            if progress is not None:
                progress({"temperature_c": last, "elapsed_s": self._monotonic() - started, "remaining_s": remaining})
            self._sleep(min(poll, remaining))
        return last

    def set_temperature_and_wait(
        self,
        value_c: float,
        *,
        dwell_s: float = 0.0,
        tolerance_c: float = 0.8,
        poll_interval_s: float = 10.0,
        settle_timeout_s: float = 14_400.0,
        stable_samples: int = 3,
        start_chamber: bool = True,
        progress: Callable[[dict[str, Any]], None] | None = None,
    ) -> float:
        self.set_temperature_c(value_c)
        if start_chamber:
            self.start()
        final = self.wait_for_temperature(
            value_c,
            tolerance_c=tolerance_c,
            stable_samples=stable_samples,
            poll_interval_s=poll_interval_s,
            settle_timeout_s=settle_timeout_s,
            progress=progress,
        )
        if dwell_s > 0:
            final = self.dwell(dwell_s, poll_interval_s=poll_interval_s, progress=progress)
        return final

    def safe_shutdown(self, *, timeout_s: float | None = None) -> dict[str, Any]:
        """Best-effort safe state using only capabilities configured for this chamber.

        Stopping the chamber is always attempted.  Auxiliary outputs are disabled
        only when a physical channel mapping has been explicitly configured.
        This prevents an unqualified driver from sending model-dependent digital
        output commands during teardown.
        """
        started = self._monotonic()
        failures: list[dict[str, Any]] = []
        actions: list[dict[str, Any]] = []
        planned_actions: list[tuple[str, Callable[[], None]]] = []

        for name, channel, action in (
            ("compressed_air_off", self.compressed_air_output_channel, lambda: self.set_compressed_air(False)),
            ("dryer_off", self.dryer_output_channel, lambda: self.set_dryer(False)),
        ):
            if channel is None:
                actions.append(
                    {
                        "action": name,
                        "status": "SKIP",
                        "reason": "auxiliary output channel is not configured",
                    }
                )
            else:
                planned_actions.append((name, action))
        planned_actions.append(("chamber_stop", self.stop))

        for name, action in planned_actions:
            if timeout_s is not None and self._monotonic() - started >= timeout_s:
                failures.append({"action": name, "error": "safe-shutdown deadline exceeded"})
                actions.append({"action": name, "status": "FAIL"})
                break
            try:
                action()
                actions.append({"action": name, "status": "PASS"})
            except DriverError as exc:
                failures.append({"action": name, "error": exc.to_dict()})
                actions.append({"action": name, "status": "FAIL"})
        result = {
            "safe": not failures,
            "actions": actions,
            "failures": failures,
            "elapsed_s": self._monotonic() - started,
            "confirmed": not failures,
        }
        if failures:
            raise DriverSafetyError(
                "safe state could not be confirmed",
                operation="Safe Shutdown",
                details=result,
                recovery_action="use the chamber emergency stop and inspect the device locally",
            )
        return result

    def diagnostics(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "connected": self.is_connected,
            "identity": None if self._identity is None else self._identity.to_dict(),
            "temperature_limits": self.get_temperature_limits(),
            "operations_started": self._operations_started,
            "operations_succeeded": self._operations_succeeded,
            "operations_failed": self._operations_failed,
            "last_error": self._last_error,
            "transport_state": self.transport.state.value,
            "transport_descriptor": None if getattr(self.transport, "_descriptor", None) is None else self.transport.descriptor.to_dict(),
            "transport_metrics": self.transport.metrics.to_dict(),
            "protocol_trace": self._trace.to_list(),
        }

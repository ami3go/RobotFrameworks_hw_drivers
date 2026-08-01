"""Instrument driver for the B&K Precision 8500 series DC electronic loads.

This module is pure Python and has no Robot Framework dependency, so it can be
reused from scripts, pytest, or any other harness. The Robot Framework keyword
layer in :mod:`bk8500_load.library` is a thin wrapper over this class.

Design rules
------------
* All public arguments and return values are in SI units (V, A, W, ohm, s).
  Raw instrument counts never leave this module.
* Every parameter is validated against the model's rated envelope *before* a
  frame is transmitted, so an out-of-range request fails fast and locally.
* Every command's response status is checked; a non-success status raises
  :class:`~bk8500_load.exceptions.BK8500CommandError`.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from typing import Any, Callable

from . import protocol as p
from .enums import (
    DEMAND_STATE_BITS,
    OPERATION_STATE_BITS,
    InputValues,
    ListRepeat,
    ListStep,
    LoadFunction,
    LoadMode,
    ModelLimits,
    ProductInfo,
    TransientOperation,
    TransientSettings,
    TriggerSource,
    decode_bitfield,
    limits_for,
    parse_enum,
)
from .exceptions import (
    BK8500CommandError,
    BK8500ConfigurationError,
    BK8500Error,
    BK8500TimeoutError,
    BK8500ConnectionError,
    BK8500ProtectionError,
    BK8500ProtocolError,
    BK8500SafetyError,
    BK8500StateError,
    BK8500ValidationError,
)
from .transport import SUPPORTED_BAUD_RATES, SerialTransport, SimulatedTransport, Transport

LOGGER = logging.getLogger(__name__)


def _ordered_baud_rates(
    preferred: int,
    candidates: Iterable[int] = SUPPORTED_BAUD_RATES,
) -> tuple[int, ...]:
    """Return a validated, de-duplicated baud probe order.

    The explicitly requested rate is always attempted first. All candidates
    must be rates supported by the 8500-series firmware; invalid values are
    rejected before any serial port is opened.
    """
    try:
        preferred_rate = int(preferred)
    except (TypeError, ValueError):
        raise BK8500ConfigurationError(
            f"Preferred baud rate must be numeric, received {preferred!r}"
        ) from None

    ordered: list[int] = [preferred_rate]
    for candidate in candidates:
        try:
            rate = int(candidate)
        except (TypeError, ValueError):
            raise BK8500ConfigurationError(
                f"Baud-rate candidate must be numeric, received {candidate!r}"
            ) from None
        if rate not in ordered:
            ordered.append(rate)

    unsupported = [rate for rate in ordered if rate not in SUPPORTED_BAUD_RATES]
    if unsupported:
        raise BK8500ConfigurationError(
            f"Unsupported baud-rate candidates: {unsupported}. "
            f"Supported rates: {SUPPORTED_BAUD_RATES}"
        )
    return tuple(ordered)

#: Per-operation settling times, in seconds, matching the
#: ``stabilization_delay_s`` field of each capability in ai/bk8500_load_ai_contract.yaml.
#: Applied by the driver so the contract describes behaviour rather than advice.
STABILIZATION_DELAYS_S: dict[str, float] = {
    "input_state": 0.1,
    "apply_load": 0.1,
    "mode": 0.05,
    "setpoint": 0.05,
    "function": 0.05,
    "remote_sense": 0.2,
    "save_list_file": 0.5,
    "recall_list_file": 0.2,
    "save_settings": 0.5,
    "recall_settings": 0.2,
    "safe_state": 0.1,
}

#: Widest dwell time expressible in the 2 byte, 0.1 ms transient/list field.
MAX_DWELL_S = 65535 / p.COUNTS_PER_SECOND_DWELL
#: Widest LOAD ON timer value (2 byte field, 1 s units).
MAX_LOAD_ON_TIMER_S = 60000

_MODE_SETPOINT_COMMANDS: dict[LoadMode, tuple[int, int, float, str]] = {
    LoadMode.CC: (p.Command.SET_CC_CURRENT, p.Command.GET_CC_CURRENT, p.COUNTS_PER_AMP, "A"),
    LoadMode.CV: (p.Command.SET_CV_VOLTAGE, p.Command.GET_CV_VOLTAGE, p.COUNTS_PER_VOLT, "V"),
    LoadMode.CW: (p.Command.SET_CW_POWER, p.Command.GET_CW_POWER, p.COUNTS_PER_WATT, "W"),
    LoadMode.CR: (p.Command.SET_CR_RESISTANCE, p.Command.GET_CR_RESISTANCE, p.COUNTS_PER_OHM, "ohm"),
}

_TRANSIENT_COMMANDS: dict[LoadMode, tuple[int, int, float]] = {
    LoadMode.CC: (p.Command.SET_CC_TRANSIENT, p.Command.GET_CC_TRANSIENT, p.COUNTS_PER_AMP),
    LoadMode.CV: (p.Command.SET_CV_TRANSIENT, p.Command.GET_CV_TRANSIENT, p.COUNTS_PER_VOLT),
    LoadMode.CW: (p.Command.SET_CW_TRANSIENT, p.Command.GET_CW_TRANSIENT, p.COUNTS_PER_WATT),
    LoadMode.CR: (p.Command.SET_CR_TRANSIENT, p.Command.GET_CR_TRANSIENT, p.COUNTS_PER_OHM),
}

_LIST_STEP_COMMANDS: dict[LoadMode, tuple[int, int, float]] = {
    LoadMode.CC: (p.Command.SET_LIST_STEP_CURRENT, p.Command.GET_LIST_STEP_CURRENT, p.COUNTS_PER_AMP),
    LoadMode.CV: (p.Command.SET_LIST_STEP_VOLTAGE, p.Command.GET_LIST_STEP_VOLTAGE, p.COUNTS_PER_VOLT),
    LoadMode.CW: (p.Command.SET_LIST_STEP_POWER, p.Command.GET_LIST_STEP_POWER, p.COUNTS_PER_WATT),
    LoadMode.CR: (
        p.Command.SET_LIST_STEP_RESISTANCE,
        p.Command.GET_LIST_STEP_RESISTANCE,
        p.COUNTS_PER_OHM,
    ),
}


class BK8500Driver:
    """Stateful driver for one 8500 series load on one transport."""

    def __init__(
        self,
        transport: Transport,
        model: str | None = None,
        address: int = 0,
        retries: int = 2,
        retry_delay_s: float = 0.05,
        settle_delay_s: float = 0.0,
        apply_stabilization_delays: bool = True,
    ) -> None:
        if not 0 <= int(address) < 0xFF:
            raise BK8500ValidationError(f"Address {address} outside 0x00..0xFE")
        self.transport = transport
        self.address = int(address)
        self.retries = max(int(retries), 0)
        self.retry_delay_s = float(retry_delay_s)
        self.settle_delay_s = float(settle_delay_s)
        self.apply_stabilization_delays = bool(apply_stabilization_delays)
        self.response_style: str | None = None
        self._declared_model = model
        self._limits: ModelLimits = limits_for(model)
        self._product_info: ProductInfo | None = None
        self._remote = False
        self.detected_baudrate: int | None = getattr(transport, "baudrate", None)
        self.baudrate_probe_attempts: tuple[dict[str, Any], ...] = ()

    # ------------------------------------------------------------------
    # construction helpers
    # ------------------------------------------------------------------
    @classmethod
    def on_serial_port(
        cls,
        port: str,
        baudrate: int = 9600,
        model: str | None = None,
        address: int = 0,
        timeout_s: float = 1.0,
        assert_dtr: bool = True,
        assert_rts: bool = True,
        **kwargs,
    ) -> "BK8500Driver":
        transport = SerialTransport(
            port,
            baudrate,
            timeout_s,
            assert_dtr=assert_dtr,
            assert_rts=assert_rts,
        )
        return cls(transport, model=model, address=address, **kwargs)

    @classmethod
    def connect_serial_with_baud_detection(
        cls,
        port: str,
        preferred_baudrate: int = 9600,
        baudrate_candidates: Iterable[int] = SUPPORTED_BAUD_RATES,
        model: str | None = None,
        address: int = 0,
        timeout_s: float = 1.0,
        probe_timeout_s: float = 0.75,
        assert_dtr: bool = True,
        assert_rts: bool = True,
        retries: int = 2,
        retry_delay_s: float = 0.05,
        inter_probe_delay_s: float = 0.1,
        confirm_identity: bool = True,
        **driver_kwargs: Any,
    ) -> tuple["BK8500Driver", ProductInfo, tuple[dict[str, Any], ...]]:
        """Connect at the first baud rate that returns a stable identity.

        Detection is deliberately read-only: every attempt sends only the
        product-information query. Exact local echoes, malformed packets,
        empty identities and timeouts are rejected by the normal transport and
        identity parsers. When ``confirm_identity`` is true, two consecutive
        identity queries must agree before the rate is accepted.

        The successful driver remains connected and is returned together with
        the identity and a machine-readable attempt log.
        """
        rates = _ordered_baud_rates(preferred_baudrate, baudrate_candidates)
        attempts: list[dict[str, Any]] = []
        driver_kwargs = dict(driver_kwargs)
        driver_kwargs.pop("retries", None)
        driver_kwargs.pop("retry_delay_s", None)
        normal_timeout = float(timeout_s)
        quick_timeout = float(probe_timeout_s)
        if normal_timeout <= 0:
            raise BK8500ConfigurationError(
                f"timeout_s must be greater than zero, received {timeout_s!r}"
            )
        if not 0.05 <= quick_timeout <= 10.0:
            raise BK8500ConfigurationError(
                f"probe_timeout_s must be between 0.05 and 10.0 seconds, "
                f"received {probe_timeout_s!r}"
            )
        if float(inter_probe_delay_s) < 0:
            raise BK8500ConfigurationError(
                f"inter_probe_delay_s cannot be negative, received {inter_probe_delay_s!r}"
            )

        for baudrate in rates:
            candidate = cls.on_serial_port(
                port=port,
                baudrate=baudrate,
                model=model,
                address=address,
                timeout_s=quick_timeout,
                assert_dtr=assert_dtr,
                assert_rts=assert_rts,
                retries=0,
                retry_delay_s=retry_delay_s,
                **driver_kwargs,
            )
            try:
                first = candidate.connect(identify=True)
                if first is None:  # defensive: identify=True must return data
                    raise BK8500ConnectionError(
                        "Baud probe did not return product information"
                    )
                if not first.model or not first.serial_number:
                    raise BK8500ProtocolError(
                        "Baud probe returned an incomplete product identity"
                    )

                if confirm_identity:
                    second = candidate.get_product_info()
                    if (
                        second.model != first.model
                        or second.serial_number != first.serial_number
                        or second.firmware_raw != first.firmware_raw
                    ):
                        raise BK8500ProtocolError(
                            "Baud probe identity was not repeatable: "
                            f"first={first.as_dict()}, second={second.as_dict()}"
                        )

                candidate.retries = max(int(retries), 0)
                candidate.retry_delay_s = float(retry_delay_s)
                candidate.detected_baudrate = baudrate
                transport = candidate.transport
                if hasattr(transport, "timeout_s"):
                    transport.timeout_s = normal_timeout
                serial_object = getattr(transport, "_serial", None)
                if serial_object is not None:
                    serial_object.timeout = normal_timeout

                attempts.append(
                    {
                        "baudrate": baudrate,
                        "result": "PASS",
                        "identity": first.as_dict(),
                    }
                )
                candidate.baudrate_probe_attempts = tuple(attempts)
                LOGGER.info(
                    "Detected BK8500 baud rate %d on %s: model=%s, serial=%s, firmware=%s",
                    baudrate,
                    port,
                    first.model,
                    first.serial_number,
                    first.firmware_version,
                )
                return candidate, first, tuple(attempts)

            except BK8500Error as exc:
                candidate.transport.close()
                attempts.append(
                    {
                        "baudrate": baudrate,
                        "result": "FAIL",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                LOGGER.info(
                    "Baud-rate probe failed on %s at %d baud: %s",
                    port,
                    baudrate,
                    exc,
                )
                if inter_probe_delay_s > 0:
                    time.sleep(float(inter_probe_delay_s))
            except Exception:
                candidate.transport.close()
                raise

        summary = "; ".join(
            f"{attempt['baudrate']}: {attempt.get('error_type', 'unknown')} - "
            f"{attempt.get('error', 'no details')}"
            for attempt in attempts
        )
        raise BK8500ConnectionError(
            f"Could not identify a BK8500-compatible load on {port} at any "
            f"supported baud rate. Attempts: {summary}"
        )

    @classmethod
    def simulated(cls, model: str = "8500", **kwargs) -> "BK8500Driver":
        sim_kwargs = {
            key: kwargs.pop(key)
            for key in ("source_voltage_v", "source_resistance_ohm", "serial_number")
            if key in kwargs
        }
        return cls(SimulatedTransport(model=model, **sim_kwargs), model=model, **kwargs)

    # ------------------------------------------------------------------
    # properties
    # ------------------------------------------------------------------
    @property
    def limits(self) -> ModelLimits:
        """Rated envelope used for pre-flight validation."""
        return self._limits

    @property
    def is_connected(self) -> bool:
        return self.transport.is_open

    @property
    def description(self) -> str:
        return f"{self._limits.model} on {self.transport.description}"

    # ------------------------------------------------------------------
    # connection lifecycle
    # ------------------------------------------------------------------
    def connect(self, identify: bool = True) -> ProductInfo | None:
        """Open the transport and, by default, read the instrument identity.

        When ``identify`` is true the model reported by the instrument
        replaces the declared model for validation purposes, so limits always
        follow the hardware actually present.
        """
        self.transport.open()
        if not identify:
            return None
        try:
            info = self.get_product_info()
        except Exception:
            # A failed identity read must not leak an open serial handle.  The
            # caller may retry after correcting the baud rate or signal lines.
            # Cleanup failure is logged but never masks the useful protocol or
            # timeout exception that caused connection setup to fail.
            try:
                self.transport.close()
            except Exception as close_error:  # pragma: no cover - defensive
                LOGGER.warning("Transport cleanup after failed identification failed: %s", close_error)
            raise
        detected = limits_for(info.model)
        if detected.model != "UNKNOWN":
            if self._declared_model and detected.model != limits_for(self._declared_model).model:
                LOGGER.warning(
                    "Declared model %s does not match instrument model %s; using %s",
                    self._declared_model,
                    info.model,
                    info.model,
                )
            self._limits = detected
        return info

    def disconnect(self, safe: bool = True) -> None:
        """Bring the load to a safe state where possible, then close the port."""
        if self.transport.is_open and safe:
            try:
                self.reset_to_safe_state()
            except Exception as exc:  # never mask the close
                LOGGER.warning("Safe-state teardown failed: %s", exc)
        self.transport.close()

    def reset_to_safe_state(self) -> None:
        """Input off, FIXED function, front panel returned to the operator."""
        self.set_remote_control(True)
        self.set_input_state(False)
        self.set_function(LoadFunction.FIXED)
        self.set_local_key_enabled(True)
        self.set_remote_control(False)
        self._settle("safe_state")

    # ------------------------------------------------------------------
    # frame level
    # ------------------------------------------------------------------
    def _transact(self, command: int, payload: bytes = b"") -> bytes:
        if not self.transport.is_open:
            raise BK8500ConnectionError("Driver is not connected; call connect() first")
        frame = p.build_frame(self.address, command, payload)
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = self.transport.transact(frame)
            except (BK8500ProtocolError, BK8500TimeoutError) as exc:
                # Both are transient on a TTL adapter. The transport flushes the
                # input buffer before each write, so a late frame from the failed
                # attempt cannot be mistaken for the reply to the next one.
                last_error = exc
            else:
                ok, reason = p.frame_is_well_formed(response)
                if ok and response[1] != self.address:
                    ok, reason = False, (
                        f"reply came from address 0x{response[1]:02X}, "
                        f"expected 0x{self.address:02X}"
                    )
                if ok:
                    LOGGER.debug(
                        "cmd 0x%02X -> %s | %s",
                        command,
                        p.format_frame(frame),
                        p.format_frame(response),
                    )
                    return response
                last_error = BK8500ProtocolError(
                    f"Malformed response to command 0x{int(command):02X}: {reason} "
                    f"[{p.format_frame(response)}]"
                )
            if attempt < self.retries:
                time.sleep(self.retry_delay_s)
        raise last_error  # type: ignore[misc]

    def _settle(self, operation: str) -> None:
        """Sleep for the contract's declared stabilization delay, if enabled."""
        if not self.apply_stabilization_delays:
            return
        delay = STABILIZATION_DELAYS_S.get(operation, 0.0)
        if delay:
            time.sleep(delay)

    @staticmethod
    def _check_status(command: int, response: bytes) -> None:
        status = response[3]
        if status == p.StatusCode.SUCCESS:
            return
        text = p.STATUS_TEXT.get(status, f"unknown status 0x{status:02X}")
        raise BK8500CommandError(
            f"Command 0x{int(command):02X} rejected by the instrument: {text}", status=status
        )

    def _write(self, command: int, payload: bytes = b"") -> None:
        """Send a command that returns only a status frame."""
        response = self._transact(command, payload)
        if response[2] != p.Command.STATUS:
            raise BK8500ProtocolError(
                f"Command 0x{int(command):02X} expected a status frame, "
                f"received command byte 0x{response[2]:02X}"
            )
        self._check_status(command, response)
        if self.settle_delay_s:
            time.sleep(self.settle_delay_s)

    def _note_response_style(self, style: str) -> None:
        """Record and log, once, how this firmware tags its data replies."""
        if self.response_style == style:
            return
        if self.response_style is not None:
            LOGGER.warning(
                "Instrument changed reply style from %s to %s", self.response_style, style
            )
        elif style == "status_tagged":
            LOGGER.warning(
                "This firmware tags data replies with command byte 0x12 rather than "
                "echoing the request. The driver reads the payload from byte 3 as the "
                "vendor's own examples do. Verify one known value before trusting a run."
            )
        self.response_style = style

    def _query(self, command: int, payload: bytes = b"") -> bytes:
        """Send a command that returns a data frame; return its 22 byte payload.

        Two reply framings are accepted. Most firmware echoes the request's
        command byte in a data reply, which is unambiguous. Some firmware tags
        every reply with the status command byte 0x12; the manual does not
        state which applies to read commands and the vendor's own examples read
        the payload from byte 3 without checking byte 2 at all. Rejecting the
        second form would make every read keyword fail on such an instrument,
        so it is accepted with a warning and recorded in ``response_style``.
        """
        response = self._transact(command, payload)
        if response[2] == int(command):
            self._note_response_style("echo")
            return response[3:25]
        if response[2] == p.Command.STATUS:
            status = response[3]
            if status in (
                p.StatusCode.CHECKSUM_INCORRECT,
                p.StatusCode.PARAMETER_INCORRECT,
                p.StatusCode.UNRECOGNISED_COMMAND,
                p.StatusCode.INVALID_COMMAND,
            ):
                self._check_status(command, response)  # raises BK8500CommandError
            if status == p.StatusCode.SUCCESS and not any(response[4:25]):
                # 0x80 followed by 21 zero bytes is indistinguishable from a
                # bare success status. Refuse to guess rather than return 0x80
                # counts as if it were a measurement.
                raise BK8500ProtocolError(
                    f"Ambiguous reply to command 0x{int(command):02X}: a status frame "
                    "reporting success carries no data, and the payload is empty. "
                    "The instrument may not support this read command."
                )
            self._note_response_style("status_tagged")
            return response[3:25]
        raise BK8500ProtocolError(
            f"Response command byte 0x{response[2]:02X} is neither the request "
            f"0x{int(command):02X} nor a status frame"
        )

    # ------------------------------------------------------------------
    # validation helpers
    # ------------------------------------------------------------------
    def _validate(self, value: float, low: float, high: float, name: str, unit: str) -> float:
        if isinstance(value, bool):
            raise BK8500ValidationError(f"{name} must be numeric, received boolean {value!r}")
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            raise BK8500ValidationError(f"{name} must be numeric, received {value!r}") from None
        if not low <= numeric <= high:
            raise BK8500ValidationError(
                f"{name} {numeric} {unit} outside the permitted range "
                f"{low} .. {high} {unit} for model {self._limits.model}"
            )
        return numeric

    def _validate_dwell(self, value: float, name: str) -> float:
        return self._validate(value, 0.0, MAX_DWELL_S, name, "s")

    def _setpoint_range(self, mode: LoadMode) -> tuple[float, float, str]:
        if mode == LoadMode.CC:
            return 0.0, self._limits.max_current_a, "A"
        if mode == LoadMode.CV:
            return 0.0, self._limits.max_voltage_v, "V"
        if mode == LoadMode.CW:
            return 0.0, self._limits.max_power_w, "W"
        return self._limits.min_resistance_ohm, self._limits.max_resistance_ohm, "ohm"

    # ------------------------------------------------------------------
    # control state
    # ------------------------------------------------------------------
    def set_remote_control(self, enabled: bool = True) -> None:
        """Command 0x20. Remote control is a precondition for every setting."""
        self._write(p.Command.SET_REMOTE, bytes([int(bool(enabled))]))
        self._remote = bool(enabled)

    def set_local_key_enabled(self, enabled: bool = True) -> None:
        """Command 0x55. Enable or disable the front panel LOCAL key."""
        self._write(p.Command.SET_LOCAL_KEY, bytes([int(bool(enabled))]))

    def set_input_state(self, on: bool) -> None:
        """Command 0x21. Connect (on) or disconnect (off) the load input.

        This is the only keyword that starts sinking current. It refuses to
        run unless remote control has been claimed in this session.
        """
        if on and not self._remote:
            raise BK8500StateError(
                "Refusing to enable the input: remote control has not been claimed. "
                "Call set_remote_control(True) first."
            )
        self._write(p.Command.SET_INPUT, bytes([int(bool(on))]))
        self._settle("input_state")

    def set_remote_sense(self, enabled: bool) -> None:
        """Command 0x56."""
        self._write(p.Command.SET_REMOTE_SENSE, bytes([int(bool(enabled))]))
        self._settle("remote_sense")

    def get_remote_sense(self) -> bool:
        """Command 0x57."""
        return bool(self._query(p.Command.GET_REMOTE_SENSE)[0])

    # ------------------------------------------------------------------
    # protection limits
    # ------------------------------------------------------------------
    def set_max_voltage(self, voltage_v: float) -> None:
        """Command 0x22. Instrument-side over-voltage limit."""
        value = self._validate(voltage_v, 0.0, self._limits.max_voltage_v, "Maximum voltage", "V")
        self._write(p.Command.SET_MAX_VOLTAGE, p.encode_int(value * p.COUNTS_PER_VOLT, 4))

    def get_max_voltage(self) -> float:
        """Command 0x23."""
        return p.decode_int(self._query(p.Command.GET_MAX_VOLTAGE)[:4]) / p.COUNTS_PER_VOLT

    def set_max_current(self, current_a: float) -> None:
        """Command 0x24. Instrument-side over-current limit."""
        value = self._validate(current_a, 0.0, self._limits.max_current_a, "Maximum current", "A")
        self._write(p.Command.SET_MAX_CURRENT, p.encode_int(value * p.COUNTS_PER_AMP, 4))

    def get_max_current(self) -> float:
        """Command 0x25."""
        return p.decode_int(self._query(p.Command.GET_MAX_CURRENT)[:4]) / p.COUNTS_PER_AMP

    def set_max_power(self, power_w: float) -> None:
        """Command 0x26. Instrument-side over-power limit."""
        value = self._validate(power_w, 0.0, self._limits.max_power_w, "Maximum power", "W")
        self._write(p.Command.SET_MAX_POWER, p.encode_int(value * p.COUNTS_PER_WATT, 4))

    def get_max_power(self) -> float:
        """Command 0x27."""
        return p.decode_int(self._query(p.Command.GET_MAX_POWER)[:4]) / p.COUNTS_PER_WATT

    def configure_protection(
        self,
        max_voltage_v: float | None = None,
        max_current_a: float | None = None,
        max_power_w: float | None = None,
    ) -> None:
        """Set every supplied protection limit in one call."""
        if max_voltage_v is not None:
            self.set_max_voltage(max_voltage_v)
        if max_current_a is not None:
            self.set_max_current(max_current_a)
        if max_power_w is not None:
            self.set_max_power(max_power_w)

    # ------------------------------------------------------------------
    # mode and setpoints
    # ------------------------------------------------------------------
    def set_mode(self, mode: LoadMode | str) -> LoadMode:
        """Command 0x28."""
        resolved = parse_enum(LoadMode, mode, "Mode")
        self._write(p.Command.SET_MODE, bytes([int(resolved)]))
        self._settle("mode")
        return resolved

    def get_mode(self) -> LoadMode:
        """Command 0x29."""
        return LoadMode(self._query(p.Command.GET_MODE)[0])

    def set_setpoint(self, mode: LoadMode | str, value: float) -> None:
        """Write the regulation level belonging to ``mode`` (0x2A/0x2C/0x2E/0x30)."""
        resolved = parse_enum(LoadMode, mode, "Mode")
        command, _, scale, unit = _MODE_SETPOINT_COMMANDS[resolved]
        low, high, _ = self._setpoint_range(resolved)
        checked = self._validate(value, low, high, f"{resolved.name} setpoint", unit)
        self._write(command, p.encode_int(checked * scale, 4))
        self._settle("setpoint")

    def get_setpoint(self, mode: LoadMode | str) -> float:
        """Read the regulation level belonging to ``mode`` (0x2B/0x2D/0x2F/0x31)."""
        resolved = parse_enum(LoadMode, mode, "Mode")
        _, command, scale, _ = _MODE_SETPOINT_COMMANDS[resolved]
        return p.decode_int(self._query(command)[:4]) / scale

    def apply_load(self, mode: LoadMode | str, value: float, enable_input: bool = False) -> None:
        """Select a mode, write its setpoint, and optionally close the input.

        Ordering matters on hardware: the setpoint is written before the input
        is enabled so the DUT never sees a stale level.
        """
        resolved = self.set_mode(mode)
        self.set_setpoint(resolved, value)
        self.set_function(LoadFunction.FIXED)
        if enable_input:
            self.set_input_state(True)

    # ------------------------------------------------------------------
    # function
    # ------------------------------------------------------------------
    def set_function(self, function: LoadFunction | str) -> LoadFunction:
        """Command 0x5D. FIXED / SHORT / TRANSIENT / LIST / BATTERY."""
        resolved = parse_enum(LoadFunction, function, "Function")
        if resolved == LoadFunction.SHORT:
            raise BK8500SafetyError(
                "SHORT function is not available through this keyword because it "
                "commands the maximum sink current the model supports. Use "
                "set_function_unchecked('SHORT') if the bench contract explicitly "
                "allows it."
            )
        self._write(p.Command.SET_FUNCTION, bytes([int(resolved)]))
        self._settle("function")
        return resolved

    def set_function_unchecked(self, function: LoadFunction | str) -> LoadFunction:
        """Set any function including SHORT. Bypasses the SHORT safety rule."""
        resolved = parse_enum(LoadFunction, function, "Function")
        self._write(p.Command.SET_FUNCTION, bytes([int(resolved)]))
        self._settle("function")
        return resolved

    def get_function(self) -> LoadFunction:
        """Command 0x5E."""
        return LoadFunction(self._query(p.Command.GET_FUNCTION)[0])

    # ------------------------------------------------------------------
    # transient
    # ------------------------------------------------------------------
    def set_transient(
        self,
        mode: LoadMode | str,
        level_a: float,
        dwell_a_s: float,
        level_b: float,
        dwell_b_s: float,
        operation: TransientOperation | str = TransientOperation.CONTINUOUS,
    ) -> None:
        """Commands 0x32/0x34/0x36/0x38. Configure A/B transient toggling."""
        resolved = parse_enum(LoadMode, mode, "Mode")
        op = parse_enum(TransientOperation, operation, "Transient operation")
        command, _, scale = _TRANSIENT_COMMANDS[resolved]
        low, high, unit = self._setpoint_range(resolved)
        a = self._validate(level_a, low, high, f"{resolved.name} transient level A", unit)
        b = self._validate(level_b, low, high, f"{resolved.name} transient level B", unit)
        ta = self._validate_dwell(dwell_a_s, "Transient dwell A")
        tb = self._validate_dwell(dwell_b_s, "Transient dwell B")
        payload = (
            p.encode_int(a * scale, 4)
            + p.encode_int(ta * p.COUNTS_PER_SECOND_DWELL, 2)
            + p.encode_int(b * scale, 4)
            + p.encode_int(tb * p.COUNTS_PER_SECOND_DWELL, 2)
            + bytes([int(op)])
        )
        self._write(command, payload)

    def get_transient(self, mode: LoadMode | str) -> TransientSettings:
        """Commands 0x33/0x35/0x37/0x39."""
        resolved = parse_enum(LoadMode, mode, "Mode")
        _, command, scale = _TRANSIENT_COMMANDS[resolved]
        data = self._query(command)
        return TransientSettings(
            mode=resolved,
            level_a=p.decode_int(data[0:4]) / scale,
            dwell_a_s=p.decode_int(data[4:6]) / p.COUNTS_PER_SECOND_DWELL,
            level_b=p.decode_int(data[6:10]) / scale,
            dwell_b_s=p.decode_int(data[10:12]) / p.COUNTS_PER_SECOND_DWELL,
            operation=TransientOperation(data[12]),
        )

    # ------------------------------------------------------------------
    # triggering
    # ------------------------------------------------------------------
    def set_trigger_source(self, source: TriggerSource | str) -> TriggerSource:
        """Command 0x58. IMMEDIATE (front panel) / EXTERNAL (rear TTL) / BUS."""
        resolved = parse_enum(TriggerSource, source, "Trigger source")
        self._write(p.Command.SET_TRIGGER_SOURCE, bytes([int(resolved)]))
        return resolved

    def get_trigger_source(self) -> TriggerSource:
        """Command 0x59."""
        return TriggerSource(self._query(p.Command.GET_TRIGGER_SOURCE)[0])

    def trigger(self) -> None:
        """Command 0x5A. Software trigger; only valid when the source is BUS."""
        self._write(p.Command.TRIGGER)

    # ------------------------------------------------------------------
    # list operation
    # ------------------------------------------------------------------
    def configure_list(
        self,
        mode: LoadMode | str,
        steps: list[tuple[float, float]],
        repeat: ListRepeat | str = ListRepeat.ONCE,
        name: str | None = None,
    ) -> None:
        """Program a complete list sequence (0x3A..0x49).

        ``steps`` is a list of ``(level, dwell_s)`` pairs in SI units. Step
        indices are 1-based on the wire and are generated from list order.
        """
        resolved = parse_enum(LoadMode, mode, "List mode")
        repetition = parse_enum(ListRepeat, repeat, "List repeat")
        if len(steps) < 2:
            raise BK8500ValidationError(
                f"A BK8500 list needs at least 2 steps; received {len(steps)}. "
                "Physical BK8500 firmware 1.84 rejects command 0x3E when the step count is 1."
            )
        if len(steps) > 1000:
            raise BK8500ValidationError(f"A list holds at most 1000 steps, received {len(steps)}")

        # The active EEPROM partition limits the volatile list length as well:
        # 1x1000, 2x500, 4x250 or 8x120 steps. Reading it before any write keeps
        # validation all-or-nothing and produces a useful local error instead of
        # an opaque 0x3E rejection from the instrument.
        partition = self.get_list_partition()
        capacity = {1: 1000, 2: 500, 4: 250, 8: 120}.get(partition)
        if capacity is None:
            raise BK8500ProtocolError(
                f"Instrument returned unsupported list partition {partition}; expected 1, 2, 4 or 8"
            )
        if len(steps) > capacity:
            raise BK8500ValidationError(
                f"List has {len(steps)} steps but partition {partition} allows at most {capacity}"
            )

        low, high, unit = self._setpoint_range(resolved)
        set_command, _, scale = _LIST_STEP_COMMANDS[resolved]

        # Validate the whole profile before writing anything. A rejection partway
        # through would leave the instrument holding a step count that disagrees
        # with the steps actually programmed, and the missing steps play back as
        # zero: silently wrong test data instead of a failure.
        checked: list[tuple[int, float, float]] = []
        if name is not None:
            self._check_list_name(name)
        for index, (level, dwell) in enumerate(steps, start=1):
            checked.append(
                (
                    index,
                    self._validate(level, low, high, f"List step {index} level", unit),
                    self._validate_dwell(dwell, f"List step {index} dwell"),
                )
            )

        # List editing is only safe with the input open. Claiming remote control
        # belongs to the caller, but opening the input here prevents accidental
        # reprogramming while a profile is actively sinking current.
        self.set_input_state(False)
        self._write(p.Command.SET_LIST_MODE, bytes([int(resolved)]))
        self._write(p.Command.SET_LIST_REPEAT, bytes([int(repetition)]))
        try:
            self._write(p.Command.SET_LIST_STEP_COUNT, p.encode_int(len(steps), 2))
        except BK8500CommandError as exc:
            raise BK8500CommandError(
                f"{exc}. Requested list step count={len(steps)}, mode={resolved.name}, "
                f"repeat={repetition.name}, partition={partition}, capacity={capacity}. "
                "The input was forced OFF before list editing; if this follows an EEPROM "
                "save/recall, allow the driver's persistence settle delay to complete.",
                status=exc.status,
            ) from exc
        for index, checked_level, checked_dwell in checked:
            payload = (
                p.encode_int(index, 2)
                + p.encode_int(checked_level * scale, 4)
                + p.encode_int(checked_dwell * p.COUNTS_PER_SECOND_DWELL, 2)
            )
            self._write(set_command, payload)
        if name is not None:
            self.set_list_name(name)

    def get_list_step(self, mode: LoadMode | str, index: int) -> ListStep:
        """Read back one list step (0x41/0x43/0x45/0x47)."""
        resolved = parse_enum(LoadMode, mode, "List mode")
        _, command, scale = _LIST_STEP_COMMANDS[resolved]
        if not 1 <= int(index) <= 1000:
            raise BK8500ValidationError(f"List step index {index} outside 1..1000")
        data = self._query(command, p.encode_int(int(index), 2))
        return ListStep(
            index=p.decode_int(data[0:2]),
            level=p.decode_int(data[2:6]) / scale,
            dwell_s=p.decode_int(data[6:8]) / p.COUNTS_PER_SECOND_DWELL,
        )

    def get_list_step_count(self) -> int:
        """Command 0x3F."""
        return p.decode_int(self._query(p.Command.GET_LIST_STEP_COUNT)[:2])

    @staticmethod
    def _check_list_name(name: str) -> bytes:
        encoded = str(name).encode("ascii", "ignore")
        if len(encoded) > 10:
            raise BK8500ValidationError(f"List name '{name}' exceeds 10 ASCII characters")
        return encoded

    def set_list_name(self, name: str) -> None:
        """Command 0x48. Up to 10 ASCII characters."""
        self._write(p.Command.SET_LIST_NAME, self._check_list_name(name).ljust(10, b"\x00"))

    def get_list_name(self) -> str:
        """Command 0x49."""
        return self._query(p.Command.GET_LIST_NAME)[:10].split(b"\x00")[0].decode("ascii", "replace")

    def set_list_partition(self, partition: int) -> None:
        """Command 0x4A. 1, 2, 4 or 8 files (1000/500/250/120 steps each)."""
        if int(partition) not in (1, 2, 4, 8):
            raise BK8500ValidationError(f"List partition must be 1, 2, 4 or 8; received {partition}")
        self._write(p.Command.SET_LIST_PARTITION, bytes([int(partition)]))

    def get_list_partition(self) -> int:
        """Command 0x4B. Return the active list-memory partition count."""
        return int(self._query(p.Command.GET_LIST_PARTITION)[0])

    def save_list_file(self, location: int) -> None:
        """Command 0x4C. Store the current list in an active partition slot."""
        location = int(location)
        partition = self.get_list_partition()
        if not 1 <= location <= partition:
            raise BK8500ValidationError(
                f"List file location {location} outside 1..{partition} for partition {partition}"
            )
        self._write(p.Command.SAVE_LIST_FILE, bytes([location]))
        self._settle("save_list_file")

    def recall_list_file(self, location: int) -> None:
        """Command 0x4D. Recall a list from an active partition slot."""
        location = int(location)
        partition = self.get_list_partition()
        if not 1 <= location <= partition:
            raise BK8500ValidationError(
                f"List file location {location} outside 1..{partition} for partition {partition}"
            )
        self._write(p.Command.RECALL_LIST_FILE, bytes([location]))
        self._settle("recall_list_file")

    # ------------------------------------------------------------------
    # battery test and LOAD ON timer
    # ------------------------------------------------------------------
    def set_battery_cutoff_voltage(self, voltage_v: float) -> None:
        """Command 0x4E. Minimum terminal voltage for the battery test."""
        value = self._validate(
            voltage_v, 0.0, self._limits.max_voltage_v, "Battery cut-off voltage", "V"
        )
        self._write(p.Command.SET_BATTERY_MIN_VOLTAGE, p.encode_int(value * p.COUNTS_PER_VOLT, 4))

    def get_battery_cutoff_voltage(self) -> float:
        """Command 0x4F."""
        return p.decode_int(self._query(p.Command.GET_BATTERY_MIN_VOLTAGE)[:4]) / p.COUNTS_PER_VOLT

    def set_load_on_timer(self, seconds: float) -> None:
        """Command 0x50. LOAD ON duration in whole seconds."""
        value = self._validate(seconds, 0, MAX_LOAD_ON_TIMER_S, "LOAD ON timer", "s")
        self._write(p.Command.SET_LOAD_ON_TIMER, p.encode_int(value, 2))

    def get_load_on_timer(self) -> float:
        """Command 0x51."""
        return float(p.decode_int(self._query(p.Command.GET_LOAD_ON_TIMER)[:2]))

    def set_load_on_timer_enabled(self, enabled: bool) -> None:
        """Command 0x52."""
        self._write(p.Command.SET_LOAD_ON_TIMER_STATE, bytes([int(bool(enabled))]))

    def get_load_on_timer_enabled(self) -> bool:
        """Command 0x53."""
        return bool(self._query(p.Command.GET_LOAD_ON_TIMER_STATE)[0])

    # ------------------------------------------------------------------
    # settings storage
    # ------------------------------------------------------------------
    def save_settings(self, register: int) -> None:
        """Command 0x5B. Registers 1..25."""
        if not 1 <= int(register) <= 25:
            raise BK8500ValidationError(f"Settings register {register} outside 1..25")
        self._write(p.Command.SAVE_SETTINGS, bytes([int(register)]))
        self._settle("save_settings")

    def recall_settings(self, register: int) -> None:
        """Command 0x5C. Registers 1..25."""
        if not 1 <= int(register) <= 25:
            raise BK8500ValidationError(f"Settings register {register} outside 1..25")
        self._write(p.Command.RECALL_SETTINGS, bytes([int(register)]))
        self._settle("recall_settings")

    # ------------------------------------------------------------------
    # measurement and identity
    # ------------------------------------------------------------------
    def measure(self) -> InputValues:
        """Command 0x5F. Voltage, current, power and both state registers."""
        data = self._query(p.Command.GET_INPUT_VALUES)
        operation_raw = data[12]
        demand_raw = p.decode_int(data[13:15])
        return InputValues(
            voltage_v=p.decode_int(data[0:4]) / p.COUNTS_PER_VOLT,
            current_a=p.decode_int(data[4:8]) / p.COUNTS_PER_AMP,
            power_w=p.decode_int(data[8:12]) / p.COUNTS_PER_WATT,
            operation_state=decode_bitfield(operation_raw, OPERATION_STATE_BITS),
            demand_state=decode_bitfield(demand_raw, DEMAND_STATE_BITS),
            operation_state_raw=operation_raw,
            demand_state_raw=demand_raw,
        )

    def get_product_info(self) -> ProductInfo:
        """Command 0x6A. Model, serial number and firmware version."""
        data = self._query(p.Command.GET_PRODUCT_INFO)
        if not any(data):
            raise BK8500ProtocolError(
                "Product-information reply contained an empty payload. This is the "
                "signature of an echoed 0x6A request rather than a device data reply. "
                "Check the selected COM port, RX wiring, adapter driver and DTR/RTS."
            )
        model = data[0:5].split(b"\x00")[0].decode("ascii", "replace").strip()
        firmware = f"{data[6]:X}.{data[5]:02X}"
        serial_number = data[7:17].split(b"\x00")[0].decode("ascii", "replace").strip()
        self._product_info = ProductInfo(
            model, serial_number, firmware, firmware_raw=(data[6], data[5])
        )
        return self._product_info

    # ------------------------------------------------------------------
    # derived helpers
    # ------------------------------------------------------------------
    def assert_no_protection_faults(self) -> InputValues:
        """Read the load and raise if any protection bit is asserted."""
        reading = self.measure()
        if reading.active_protections:
            raise BK8500ProtectionError(
                "Instrument reports active protection: "
                + ", ".join(reading.active_protections),
                faults=reading.active_protections,
            )
        return reading

    def wait_until_stable(
        self,
        quantity: str = "current",
        tolerance: float = 0.01,
        window_s: float = 1.0,
        timeout_s: float = 10.0,
        interval_s: float = 0.1,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> InputValues:
        """Poll until a measured quantity stays inside ``tolerance`` for ``window_s``.

        ``quantity`` is ``voltage``, ``current`` or ``power``. ``tolerance`` is
        the maximum absolute peak-to-peak spread allowed inside the window, in
        the quantity's SI unit. Raises :class:`BK8500StateError` on timeout.
        """
        attribute = {
            "voltage": "voltage_v",
            "current": "current_a",
            "power": "power_w",
        }.get(str(quantity).lower())
        if attribute is None:
            raise BK8500ValidationError(
                f"Quantity '{quantity}' must be one of voltage, current, power"
            )
        deadline = clock() + float(timeout_s)
        samples: list[tuple[float, float]] = []
        last: InputValues | None = None
        values: list[float] = []
        while clock() < deadline:
            last = self.measure()
            now = clock()
            samples.append((now, getattr(last, attribute)))
            observed_for = now - samples[0][0]
            values = [v for timestamp, v in samples if now - timestamp <= window_s]
            if observed_for >= window_s and max(values) - min(values) <= float(tolerance):
                return last
            # Keep one sample older than the window so the boundary stays reachable.
            samples = [(t, v) for t, v in samples if now - t <= window_s * 2]
            sleep(float(interval_s))
        spread = "no samples"
        if values:
            spread = f"last spread {max(values) - min(values):.6g}"
        raise BK8500StateError(
            f"{quantity} did not settle within {tolerance} over {window_s} s "
            f"(timeout {timeout_s} s, {spread})"
        )

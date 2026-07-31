"""Transports for the BK8500 driver.

Three implementations are provided:

* :class:`SerialTransport` -- the real instrument over RS-232 / USB-serial.
* :class:`SimulatedTransport` -- an in-process instrument model. It answers
  the full command set used by this driver so that suites can be developed,
  linted and regression-tested without hardware.
* :class:`Transport` -- the abstract base every transport implements.

The transport layer is deliberately dumb: it moves 26 byte frames and knows
nothing about units, modes or safety. All semantics live in
:mod:`bk8500_load.driver`.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from abc import ABC, abstractmethod
from typing import Final

from . import protocol as p
from .enums import (
    DEMAND_STATE_BITS,
    OPERATION_STATE_BITS,
    LoadFunction,
    LoadMode,
    TriggerSource,
)
from .exceptions import (
    BK8500ConfigurationError,
    BK8500ConnectionError,
    BK8500ProtocolError,
    BK8500TimeoutError,
)

LOGGER = logging.getLogger(__name__)

#: The manual permits exactly these four rates ("USB (Virtual COM) settings").
#: Higher rates are not supported by the instrument's firmware even when the
#: USB-serial adapter offers them.
SUPPORTED_BAUD_RATES: Final[tuple[int, ...]] = (4800, 9600, 19200, 38400)


class Transport(ABC):
    """Moves one 26 byte request and returns one 26 byte response."""

    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @property
    @abstractmethod
    def is_open(self) -> bool: ...

    @abstractmethod
    def transact(self, frame: bytes) -> bytes:
        """Send ``frame`` and return the 26 byte response frame."""

    @property
    def description(self) -> str:
        return self.__class__.__name__


class SerialTransport(Transport):
    """Real instrument on a serial port, using pyserial.

    The 8500 series rear panel DB9 carries **TTL** levels, not RS-232 levels,
    and is reached through the vendor's IT-E132B USB-to-TTL adapter. The manual
    requires that the DTR and RTS lines be asserted: the adapter takes part of
    its interface power and its enable from them, so a link with DTR or RTS low
    goes silent and every transaction times out.

    pyserial usually raises both lines on open, but that is a platform and
    driver dependent default, not a guarantee. This transport asserts them
    explicitly after opening and verifies the result, so a silent link fails
    with a message that names the cause instead of a bare timeout.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        timeout_s: float = 1.0,
        write_timeout_s: float = 1.0,
        assert_dtr: bool = True,
        assert_rts: bool = True,
        startup_delay_s: float = 1.0,
        discard_local_echo: bool = True,
        query_echo_grace_s: float = 0.05,
    ) -> None:
        if int(baudrate) not in SUPPORTED_BAUD_RATES:
            raise BK8500ConfigurationError(
                f"Baud rate {baudrate} is not supported by the 8500 series. "
                f"Permitted rates: {', '.join(str(rate) for rate in SUPPORTED_BAUD_RATES)}"
            )
        self.port = port
        self.baudrate = int(baudrate)
        self.timeout_s = float(timeout_s)
        self.write_timeout_s = float(write_timeout_s)
        self.assert_dtr = bool(assert_dtr)
        self.assert_rts = bool(assert_rts)
        self.startup_delay_s = max(float(startup_delay_s), 0.0)
        self.discard_local_echo = bool(discard_local_echo)
        self.query_echo_grace_s = max(float(query_echo_grace_s), 0.0)
        self._serial = None
        self._lock = threading.Lock()

    @property
    def description(self) -> str:
        return f"serial:{self.port}@{self.baudrate}"

    @property
    def signal_lines(self) -> dict[str, bool | None]:
        """Current DTR/RTS state, for diagnostics. ``None`` when unreadable."""
        if self._serial is None:
            return {"dtr": None, "rts": None}
        return {
            "dtr": getattr(self._serial, "dtr", None),
            "rts": getattr(self._serial, "rts", None),
        }

    def open(self) -> None:
        """Open the serial adapter using the vendor-compatible line sequence.

        The IT-E132/IT-E132B path used by the 8500 series is sensitive to DTR
        and RTS state during port initialisation.  Create the pyserial object
        closed, request both line states, open the port, reassert them, then
        allow the adapter and load to settle before the first transaction.
        """
        try:
            import serial  # imported lazily so the simulator needs no pyserial
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise BK8500ConnectionError(
                "pyserial is required for SerialTransport: pip install pyserial"
            ) from exc
        try:
            self._serial = serial.Serial(
                port=None,
                baudrate=self.baudrate,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=self.timeout_s,
                write_timeout=self.write_timeout_s,
                # No hardware handshaking: DTR and RTS are static enable lines
                # for the adapter, not flow control.
                rtscts=False,
                dsrdtr=False,
                xonxoff=False,
            )
            # Match the proven bench sequence: request line states before open.
            self._set_signal_lines()
            self._serial.port = self.port
            self._serial.open()
            # Some operating-system drivers rewrite the line states on open.
            self._apply_signal_lines()
            if self.startup_delay_s:
                time.sleep(self.startup_delay_s)
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
        except BK8500ConnectionError:
            self.close()
            raise
        except Exception as exc:  # serial.SerialException and friends
            self.close()
            raise BK8500ConnectionError(f"Cannot open {self.port}: {exc}") from exc

    def _set_signal_lines(self) -> None:
        """Request DTR/RTS states without requiring the port to be open."""
        for name, wanted in (("dtr", self.assert_dtr), ("rts", self.assert_rts)):
            try:
                setattr(self._serial, name, wanted)
            except Exception as exc:  # pragma: no cover - driver dependent
                raise BK8500ConnectionError(
                    f"Cannot set {name.upper()} on {self.port}: {exc}. The 8500 series "
                    f"requires DTR and RTS to be asserted; check the USB-serial driver."
                ) from exc

    def _apply_signal_lines(self) -> None:
        """Reassert DTR and RTS after open, then verify the resulting state."""
        self._set_signal_lines()
        actual = self.signal_lines
        for name, wanted in (("dtr", self.assert_dtr), ("rts", self.assert_rts)):
            if wanted and actual.get(name) is False:
                raise BK8500ConnectionError(
                    f"{name.upper()} did not assert on {self.port}. The 8500 series "
                    f"requires DTR and RTS asserted; without them the link is silent "
                    f"and every command times out."
                )
        LOGGER.debug("Signal lines on %s: %s", self.port, actual)

    def close(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            finally:
                self._serial = None

    @property
    def is_open(self) -> bool:
        return self._serial is not None and bool(self._serial.is_open)

    def _read_exactly_until(self, count: int, deadline: float) -> bytes:
        """Read exactly ``count`` bytes before ``deadline``."""
        received = bytearray()
        while len(received) < count:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            # Keep each pyserial read bounded by the remaining overall budget.
            previous_timeout = self._serial.timeout
            self._serial.timeout = min(self.timeout_s, remaining)
            try:
                chunk = self._serial.read(count - len(received))
            finally:
                self._serial.timeout = previous_timeout
            if chunk:
                received.extend(chunk)
        return bytes(received)

    def transact(self, frame: bytes) -> bytes:
        """Send one packet and return the device response.

        Some USB-to-TTL paths locally echo the transmitted 26-byte packet
        before the instrument response. For writes, an exact copy can never be
        a valid response because the 8500 protocol requires command 0x12.
        For reads, an all-zero result can occasionally equal the request, so a
        short grace window is used to detect a second frame before accepting the
        first one as data.
        """
        if not self.is_open:
            raise BK8500ConnectionError(f"Port {self.port} is not open")
        deadline = time.monotonic() + self.timeout_s
        echo_seen = False
        with self._lock:
            self._serial.reset_input_buffer()
            self._serial.write(frame)
            self._serial.flush()
            while True:
                response = self._read_exactly_until(p.PACKET_LENGTH, deadline)
                if len(response) != p.PACKET_LENGTH:
                    detail = (
                        " An exact local echo was received, but no device response followed."
                        if echo_seen
                        else ""
                    )
                    raise BK8500TimeoutError(
                        f"Expected {p.PACKET_LENGTH} response bytes from {self.port} within "
                        f"{self.timeout_s} s, received {len(response)}.{detail}"
                    )

                command = frame[2]
                if self.discard_local_echo and response == frame:
                    echo_seen = True
                    if p.command_expects_status(command):
                        LOGGER.warning(
                            "Discarded exact local echo on %s for write command 0x%02X; "
                            "waiting for the instrument status frame",
                            self.port,
                            command,
                        )
                        continue

                    # A query can legitimately return an all-zero payload that
                    # is byte-identical to the request. Briefly look for a
                    # second frame; if none arrives, return the first and let
                    # command-specific validation decide whether it is valid.
                    grace_deadline = min(
                        deadline, time.monotonic() + self.query_echo_grace_s
                    )
                    second = self._read_exactly_until(p.PACKET_LENGTH, grace_deadline)
                    if len(second) == p.PACKET_LENGTH:
                        LOGGER.warning(
                            "Discarded exact local echo on %s for query command 0x%02X; "
                            "using the following device response",
                            self.port,
                            command,
                        )
                        return bytes(second)
                    return bytes(response)

                return bytes(response)


class SimulatedTransport(Transport):
    """In-process model of an 8500 series load.

    The model implements the register set this driver uses, applies the
    instrument's unit scaling, and computes input readings from a Thevenin
    source (``source_voltage_v`` behind ``source_resistance_ohm``) so that
    measurement keywords return physically consistent values.

    It is a development and regression aid, not a metrological model: no
    noise, slew rate, thermal behaviour or timing is simulated.
    """

    def __init__(
        self,
        model: str = "8500",
        serial_number: str = "SIM0000001",
        firmware_version: str = "1.05",
        source_voltage_v: float = 12.0,
        source_resistance_ohm: float = 0.05,
        address: int = 0,
    ) -> None:
        self.model = model
        self.serial_number = serial_number
        self.firmware_version = firmware_version
        self.source_voltage_v = float(source_voltage_v)
        self.source_resistance_ohm = max(float(source_resistance_ohm), 1e-6)
        self.address = int(address)
        self._open = False
        self.frame_log: list[tuple[bytes, bytes]] = []
        self.reset()

    # -- lifecycle ---------------------------------------------------------
    def reset(self) -> None:
        """Return the simulated instrument to its power-on state."""
        self.registers: dict[int, int] = {
            p.Command.SET_MAX_VOLTAGE: int(120 * p.COUNTS_PER_VOLT),
            p.Command.SET_MAX_CURRENT: int(30 * p.COUNTS_PER_AMP),
            p.Command.SET_MAX_POWER: int(300 * p.COUNTS_PER_WATT),
            p.Command.SET_CC_CURRENT: 0,
            p.Command.SET_CV_VOLTAGE: 0,
            p.Command.SET_CW_POWER: 0,
            p.Command.SET_CR_RESISTANCE: int(10 * p.COUNTS_PER_OHM),
            p.Command.SET_BATTERY_MIN_VOLTAGE: 0,
            p.Command.SET_LOAD_ON_TIMER: 0,
            p.Command.SET_LIST_STEP_COUNT: 0,
        }
        self.remote = False
        self.input_on = False
        self.local_key = True
        self.remote_sense = False
        self.load_on_timer_state = False
        self.mode = LoadMode.CC
        self.function = LoadFunction.FIXED
        self.trigger_source = TriggerSource.IMMEDIATE
        self.triggered = False
        self.list_mode = LoadMode.CC
        self.list_repeat = 0
        self.list_partition = 8
        self.list_name = "SIMLIST"
        self.list_steps: dict[int, tuple[int, int]] = {}
        self.list_files: dict[int, dict] = {}
        self.transients: dict[int, bytes] = {}
        self.settings_registers: dict[int, dict] = {}

    def open(self) -> None:
        self._open = True

    def close(self) -> None:
        self._open = False

    @property
    def is_open(self) -> bool:
        return self._open

    @property
    def description(self) -> str:
        return f"simulated:{self.model}"

    # -- physics -----------------------------------------------------------
    def _operating_point(self) -> tuple[float, float]:
        """Return ``(voltage_v, current_a)`` at the input terminals."""
        vs = self.source_voltage_v
        rs = self.source_resistance_ohm
        if not self.input_on:
            return vs, 0.0
        if self.function == LoadFunction.BATTERY and vs <= 0:
            return vs, 0.0
        if self.function == LoadFunction.SHORT:
            return 0.0, vs / rs
        if self.mode == LoadMode.CC:
            current = self.registers[p.Command.SET_CC_CURRENT] / p.COUNTS_PER_AMP
            current = min(current, vs / rs)
        elif self.mode == LoadMode.CV:
            target = self.registers[p.Command.SET_CV_VOLTAGE] / p.COUNTS_PER_VOLT
            target = min(target, vs)
            current = max((vs - target) / rs, 0.0)
        elif self.mode == LoadMode.CW:
            power = self.registers[p.Command.SET_CW_POWER] / p.COUNTS_PER_WATT
            discriminant = vs * vs - 4 * rs * power
            current = (vs - math.sqrt(discriminant)) / (2 * rs) if discriminant >= 0 else vs / (2 * rs)
        else:  # CR
            resistance = max(self.registers[p.Command.SET_CR_RESISTANCE] / p.COUNTS_PER_OHM, 1e-6)
            current = vs / (resistance + rs)
        current = max(current, 0.0)
        voltage = max(vs - current * rs, 0.0)
        return voltage, current

    def _state_registers(self, voltage: float, current: float) -> tuple[int, int]:
        operation = 0
        for bit, name in enumerate(OPERATION_STATE_BITS):
            value = {
                "remote_control_enabled": self.remote,
                "input_on": self.input_on,
                "local_key_enabled": self.local_key,
                "remote_sense_enabled": self.remote_sense,
                "load_on_timer_enabled": self.load_on_timer_state,
                "waiting_for_trigger": self.function == LoadFunction.TRANSIENT
                and self.trigger_source == TriggerSource.BUS
                and not self.triggered,
            }.get(name, False)
            operation |= int(bool(value)) << bit

        power = voltage * current
        flags = {
            "over_voltage": voltage > self.registers[p.Command.SET_MAX_VOLTAGE] / p.COUNTS_PER_VOLT,
            "over_current": current > self.registers[p.Command.SET_MAX_CURRENT] / p.COUNTS_PER_AMP,
            "over_power": power > self.registers[p.Command.SET_MAX_POWER] / p.COUNTS_PER_WATT,
            "constant_current": self.input_on and self.mode == LoadMode.CC,
            "constant_voltage": self.input_on and self.mode == LoadMode.CV,
            "constant_power": self.input_on and self.mode == LoadMode.CW,
            "constant_resistance": self.input_on and self.mode == LoadMode.CR,
        }
        demand = 0
        for bit, name in enumerate(DEMAND_STATE_BITS):
            demand |= int(bool(flags.get(name, False))) << bit
        return operation, demand

    # -- frame handling ----------------------------------------------------
    def transact(self, frame: bytes) -> bytes:
        if not self._open:
            raise BK8500ConnectionError("Simulated transport is not open")
        ok, reason = p.frame_is_well_formed(frame)
        if not ok:
            raise BK8500ProtocolError(f"Simulator rejected request frame: {reason}")
        if frame[1] != self.address:
            response = self._status(p.StatusCode.UNRECOGNISED_COMMAND)
        else:
            response = self._dispatch(frame)
        self.frame_log.append((frame, response))
        return response

    def _status(self, code: int) -> bytes:
        return p.build_frame(self.address, p.Command.STATUS, bytes([int(code)]))

    def _data(self, command: int, payload: bytes) -> bytes:
        return p.build_frame(self.address, command, payload)

    def _dispatch(self, frame: bytes) -> bytes:  # noqa: C901 - flat command table
        command = frame[2]
        data = frame[3:25]
        C = p.Command
        try:
            command = C(command)
        except ValueError:
            return self._status(p.StatusCode.INVALID_COMMAND)

        # --- writes that map straight onto a scaled register --------------
        scaled_writes = {
            C.SET_MAX_VOLTAGE: 4,
            C.SET_MAX_CURRENT: 4,
            C.SET_MAX_POWER: 4,
            C.SET_CC_CURRENT: 4,
            C.SET_CV_VOLTAGE: 4,
            C.SET_CW_POWER: 4,
            C.SET_CR_RESISTANCE: 4,
            C.SET_BATTERY_MIN_VOLTAGE: 4,
            C.SET_LOAD_ON_TIMER: 2,
        }
        read_back = {
            C.GET_MAX_VOLTAGE: (C.SET_MAX_VOLTAGE, 4),
            C.GET_MAX_CURRENT: (C.SET_MAX_CURRENT, 4),
            C.GET_MAX_POWER: (C.SET_MAX_POWER, 4),
            C.GET_CC_CURRENT: (C.SET_CC_CURRENT, 4),
            C.GET_CV_VOLTAGE: (C.SET_CV_VOLTAGE, 4),
            C.GET_CW_POWER: (C.SET_CW_POWER, 4),
            C.GET_CR_RESISTANCE: (C.SET_CR_RESISTANCE, 4),
            C.GET_BATTERY_MIN_VOLTAGE: (C.SET_BATTERY_MIN_VOLTAGE, 4),
            C.GET_LOAD_ON_TIMER: (C.SET_LOAD_ON_TIMER, 2),
            C.GET_LIST_STEP_COUNT: (C.SET_LIST_STEP_COUNT, 2),
        }
        if command == C.SET_LIST_STEP_COUNT:
            count = p.decode_int(data[:2])
            capacity = {1: 1000, 2: 500, 4: 250, 8: 120}[self.list_partition]
            if not 2 <= count <= capacity:
                return self._status(p.StatusCode.PARAMETER_INCORRECT)
            self.registers[command] = count
            return self._status(p.StatusCode.SUCCESS)
        if command in scaled_writes:
            width = scaled_writes[command]
            self.registers[command] = p.decode_int(data[:width])
            return self._status(p.StatusCode.SUCCESS)
        if command in read_back:
            source, width = read_back[command]
            return self._data(command, p.encode_int(self.registers[source], width))

        # --- discrete state ------------------------------------------------
        if command == C.SET_REMOTE:
            self.remote = bool(data[0])
            return self._status(p.StatusCode.SUCCESS)
        if command == C.SET_INPUT:
            if not self.remote:
                return self._status(p.StatusCode.UNRECOGNISED_COMMAND)
            self.input_on = bool(data[0])
            return self._status(p.StatusCode.SUCCESS)
        if command == C.SET_MODE:
            if data[0] not in (m.value for m in LoadMode):
                return self._status(p.StatusCode.PARAMETER_INCORRECT)
            self.mode = LoadMode(data[0])
            return self._status(p.StatusCode.SUCCESS)
        if command == C.GET_MODE:
            return self._data(command, bytes([int(self.mode)]))
        if command == C.SET_FUNCTION:
            if data[0] not in (f.value for f in LoadFunction):
                return self._status(p.StatusCode.PARAMETER_INCORRECT)
            self.function = LoadFunction(data[0])
            self.triggered = False
            return self._status(p.StatusCode.SUCCESS)
        if command == C.GET_FUNCTION:
            return self._data(command, bytes([int(self.function)]))
        if command == C.SET_TRIGGER_SOURCE:
            if data[0] not in (t.value for t in TriggerSource):
                return self._status(p.StatusCode.PARAMETER_INCORRECT)
            self.trigger_source = TriggerSource(data[0])
            return self._status(p.StatusCode.SUCCESS)
        if command == C.GET_TRIGGER_SOURCE:
            return self._data(command, bytes([int(self.trigger_source)]))
        if command == C.TRIGGER:
            if self.trigger_source != TriggerSource.BUS:
                return self._status(p.StatusCode.UNRECOGNISED_COMMAND)
            self.triggered = True
            return self._status(p.StatusCode.SUCCESS)
        if command == C.SET_LOCAL_KEY:
            self.local_key = bool(data[0])
            return self._status(p.StatusCode.SUCCESS)
        if command == C.SET_REMOTE_SENSE:
            self.remote_sense = bool(data[0])
            return self._status(p.StatusCode.SUCCESS)
        if command == C.GET_REMOTE_SENSE:
            return self._data(command, bytes([int(self.remote_sense)]))
        if command == C.SET_LOAD_ON_TIMER_STATE:
            self.load_on_timer_state = bool(data[0])
            return self._status(p.StatusCode.SUCCESS)
        if command == C.GET_LOAD_ON_TIMER_STATE:
            return self._data(command, bytes([int(self.load_on_timer_state)]))

        # --- transient ------------------------------------------------------
        if command in (C.SET_CC_TRANSIENT, C.SET_CV_TRANSIENT, C.SET_CW_TRANSIENT, C.SET_CR_TRANSIENT):
            self.transients[int(command)] = bytes(data[:13])
            return self._status(p.StatusCode.SUCCESS)
        if command in (C.GET_CC_TRANSIENT, C.GET_CV_TRANSIENT, C.GET_CW_TRANSIENT, C.GET_CR_TRANSIENT):
            stored = self.transients.get(int(command) - 1, bytes(13))
            return self._data(command, stored)

        # --- list -----------------------------------------------------------
        if command == C.SET_LIST_MODE:
            self.list_mode = LoadMode(data[0])
            return self._status(p.StatusCode.SUCCESS)
        if command == C.GET_LIST_MODE:
            return self._data(command, bytes([int(self.list_mode)]))
        if command == C.SET_LIST_REPEAT:
            self.list_repeat = data[0]
            return self._status(p.StatusCode.SUCCESS)
        if command == C.GET_LIST_REPEAT:
            return self._data(command, bytes([self.list_repeat]))
        if command in (
            C.SET_LIST_STEP_CURRENT,
            C.SET_LIST_STEP_VOLTAGE,
            C.SET_LIST_STEP_POWER,
            C.SET_LIST_STEP_RESISTANCE,
        ):
            index = p.decode_int(data[0:2])
            self.list_steps[index] = (p.decode_int(data[2:6]), p.decode_int(data[6:8]))
            return self._status(p.StatusCode.SUCCESS)
        if command in (
            C.GET_LIST_STEP_CURRENT,
            C.GET_LIST_STEP_VOLTAGE,
            C.GET_LIST_STEP_POWER,
            C.GET_LIST_STEP_RESISTANCE,
        ):
            index = p.decode_int(data[0:2])
            level, dwell = self.list_steps.get(index, (0, 0))
            payload = p.encode_int(index, 2) + p.encode_int(level, 4) + p.encode_int(dwell, 2)
            return self._data(command, payload)
        if command == C.SET_LIST_NAME:
            self.list_name = data[:10].split(b"\x00")[0].decode("ascii", "replace")
            return self._status(p.StatusCode.SUCCESS)
        if command == C.GET_LIST_NAME:
            return self._data(command, self.list_name.encode("ascii")[:10].ljust(10, b"\x00"))
        if command == C.SET_LIST_PARTITION:
            if data[0] not in (1, 2, 4, 8):
                return self._status(p.StatusCode.PARAMETER_INCORRECT)
            self.list_partition = data[0]
            return self._status(p.StatusCode.SUCCESS)
        if command == C.GET_LIST_PARTITION:
            return self._data(command, bytes([self.list_partition]))
        if command == C.SAVE_LIST_FILE:
            location = data[0]
            if not 1 <= location <= self.list_partition:
                return self._status(p.StatusCode.PARAMETER_INCORRECT)
            self.list_files[location] = {
                "mode": self.list_mode,
                "repeat": self.list_repeat,
                "count": self.registers[C.SET_LIST_STEP_COUNT],
                "name": self.list_name,
                "steps": dict(self.list_steps),
            }
            return self._status(p.StatusCode.SUCCESS)
        if command == C.RECALL_LIST_FILE:
            location = data[0]
            if location not in self.list_files:
                return self._status(p.StatusCode.PARAMETER_INCORRECT)
            stored = self.list_files[location]
            self.list_mode = stored["mode"]
            self.list_repeat = stored["repeat"]
            self.registers[C.SET_LIST_STEP_COUNT] = stored["count"]
            self.list_name = stored["name"]
            self.list_steps = dict(stored["steps"] )
            return self._status(p.StatusCode.SUCCESS)

        # --- store / recall --------------------------------------------------
        if command == C.SAVE_SETTINGS:
            if not 1 <= data[0] <= 25:
                return self._status(p.StatusCode.PARAMETER_INCORRECT)
            self.settings_registers[data[0]] = dict(self.registers)
            return self._status(p.StatusCode.SUCCESS)
        if command == C.RECALL_SETTINGS:
            if data[0] not in self.settings_registers:
                return self._status(p.StatusCode.PARAMETER_INCORRECT)
            self.registers.update(self.settings_registers[data[0]])
            return self._status(p.StatusCode.SUCCESS)
        if command == C.SET_ADDRESS:
            self.address = data[0]
            return self._status(p.StatusCode.SUCCESS)

        # --- measurement and identity ---------------------------------------
        if command == C.GET_INPUT_VALUES:
            voltage, current = self._operating_point()
            operation, demand = self._state_registers(voltage, current)
            payload = (
                p.encode_int(round(voltage * p.COUNTS_PER_VOLT), 4)
                + p.encode_int(round(current * p.COUNTS_PER_AMP), 4)
                + p.encode_int(round(voltage * current * p.COUNTS_PER_WATT), 4)
                + bytes([operation])
                + p.encode_int(demand, 2)
            )
            return self._data(command, payload)
        if command == C.GET_PRODUCT_INFO:
            major, _, minor = self.firmware_version.partition(".")
            payload = self.model.encode("ascii")[:5].ljust(5, b"\x00")
            payload += bytes([int(minor or 0, 16) & 0xFF, int(major) & 0xFF])
            payload += self.serial_number.encode("ascii")[:10].ljust(10, b"\x00")
            return self._data(command, payload)

        return self._status(p.StatusCode.INVALID_COMMAND)

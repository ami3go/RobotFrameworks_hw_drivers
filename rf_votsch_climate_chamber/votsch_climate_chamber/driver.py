"""Industrial-hardened, API-compatible ClimateChamber driver.

This module keeps the public API of the original ClimateChamber.py while
hardening the implementation for long-running use:

- reconnecting TCP socket layer
- sendall() instead of send()
- response framing until protocol terminator
- robust protocol parsing
- optional write verification by readback
- finite wait support in set_and_wait()
- logging instead of print-only operation
- thread-safe high-level operations

The legacy API remains available:

    ClimateChamber(ip, temperature_min, temperature_max, timeout=1, temp_round=2)
    chamber.temperature_measured
    chamber.temperature_set_point = 25
    chamber.start()
    chamber.stop()
    chamber.set_and_wait(25, 10)
    chamber.query(...)
    chamber.query_command_low_level(...)

New safety/reliability options are keyword-only, so existing positional calls
continue to work.
"""

from __future__ import annotations

import contextlib
import datetime
import logging
import math
import socket
import time
from collections.abc import Callable
from threading import RLock
from typing import Any, cast

try:  # Keep old colored console output if colorama is installed.
    from colorama import Fore, Style  # type: ignore[import-untyped]
except Exception:  # pragma: no cover - only used when colorama is absent.
    class _NoColor:
        BLUE = ""
        YELLOW = ""
        GREEN = ""
        RED = ""
        RESET_ALL = ""

    Fore = _NoColor()
    Style = _NoColor()


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ClimateChamberError(RuntimeError):
    """Base class for climate-chamber runtime errors."""


class ClimateChamberCommunicationError(ClimateChamberError):
    """Raised when TCP communication with the chamber fails."""


class ClimateChamberProtocolError(ClimateChamberError):
    """Raised when the chamber response cannot be parsed safely."""


class ClimateChamberCommandError(ClimateChamberError):
    """Raised when the chamber reports command execution failure."""


class ClimateChamberTimeoutError(ClimateChamberError, TimeoutError):
    """Raised when a chamber operation exceeds its configured timeout."""


class ClimateChamberSafetyError(ValueError):
    """Raised for unsafe user input such as invalid temperature limits."""


# ---------------------------------------------------------------------------
# Support functions kept for API compatibility
# ---------------------------------------------------------------------------


def range_check(val, min, max, val_name):  # noqa: A002 - keep old API name.
    """Clamp *val* to [min, max]. Kept for compatibility with old code."""
    if val > max:
        print(f"Wrong {val_name}: {val}. Max value should be < {max}")
        val = max
    if val < min:
        print(f"Wrong {val_name}: {val}. Should be >= {min}")
        val = min
    return val


def check_tolerance(value, target, tolerance=0.1):
    """Return True when *value* is within +/- *tolerance* of *target*."""
    return float(target) - float(tolerance) <= float(value) <= float(target) + float(tolerance)


def get_time():
    """Return local time formatted for progress messages."""
    t = datetime.datetime.now()
    return f"{t.hour:02d}:{t.minute:02d}:{t.second:02d}"


# ---------------------------------------------------------------------------
# Command dictionary from the original implementation
# ---------------------------------------------------------------------------


def _generate_list_of_all_possible_commands(dictionary):
    """Generate a sorted list of all command names from COMMANDS_DICT."""
    if not isinstance(dictionary, dict):
        return [""]

    return_list = []
    for key, value in dictionary.items():
        sub_keys = _generate_list_of_all_possible_commands(value)
        for sub_key in sub_keys:
            command = f"{key} {sub_key}".strip()
            return_list.append(command)
    return sorted(return_list)


COMMANDS_DICT = {
    # This dictionary was created by Izaak, see original code references.
    'GET': {
        'CHAMBER': {
            'INFO': 99997,
            'STATUS': 10012,
        },
        'CONTROL_VARIABLE': {
            'NUMBER_OF': 11018,
            'NAME': 11026,
            'UNIT': 11023,
            'SET_POINT': 11002,
            'ACTUAL_VALUE': 11004,
            'INPUT_LIMIT_MIN': 11007,
            'INPUT_LIMIT_MAX': 11009,
            'WARNING_LIMIT_MIN': 11016,
            'WARNING_LIMIT_MAX': 11017,
            'ALARM_LIMIT_MIN': 11014,
            'ALARM_LIMIT_MAX': 11015,
        },
        'CONTROL_VALUE': {
            'NAME': 13011,
            'UNIT': 13010,
            'SET_POINT': 13005,
            'INPUT_LIMIT_MIN': 13002,
            'INPUT_LIMIT_MAX': 13004,
        },
        'MEASURED_VALUE': {
            'NUMBER_OF': 12012,
            'NAME': 12019,
            'UNIT': 12016,
            'ACTUAL_VALUE': 12002,
            'WARNING_LIMIT_MIN': 12010,
            'WARNING_LIMIT_MAX': 12011,
            'ALARM_LIMIT_MIN': 12008,
            'ALARM_LIMIT_MAX': 12009,
        },
        'DIGITAL_IN': {
            'NUMBER_OF': 15004,
            'NAME': 15005,
            'VALUE': 15002,
        },
        'DIGITAL_OUT': {
            'NUMBER_OF': 14007,
            'NAME': 14010,
            'VALUE': 14003,
        },
        'MESSAGE': {
            'NUMBER_OF': 17002,
            'TEXT': 17007,
            'TYPE': 17005,
            'CATEGORY': 17111,
            'STATUS': 17009,
        },
        'ERROR': {},
        'GRADIENT_UP': {
            'VALUE': 11066,
        },
        'GRADIENT_DOWN': {
            'VALUE': 11070,
        },
        'PROGRAM': {
            'NUMBER': 19204,
            'NAME': 19031,
            'TOTAL_LOOPS': 19004,
            'COMPLETED_LOOPS': 19006,
            'START_DATETIME': 19208,
            'LEAD_TIME': 19010,
            'ACTIVE_TIME': 19021,
            'STATUS': 19210,
        },
    },
    'SET': {
        'CONTROL_VARIABLE': {
            'SET_POINT': 11001,
        },
        'CONTROL_VALUE': {
            'SET_POINT': 13006,
        },
        'DIGITAL_OUT': {
            'VALUE': 14001,
        },
        'GRADIENT_UP': {
            'VALUE': 11068,
        },
        'GRADIENT_DOWN': {
            'VALUE': 11072,
        },
        'PROGRAM': {
            'CONTROL': 19209,
            'TOTAL_LOOPS': 19003,
            'START_DATE': 19207,
        },
    },
    'START': {
        'MANUAL_MODE': 14001,
        'PROGRAM': 19014,
    },
    'STOP': {
        'PROGRAM': 19015,
    },
    'RESET': {
        'ERRORS': 17012,
    },
}
COMMANDS_LIST = _generate_list_of_all_possible_commands(COMMANDS_DICT)


# ---------------------------------------------------------------------------
# Validation / protocol helpers
# ---------------------------------------------------------------------------


def _validate_type(var, var_name, typ):
    if not isinstance(var, typ):
        raise TypeError(
            f'<{var_name}> must be of type {typ}, received object of type {type(var)}.'
        )


def _to_float(var, var_name) -> float:
    """Convert *var* to float or raise TypeError with a clear message."""
    if isinstance(var, bool):
        raise TypeError(f'Cannot interpret <{var_name}> as a float number, received bool.')
    msg = f'Cannot interpret <{var_name}> as a float number, received object of type {type(var)}.'
    try:
        return float(var)
    except (TypeError, ValueError) as exc:
        raise TypeError(msg) from exc


def _validate_float(var, var_name):
    """Validate that *var* can be interpreted as a float.

    Unlike the original implementation, this now matches the old docstring and
    accepts numeric strings such as "3.14".
    """
    _to_float(var, var_name)


def _format_float_for_chamber(value: float) -> str:
    """Format floats without locale dependence or unnecessary noise."""
    return format(float(value), ".10g")


def _normalize_command_name(command_name: str) -> str:
    return " ".join(command_name.upper().split())


def create_command_string(command_number: str, *arguments):
    """Create the byte string that must be sent to the chamber.

    Kept API-compatible with the original function.
    """
    _validate_type(command_number, 'command_number', str)

    if not command_number.isdigit() or len(command_number) != 5:
        raise ValueError(
            f'<command_number> must be a string containing a 5 digit integer number, '
            f'received {command_number!r}.'
        )

    if len(arguments) > 4:
        raise ValueError(f'The maximum number of arguments is 4, but received {len(arguments)}.')

    chamber_index = '1'  # According to the protocol this can always be 1.
    separator = b'\xb6'  # 182 decimal, rendered as "¶" in latin-1.
    parts = [command_number, chamber_index] + [str(arg) for arg in arguments]

    for arg in parts:
        if '\r' in arg or '\n' in arg:
            raise ValueError(f'Command argument contains line terminator: {arg!r}')
        if '¶' in arg:
            raise ValueError(f'Command argument contains protocol separator character: {arg!r}')
        try:
            arg.encode('ascii')
        except UnicodeEncodeError as exc:
            raise ValueError(f'Command argument must be ASCII-compatible: {arg!r}') from exc

    return separator.join(part.encode('ascii') for part in parts) + b'\r'


def translate_command_name_to_command_number(command_name: str):
    """Translate a human-readable command name to its 5-digit command number."""
    _validate_type(command_name, 'command_name', str)
    command_name = _normalize_command_name(command_name)

    def recursive_search(commands_dict, name_parts):
        if not name_parts:
            return None
        current = name_parts[0]
        if current not in commands_dict:
            return None
        value = commands_dict[current]
        if isinstance(value, dict):
            return recursive_search(value, name_parts[1:])
        if len(name_parts) == 1:
            return value
        return None

    command_number = recursive_search(COMMANDS_DICT, command_name.split(' '))
    if command_number is None:
        raise ValueError(
            f'Invalid command "{command_name}". This is a list of all possible command names: '
            f'{COMMANDS_LIST}.'
        )
    return str(command_number)


# ---------------------------------------------------------------------------
# Climate chamber class
# ---------------------------------------------------------------------------


class ClimateChamber:
    """TCP driver for a Vötsch/SimServ compatible climate chamber.

    Existing positional arguments are unchanged. New production options are
    keyword-only and therefore do not break old code.
    """

    COMMANDS_DICT = COMMANDS_DICT
    COMMANDS_LIST = COMMANDS_LIST

    def __init__(
        self,
        ip: str,
        temperature_min: float,
        temperature_max: float,
        timeout=1,
        temp_round=2,
        *,
        port: int = 2049,
        auto_reconnect: bool = True,
        retries: int = 2,
        retry_delay: float = 0.5,
        retry_backoff: float = 1.5,
        response_timeout: float | None = None,
        max_response_bytes: int = 4096,
        verify_writes: bool = True,
        state_change_timeout: float = 10.0,
        state_settle_delay: float = 1.0,
        setpoint_verify_tolerance: float = 0.05,
        tcp_keepalive: bool = True,
        connect_on_init: bool = True,
        socket_factory: Callable[[tuple[str, int], float], socket.socket] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        logger: logging.Logger | None = None,
    ):
        """Create an object and start the network connection.

        Parameters compatible with the original API:
            ip: chamber IP address or hostname.
            temperature_min: local software safety limit.
            temperature_max: local software safety limit.
            timeout: socket connect/read timeout in seconds.
            temp_round: rounding used by temperature_measured.

        New keyword-only options:
            auto_reconnect: reconnect and retry after broken TCP connections.
            retries: command retry attempts after communication failure.
            verify_writes: verify set/start/stop/output commands by readback.
            response_timeout: total time allowed to receive a response frame.
        """
        _validate_type(ip, 'ip', str)
        self._ip = ip
        self._port = int(port)
        self._timeout = float(timeout)
        self._response_timeout = float(response_timeout) if response_timeout is not None else float(timeout)
        self._max_response_bytes = int(max_response_bytes)
        self._auto_reconnect = bool(auto_reconnect)
        self._retries = int(retries)
        self._retry_delay = float(retry_delay)
        self._retry_backoff = float(retry_backoff)
        self._verify_writes = bool(verify_writes)
        self._state_change_timeout = float(state_change_timeout)
        self._state_settle_delay = float(state_settle_delay)
        self._setpoint_verify_tolerance = float(setpoint_verify_tolerance)
        self._tcp_keepalive = bool(tcp_keepalive)
        self._connect_on_init = bool(connect_on_init)
        self._socket_factory = socket_factory or (
            lambda address, connection_timeout: socket.create_connection(
                address, timeout=connection_timeout
            )
        )
        self._monotonic = monotonic
        self._sleep = sleep
        self._logger = logger or logging.getLogger(__name__)
        self._validate_transport_configuration()

        self._temperature_min = _to_float(temperature_min, 'temperature_min')
        self._temperature_max = _to_float(temperature_max, 'temperature_max')
        self._validate_temperature_limits(self._temperature_min, self._temperature_max)
        self._temp_round = int(temp_round)

        self._communication_lock = RLock()
        self._operation_lock = RLock()

        # Keep public attribute name from original code.
        self.socket: socket.socket | None = None

        self._commands_sent = 0
        self._commands_ok = 0
        self._commands_failed = 0
        self._reconnect_count = 0
        self._last_raw_response: bytes | None = None
        # Bytes after a response terminator belong to the next response.  Some
        # TCP stacks coalesce frames, so they must not be discarded.
        self._receive_buffer = bytearray()

        if self._connect_on_init:
            self.connect()

    # ------------------------------------------------------------------
    # Context manager / connection management
    # ------------------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.disconnect()
        return False

    def __del__(self):  # pragma: no cover - best-effort cleanup only.
        with contextlib.suppress(Exception):
            self.disconnect()

    @property
    def is_connected(self) -> bool:
        """Return True if this object currently has an open socket object."""
        return self.socket is not None

    @property
    def communication_stats(self) -> dict[str, int | bytes | None]:
        """Return simple counters useful for monitoring/debugging."""
        return {
            'commands_sent': self._commands_sent,
            'commands_ok': self._commands_ok,
            'commands_failed': self._commands_failed,
            'reconnect_count': self._reconnect_count,
            'last_raw_response': self._last_raw_response,
        }

    def _validate_transport_configuration(self):
        """Reject invalid transport settings before opening a socket."""
        numeric_positive = {
            "timeout": self._timeout,
            "response_timeout": self._response_timeout,
            "retry_backoff": self._retry_backoff,
            "state_change_timeout": self._state_change_timeout,
            "setpoint_verify_tolerance": self._setpoint_verify_tolerance,
        }
        for name, value in numeric_positive.items():
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"<{name}> must be a finite value greater than 0, received {value!r}.")
        if not math.isfinite(self._retry_delay) or self._retry_delay < 0:
            raise ValueError(f"<retry_delay> must be finite and >= 0, received {self._retry_delay!r}.")
        if not math.isfinite(self._state_settle_delay) or self._state_settle_delay < 0:
            raise ValueError(
                f"<state_settle_delay> must be finite and >= 0, received {self._state_settle_delay!r}."
            )
        if not 1 <= self._port <= 65535:
            raise ValueError(f"<port> must be between 1 and 65535, received {self._port!r}.")
        if self._retries < 0:
            raise ValueError(f"<retries> must be >= 0, received {self._retries!r}.")
        if self._max_response_bytes < 16:
            raise ValueError(
                f"<max_response_bytes> must be at least 16, received {self._max_response_bytes!r}."
            )

    def connect(self):
        """Open the TCP connection if it is not already open.

        This explicit method allows Robot Framework and documentation tools to
        import the library without contacting hardware.
        """
        with self._communication_lock:
            if self.socket is None:
                self._connect_locked()

    def verify_connection(self) -> bool:
        """Verify communication using a harmless chamber-status query."""
        self.query('GET CHAMBER STATUS')
        return True

    def disconnect(self):
        """Close the TCP connection. Safe to call more than once."""
        with self._communication_lock:
            self._close_socket_locked()

    def reconnect(self):
        """Force a TCP reconnect to the chamber."""
        with self._communication_lock:
            self._close_socket_locked()
            self._connect_locked()
            self._reconnect_count += 1

    def _connect_locked(self):
        """Open a TCP connection. Caller must hold _communication_lock."""
        self._close_socket_locked()
        try:
            sock = self._socket_factory((self._ip, self._port), self._timeout)
            sock.settimeout(self._timeout)
            if self._tcp_keepalive:
                self._enable_tcp_keepalive(sock)
            self.socket = sock
            self._logger.info("Connected to climate chamber at %s:%s", self._ip, self._port)
        except OSError as exc:
            self.socket = None
            self._receive_buffer.clear()
            raise ClimateChamberCommunicationError(
                f'Cannot connect to climate chamber at {self._ip}:{self._port}: {exc}'
            ) from exc

    def _close_socket_locked(self):
        """Close current socket. Caller must hold _communication_lock."""
        sock = self.socket
        self.socket = None
        self._receive_buffer.clear()
        if sock is not None:
            with contextlib.suppress(OSError):
                sock.shutdown(socket.SHUT_RDWR)
            with contextlib.suppress(OSError):
                sock.close()
            self._logger.info("Disconnected from climate chamber at %s:%s", self._ip, self._port)

    def _ensure_connected_locked(self):
        if self.socket is None:
            self._connect_locked()

    def _enable_tcp_keepalive(self, sock: socket.socket):
        """Enable TCP keepalive where supported by the OS."""
        with contextlib.suppress(OSError):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # Linux/macOS style options. Ignored on platforms that do not expose them.
        for option_name, value in (
            ('TCP_KEEPIDLE', 60),
            ('TCP_KEEPALIVE', 60),  # macOS name for idle time.
            ('TCP_KEEPINTVL', 15),
            ('TCP_KEEPCNT', 4),
        ):
            option = getattr(socket, option_name, None)
            if option is not None:
                with contextlib.suppress(OSError):
                    sock.setsockopt(socket.IPPROTO_TCP, option, value)

        # Windows keepalive values: enable, idle ms, interval ms.
        if hasattr(socket, 'SIO_KEEPALIVE_VALS'):
            with contextlib.suppress(OSError, AttributeError):
                cast(Any, sock).ioctl(socket.SIO_KEEPALIVE_VALS, (1, 60_000, 15_000))

    # ------------------------------------------------------------------
    # Low-level protocol communication
    # ------------------------------------------------------------------

    def query_command_low_level(self, command_number, *arguments):
        """Send a low-level command and return the raw chamber response bytes.

        API-compatible with the original method. Internally this now uses
        sendall(), response-frame reading, reconnect, and retry handling.
        """
        frame = create_command_string(str(command_number), *arguments)
        return self._send_frame_with_retries(frame, command_for_log=str(command_number))

    def _send_frame_with_retries(self, frame: bytes, command_for_log: str) -> bytes:
        attempts = max(0, self._retries) + 1 if self._auto_reconnect else 1
        delay = max(0.0, self._retry_delay)
        last_error: BaseException | None = None

        for attempt in range(1, attempts + 1):
            try:
                started = self._monotonic()
                with self._communication_lock:
                    self._ensure_connected_locked()
                    assert self.socket is not None
                    self._commands_sent += 1
                    self.socket.sendall(frame)
                    raw_response = self._recv_response_locked()
                    self._last_raw_response = raw_response
                    self._commands_ok += 1

                elapsed = self._monotonic() - started
                self._logger.debug(
                    "Command %s succeeded in %.3fs on attempt %s/%s: %r",
                    command_for_log,
                    elapsed,
                    attempt,
                    attempts,
                    raw_response,
                )
                return raw_response

            except ClimateChamberCommunicationError as exc:
                last_error = exc
            except (TimeoutError, ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError) as exc:
                last_error = exc

            self._commands_failed += 1
            self._logger.warning(
                "Communication failure for command %s on attempt %s/%s: %s",
                command_for_log,
                attempt,
                attempts,
                last_error,
            )

            with self._communication_lock:
                self._close_socket_locked()

            if attempt >= attempts:
                break

            if delay > 0:
                self._sleep(delay)
                delay *= max(1.0, self._retry_backoff)

            with self._communication_lock:
                self._connect_locked()
                self._reconnect_count += 1

        raise ClimateChamberCommunicationError(
            f'Communication with climate chamber failed for command {command_for_log!r} '
            f'after {attempts} attempt(s): {last_error}'
        ) from last_error

    def _recv_response_locked(self) -> bytes:
        """Receive one response frame ending at ``\r``.

        TCP is a byte stream. A receive call may return a partial frame or more
        than one frame. The persistent receive buffer preserves any bytes that
        arrive after the first terminator for the next command. Caller must hold
        ``_communication_lock``.
        """
        if self.socket is None:
            raise ClimateChamberCommunicationError('Socket is not connected.')

        deadline = self._monotonic() + self._response_timeout
        old_timeout = self.socket.gettimeout()

        try:
            while True:
                terminator_index = self._receive_buffer.find(b'\r')
                if terminator_index >= 0:
                    frame_end = terminator_index + 1
                    frame = bytes(self._receive_buffer[:frame_end])
                    del self._receive_buffer[:frame_end]
                    return frame

                if len(self._receive_buffer) > self._max_response_bytes:
                    raise ClimateChamberProtocolError(
                        f'Climate chamber response exceeds {self._max_response_bytes} bytes.'
                    )

                remaining = deadline - self._monotonic()
                if remaining <= 0:
                    partial = bytes(self._receive_buffer)
                    raise ClimateChamberCommunicationError(
                        f'Timeout while waiting for response from climate chamber. '
                        f'Partial response: {partial!r}'
                    )

                self.socket.settimeout(min(self._timeout, remaining))
                try:
                    chunk = self.socket.recv(512)
                except TimeoutError:
                    continue

                if chunk == b'':
                    partial = bytes(self._receive_buffer)
                    raise ClimateChamberCommunicationError(
                        f'Climate chamber closed the TCP connection. Partial response: {partial!r}'
                    )

                self._receive_buffer.extend(chunk)
                if len(self._receive_buffer) > self._max_response_bytes:
                    raise ClimateChamberProtocolError(
                        f'Climate chamber response exceeds {self._max_response_bytes} bytes.'
                    )
        finally:
            with contextlib.suppress(OSError):
                if self.socket is not None:
                    self.socket.settimeout(old_timeout)

    def query(self, command_name: str, *arguments):
        """Send a named command and return response fields as list[str].

        API-compatible with the original method.
        """
        normalized_command = _normalize_command_name(command_name)
        command_number = translate_command_name_to_command_number(normalized_command)
        raw_response = self.query_command_low_level(command_number, *arguments)
        return self._parse_response(normalized_command, arguments, raw_response)

    def _parse_response(self, command_name: str, arguments: tuple[object, ...], raw_response: bytes) -> list[str]:
        separator = '¶'
        try:
            text = raw_response.decode('latin-1').strip('\r\n')
        except UnicodeDecodeError as exc:  # latin-1 should not fail, but keep explicit.
            raise ClimateChamberProtocolError(
                f'Cannot decode chamber response for command {command_name!r}: {raw_response!r}'
            ) from exc

        if not text:
            raise ClimateChamberProtocolError(
                f'Empty response for command {command_name!r} with arguments {arguments!r}.'
            )

        if 'read failed' in text.lower():
            raise ClimateChamberCommandError(
                f'Command {command_name!r} with arguments {arguments!r} failed. Raw response: {raw_response!r}'
            )

        parts = text.split(separator)
        if not parts:
            raise ClimateChamberProtocolError(
                f'Malformed response for command {command_name!r}: {raw_response!r}'
            )

        try:
            status_code = int(parts[0])
        except ValueError as exc:
            raise ClimateChamberProtocolError(
                f'Malformed status code in response to command {command_name!r}: {raw_response!r}'
            ) from exc

        if status_code != 1:
            raise ClimateChamberCommandError(
                f'Command {command_name!r} was rejected or failed. Status code: {status_code}. '
                f'Arguments: {arguments!r}. Raw response: {raw_response!r}'
            )

        return parts[1:]

    # ------------------------------------------------------------------
    # Basic identification properties: same public API as old code
    # ------------------------------------------------------------------

    @property
    def serial_number(self):
        """Returns the serial number as a string."""
        return self.query('get chamber info', 3)[0]

    @property
    def test_system_type(self):
        """Returns the test system type/model."""
        return self.query('get chamber info', 1)[0]

    @property
    def year_manufactured(self):
        """Returns the year manufactured as a string."""
        return f"{self.query('get chamber info', 2)[0]}"

    @property
    def idn(self):
        """Returns a string with information to identify the climate chamber."""
        return (
            f'Climate chamber vötschtechnik, {self.test_system_type}, '
            f'serial N° {self.serial_number}, manufactured in {self.year_manufactured}'
        )

    @property
    def id(self):
        """Returns a compact string identifying the climate chamber."""
        return f'{self.test_system_type} SN:{self.serial_number}-{self.year_manufactured}'

    # ------------------------------------------------------------------
    # Temperature control: same public API as old code
    # ------------------------------------------------------------------

    @property
    def temperature_measured(self):
        """Returns the measured temperature as a float number in Celsius."""
        return round(float(self.query('GET CONTROL_VARIABLE ACTUAL_VALUE', 1)[0]), self._temp_round)

    @property
    def temperature_set_point(self):
        """Returns the set temperature as a float number in Celsius."""
        return float(self.query('GET CONTROL_VARIABLE SET_POINT', 1)[0])

    @temperature_set_point.setter
    def temperature_set_point(self, celsius: float):
        """Set the temperature in Celsius."""
        value = _to_float(celsius, 'celsius')
        with self._operation_lock:
            self._validate_temperature_setpoint(value)
            self.query('SET CONTROL_VARIABLE SET_POINT', 1, _format_float_for_chamber(value))
            if self._verify_writes:
                actual = self.temperature_set_point
                if not check_tolerance(actual, value, self._setpoint_verify_tolerance):
                    raise ClimateChamberCommandError(
                        f'Temperature setpoint verification failed. Requested {value} °C, '
                        f'chamber reports {actual} °C.'
                    )

    @property
    def temperature_min(self):
        """Returns the minimum temperature limit in Celsius as a float number."""
        return self._temperature_min

    @temperature_min.setter
    def temperature_min(self, celsius: float):
        """Set the local minimum temperature safety limit in Celsius."""
        value = _to_float(celsius, 'celsius')
        self._validate_temperature_limits(value, self._temperature_max)
        self._temperature_min = value

    @property
    def temperature_max(self):
        """Returns the maximum temperature limit in Celsius as a float number."""
        return self._temperature_max

    @temperature_max.setter
    def temperature_max(self, celsius: float):
        """Set the local maximum temperature safety limit in Celsius."""
        value = _to_float(celsius, 'celsius')
        self._validate_temperature_limits(self._temperature_min, value)
        self._temperature_max = value

    def _validate_temperature_limits(self, min_value: float, max_value: float):
        if min_value >= max_value:
            raise ClimateChamberSafetyError(
                f'Invalid temperature limits: min {min_value} °C must be smaller than max {max_value} °C.'
            )

    def _validate_temperature_setpoint(self, celsius: float):
        if not self._temperature_min <= celsius <= self._temperature_max:
            raise ClimateChamberSafetyError(
                f'Trying to set temperature to {celsius} °C which is outside the temperature limits '
                f'configured for this instance. These limits allow temperatures between '
                f'{self._temperature_min} and {self._temperature_max} °C.'
            )

    # ------------------------------------------------------------------
    # Digital outputs / chamber running state: same public API as old code
    # ------------------------------------------------------------------

    @property
    def dryer(self):
        """Return True when dryer output is on, False when off."""
        return self._get_digital_out_bool(8, 'dryer')

    @dryer.setter
    def dryer(self, status: bool):
        """Turns dryer on/off. Accepts bool and legacy 0/1 values."""
        self._set_digital_out_bool(8, status, 'dryer')

    @property
    def compressed_air(self):
        """Return True when compressed-air output is on, False when off."""
        return self._get_digital_out_bool(7, 'compressed_air')

    @compressed_air.setter
    def compressed_air(self, status: bool):
        """Turns compressed air on/off. Accepts bool and legacy 0/1 values."""
        self._set_digital_out_bool(7, status, 'compressed_air')

    @property
    def is_running(self):
        """Returns True if the chamber is running and False otherwise."""
        return self._get_digital_out_bool(1, 'is_running')

    def start(self):
        """Starts the climate chamber."""
        with self._operation_lock:
            if self.is_running is False:
                self.query('START MANUAL_MODE', 1, 1)
                if self._verify_writes:
                    self._wait_for_condition(
                        lambda: self.is_running is True,
                        timeout=self._state_change_timeout,
                        description='chamber to start',
                    )
                elif self._state_settle_delay > 0:
                    self._sleep(self._state_settle_delay)

    def stop(self):
        """Stops the climate chamber."""
        with self._operation_lock:
            if self.is_running is True:
                self.query('START MANUAL_MODE', 1, 0)
                if self._verify_writes:
                    self._wait_for_condition(
                        lambda: self.is_running is False,
                        timeout=self._state_change_timeout,
                        description='chamber to stop',
                    )
                elif self._state_settle_delay > 0:
                    self._sleep(self._state_settle_delay)

    def _get_digital_out_bool(self, channel: int, name: str) -> bool:
        status = self.query('GET DIGITAL_OUT VALUE', channel)[0]
        if status == '0':
            return False
        if status == '1':
            return True
        raise ClimateChamberProtocolError(
            f'Queried {name} status from the climate chamber. Expected 0 or 1, received {status!r}.'
        )

    def _set_digital_out_bool(self, channel: int, status: bool, name: str):
        # Original code accepted True/False but also unintentionally accepted 0/1.
        # Keep that compatibility while rejecting other values.
        if status not in {True, False}:
            raise ValueError(f'<status> must be either True or False, received {status}.')

        desired = 1 if status == True else 0  # noqa: E712 - preserve legacy bool-like handling.
        with self._operation_lock:
            self.query('SET DIGITAL_OUT VALUE', channel, desired)
            if self._state_settle_delay > 0:
                self._sleep(self._state_settle_delay)
            if self._verify_writes:
                actual = self._get_digital_out_bool(channel, name)
                if actual is not bool(desired):
                    raise ClimateChamberCommandError(
                        f'{name} verification failed. Requested {bool(desired)}, chamber reports {actual}.'
                    )

    # ------------------------------------------------------------------
    # Gradient settings: same public API as old code
    # ------------------------------------------------------------------

    @property
    def gradient_up(self):
        return float(self.query('GET GRADIENT_UP VALUE', 1)[0])

    @gradient_up.setter
    def gradient_up(self, celsius: float):
        value = _to_float(celsius, 'celsius')
        min_val = 0.01
        max_val = 5.0
        if not min_val <= value <= max_val:
            raise ValueError(
                f'Trying to set gradient_up to {value} °C/min which is outside allowed limits. '
                f'These limits allow values between {min_val} and {max_val} °C/min.'
            )
        with self._operation_lock:
            self.query('SET GRADIENT_UP VALUE', 1, _format_float_for_chamber(value))
            if self._verify_writes:
                actual = self.gradient_up
                if not check_tolerance(actual, value, self._setpoint_verify_tolerance):
                    raise ClimateChamberCommandError(
                        f'gradient_up verification failed. Requested {value}, chamber reports {actual}.'
                    )

    @property
    def gradient_down(self):
        return float(self.query('GET GRADIENT_DOWN VALUE', 1)[0])

    @gradient_down.setter
    def gradient_down(self, celsius: float):
        value = _to_float(celsius, 'celsius')
        min_val = 0.01
        max_val = 3.5
        if not min_val <= value <= max_val:
            raise ValueError(
                f'Trying to set gradient_down to {value} °C/min which is outside allowed limits. '
                f'These limits allow values between {min_val} and {max_val} °C/min.'
            )
        with self._operation_lock:
            self.query('SET GRADIENT_DOWN VALUE', 1, _format_float_for_chamber(value))
            if self._verify_writes:
                actual = self.gradient_down
                if not check_tolerance(actual, value, self._setpoint_verify_tolerance):
                    raise ClimateChamberCommandError(
                        f'gradient_down verification failed. Requested {value}, chamber reports {actual}.'
                    )

    # ------------------------------------------------------------------
    # Long-running set-and-wait operation
    # ------------------------------------------------------------------

    def wait_until_temperature(
        self,
        target: float | None = None,
        *,
        tolerance: float = 0.8,
        wait_period: float = 10.0,
        timeout: float = 4 * 60 * 60,
        stable_samples: int = 1,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_callback: Callable[[], bool] | None = None,
    ) -> float:
        """Wait until measured temperature is stable around a target.

        ``target`` defaults to the current setpoint. ``stable_samples`` are
        consecutive samples inside ``target +/- tolerance``. The callback gets
        a dictionary with the latest progress values and is useful for adapters
        such as Robot Framework without coupling the driver to them.
        """
        if target is None:
            target_value = self.temperature_set_point
        else:
            target_value = _to_float(target, 'target')
            self._validate_temperature_setpoint(target_value)
        tolerance_value = _to_float(tolerance, 'tolerance')
        wait_value = _to_float(wait_period, 'wait_period')
        timeout_value = _to_float(timeout, 'timeout')
        sample_count = int(stable_samples)
        if tolerance_value < 0:
            raise ValueError('<tolerance> must be >= 0.')
        if wait_value <= 0:
            raise ValueError('<wait_period> must be > 0.')
        if timeout_value <= 0:
            raise ValueError('<timeout> must be > 0.')
        if sample_count < 1:
            raise ValueError('<stable_samples> must be >= 1.')

        started = self._monotonic()
        stable_count = 0
        last_temperature: float | None = None
        while True:
            if cancel_callback is not None and cancel_callback():
                raise ClimateChamberTimeoutError(
                    f'Waiting for {target_value} °C was cancelled. '
                    f'Last measured temperature: {last_temperature!r} °C.'
                )
            elapsed = self._monotonic() - started
            if elapsed > timeout_value:
                raise ClimateChamberTimeoutError(
                    f'Timeout waiting for chamber to reach {target_value} °C after '
                    f'{elapsed:.1f} s. Last measured temperature: {last_temperature!r} °C; '
                    f'stable samples: {stable_count}/{sample_count}.'
                )

            last_temperature = self.temperature_measured
            in_tolerance = check_tolerance(last_temperature, target_value, tolerance_value)
            stable_count = stable_count + 1 if in_tolerance else 0
            progress = {
                'target': target_value,
                'temperature': last_temperature,
                'tolerance': tolerance_value,
                'stable_count': stable_count,
                'stable_samples': sample_count,
                'elapsed_seconds': elapsed,
                'in_tolerance': in_tolerance,
            }
            if progress_callback is not None:
                progress_callback(progress)
            if stable_count >= sample_count:
                return float(last_temperature)
            self._sleep(wait_value)

    def dwell(
        self,
        duration_seconds: float,
        *,
        poll_interval: float = 60.0,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_callback: Callable[[], bool] | None = None,
    ) -> float:
        """Dwell for a finite duration and return the last measured temperature."""
        duration = _to_float(duration_seconds, 'duration_seconds')
        interval = _to_float(poll_interval, 'poll_interval')
        if duration < 0:
            raise ValueError('<duration_seconds> must be >= 0.')
        if interval <= 0:
            raise ValueError('<poll_interval> must be > 0.')
        started = self._monotonic()
        last_temperature = self.temperature_measured
        while True:
            elapsed = self._monotonic() - started
            remaining = max(0.0, duration - elapsed)
            if progress_callback is not None:
                progress_callback({
                    'temperature': last_temperature,
                    'elapsed_seconds': elapsed,
                    'remaining_seconds': remaining,
                })
            if remaining <= 0:
                return float(last_temperature)
            if cancel_callback is not None and cancel_callback():
                raise ClimateChamberTimeoutError(
                    f'Dwell was cancelled with {remaining:.1f} s remaining.'
                )
            self._sleep(min(interval, remaining))
            last_temperature = self.temperature_measured

    def set_and_wait(
        self,
        tset=25,
        wait_after_min=0,
        *,
        tolerance: float = 0.8,
        wait_period: float = 10.0,
        max_wait_min: float | None = 240.0,
        stable_samples: int = 1,
        print_progress: bool = True,
    ):
        """Set a temperature, start, stabilize, and dwell.

        The positional API is retained for existing applications. New code may
        use :meth:`wait_until_temperature` and :meth:`dwell` directly.
        """
        target = _to_float(tset, 'tset')
        dwell_minutes = _to_float(wait_after_min, 'wait_after_min')
        if dwell_minutes < 0:
            raise ValueError('<wait_after_min> must be >= 0.')
        if max_wait_min is None:
            # Legacy infinite waits are still supported explicitly. Use a very
            # large finite timeout internally so cancellation remains possible.
            timeout_seconds: float = float(100 * 365 * 24 * 60 * 60)
        else:
            max_wait_value = _to_float(max_wait_min, 'max_wait_min')
            if max_wait_value <= 0:
                raise ValueError('<max_wait_min> must be > 0 when provided.')
            timeout_seconds = max_wait_value * 60.0

        def legacy_progress(state: dict[str, Any]):
            message = (
                f"{get_time()} Current temperature is {state['temperature']} C, "
                f"target: {state['target']} C, stable samples: "
                f"{state['stable_count']}/{state['stable_samples']}"
            )
            self._progress(message, print_progress)

        with self._operation_lock:
            self.temperature_set_point = target
            self.start()
            self.wait_until_temperature(
                target,
                tolerance=tolerance,
                wait_period=wait_period,
                timeout=timeout_seconds,
                stable_samples=stable_samples,
                progress_callback=legacy_progress,
            )
            self.dwell(
                dwell_minutes * 60.0,
                poll_interval=60.0,
                progress_callback=(
                    lambda state: self._progress(
                        f"{get_time()} Dwell remaining: {float(state['remaining_seconds']) / 60.0:.1f} min, "
                        f"current temperature: {state['temperature']} C",
                        print_progress,
                    )
                ),
            )

    def _dwell(self, dwell_minutes: float, print_progress: bool):
        """Legacy private dwell wrapper retained for compatibility."""
        self.dwell(
            dwell_minutes * 60.0,
            poll_interval=60.0,
            progress_callback=lambda state: self._progress(
                f"{get_time()} Dwell remaining: {float(state['remaining_seconds']) / 60.0:.1f} min, "
                f"current temperature: {state['temperature']} C",
                print_progress,
            ),
        )

    def _progress(self, message: str, print_progress: bool):
        self._logger.info(message)
        if print_progress:
            print(message)

    # ------------------------------------------------------------------
    # Optional health/status helpers. Additive API, old code unaffected.
    # ------------------------------------------------------------------

    @property
    def chamber_status(self):
        """Return raw chamber status field as reported by GET CHAMBER STATUS."""
        return self.query('GET CHAMBER STATUS')[0]

    def health_check(self) -> dict[str, Any]:
        """Return a small health snapshot useful for 24/7 monitoring."""
        return {
            'connected': self.is_connected,
            'id': self.id,
            'is_running': self.is_running,
            'temperature_measured': self.temperature_measured,
            'temperature_set_point': self.temperature_set_point,
            'chamber_status': self.chamber_status,
            'communication_stats': self.communication_stats,
        }

    def _wait_for_condition(self, predicate: Callable[[], bool], timeout: float, description: str):
        deadline = self._monotonic() + max(0.001, float(timeout))
        last_error: BaseException | None = None

        while self._monotonic() < deadline:
            try:
                if predicate():
                    return
            except ClimateChamberError as exc:
                last_error = exc
            self._sleep(0.25)

        if last_error is not None:
            raise ClimateChamberTimeoutError(
                f'Timeout waiting for {description}. Last error: {last_error}'
            ) from last_error
        raise ClimateChamberTimeoutError(f'Timeout waiting for {description}.')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )

    climate_chamber = ClimateChamber(ip='localhost', temperature_min=-20, temperature_max=20)
    print(climate_chamber.idn)
    climate_chamber.set_and_wait(20, 1, max_wait_min=60)
    climate_chamber.stop()

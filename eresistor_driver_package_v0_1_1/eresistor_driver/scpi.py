"""Thread-safe SCPI-over-TCP transport for the E-Resistor board."""
from __future__ import annotations

import logging
import socket
import threading
import time
from typing import Callable

from .exceptions import ConnectionError, ScpiError, TimeoutError, parse_scpi_error
from .models import ConnectionState, ReconnectConfig
from .retry import backoff_delays

_LOG = logging.getLogger(__name__)


class ScpiTransport:
    """Minimal robust SCPI-over-TCP client.

    All SCPI commands are serialized through one re-entrant lock. The class can
    reconnect when a socket operation fails. Higher-level safety policy is kept
    in :class:`EResistorClient`.
    """

    def __init__(
        self,
        host: str,
        port: int = 5025,
        *,
        timeout: float = 2.0,
        retries: int = 2,
        line_ending: bytes = b"\n",
        encoding: str = "utf-8",
        read_greeting: bool = True,
        greeting_timeout_s: float = 0.25,
        max_response_bytes: int = 1024 * 1024,
        reconnect_config: ReconnectConfig | None = None,
        state_callback: Callable[[ConnectionState], None] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.line_ending = line_ending
        self.encoding = encoding
        self.read_greeting = read_greeting
        self.greeting_timeout_s = greeting_timeout_s
        self.max_response_bytes = max_response_bytes
        self.reconnect_config = reconnect_config or ReconnectConfig(max_attempts=retries)
        self.state_callback = state_callback
        self._sock: socket.socket | None = None
        self._lock = threading.RLock()
        self._state = ConnectionState.DISCONNECTED
        self._last_success_monotonic: float | None = None

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def last_success_monotonic(self) -> float | None:
        return self._last_success_monotonic

    def _set_state(self, state: ConnectionState) -> None:
        if self._state != state:
            self._state = state
            if self.state_callback:
                self.state_callback(state)

    def connect(self) -> None:
        with self._lock:
            self.close()
            self._set_state(ConnectionState.RECONNECTING)
            try:
                sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
                sock.settimeout(self.timeout)
                self._sock = sock
                if self.read_greeting:
                    self._try_read_greeting()
                self._last_success_monotonic = time.monotonic()
                self._set_state(ConnectionState.CONNECTED)
                _LOG.info("SCPI connected", extra={"host": self.host, "port": self.port})
            except OSError as exc:
                self._sock = None
                self._set_state(ConnectionState.LOST)
                raise ConnectionError(f"SCPI connection to {self.host}:{self.port} failed: {exc}") from exc

    def _try_read_greeting(self) -> None:
        if not self._sock:
            return
        old_timeout = self._sock.gettimeout()
        try:
            self._sock.settimeout(self.greeting_timeout_s)
            try:
                line = self._readline_locked(raise_on_timeout=False)
                if line:
                    _LOG.debug("SCPI greeting: %s", line)
            except OSError:
                pass
        finally:
            self._sock.settimeout(old_timeout)

    def close(self) -> None:
        with self._lock:
            sock = self._sock
            self._sock = None
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    sock.close()
                except OSError:
                    pass
            if self._state != ConnectionState.CLOSED:
                self._set_state(ConnectionState.DISCONNECTED)

    def reconnect(self) -> None:
        last_error: Exception | None = None
        for delay in backoff_delays(self.reconnect_config):
            if delay:
                time.sleep(delay)
            try:
                self.connect()
                return
            except Exception as exc:  # noqa: BLE001 - logged and retried by policy
                last_error = exc
                _LOG.warning("SCPI reconnect attempt failed: %s", exc, extra={"host": self.host})
        self._set_state(ConnectionState.LOST)
        if last_error:
            raise ConnectionError(f"SCPI reconnect failed: {last_error}") from last_error
        raise ConnectionError("SCPI reconnect failed")

    def request(self, command: str, *, multiline_until: str | None = None) -> str:
        """Send a SCPI command and read the response.

        For normal commands, reads one response line. For multi-line commands,
        set ``multiline_until`` to a terminating line/prefix such as ``#END ALL``.
        """
        with self._lock:
            attempts = max(1, self.retries + 1)
            last_exc: Exception | None = None
            for attempt in range(attempts):
                try:
                    if self._sock is None or self.state not in {ConnectionState.CONNECTED, ConnectionState.RECONNECTING}:
                        self.connect()
                    assert self._sock is not None
                    data = command.encode(self.encoding) + self.line_ending
                    self._sock.sendall(data)
                    if multiline_until is not None:
                        response = self._read_multiline_locked(multiline_until)
                    else:
                        response = self._readline_locked()
                    self._last_success_monotonic = time.monotonic()
                    parsed = parse_scpi_error(response)
                    if parsed:
                        raise ScpiError(
                            f"SCPI error {parsed.code}: {parsed.message}",
                            command=command,
                            response=response,
                            code=parsed.code,
                            host=self.host,
                        )
                    return response
                except ScpiError:
                    raise
                except (OSError, TimeoutError, socket.timeout) as exc:
                    last_exc = exc
                    _LOG.warning("SCPI command failed, attempt %d/%d: %s", attempt + 1, attempts, exc)
                    self._drop_socket_mark_lost()
                    if attempt < attempts - 1:
                        try:
                            self.reconnect()
                        except ConnectionError as rec_exc:
                            last_exc = rec_exc
                            continue
            raise ConnectionError(f"SCPI command failed after {attempts} attempt(s): {last_exc}") from last_exc

    def command(self, command: str) -> str:
        response = self.request(command)
        parsed = parse_scpi_error(response)
        if parsed:
            raise ScpiError(
                f"SCPI error {parsed.code}: {parsed.message}",
                command=command,
                response=response,
                code=parsed.code,
                host=self.host,
            )
        return response

    def _drop_socket_mark_lost(self) -> None:
        sock = self._sock
        self._sock = None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        self._set_state(ConnectionState.LOST)

    def _readline_locked(self, *, raise_on_timeout: bool = True) -> str:
        if self._sock is None:
            raise ConnectionError("SCPI socket is not connected")
        chunks = bytearray()
        while True:
            if len(chunks) > self.max_response_bytes:
                raise ScpiError(f"SCPI response exceeded {self.max_response_bytes} bytes")
            try:
                b = self._sock.recv(1)
            except socket.timeout as exc:
                if raise_on_timeout:
                    raise TimeoutError(f"SCPI read timed out after {self.timeout}s") from exc
                return ""
            if not b:
                raise ConnectionError("SCPI socket closed by peer")
            if b == b"\n":
                break
            chunks.extend(b)
        return chunks.decode(self.encoding, errors="replace").rstrip("\r")

    def _read_multiline_locked(self, multiline_until: str) -> str:
        lines: list[str] = []
        total = 0
        until = multiline_until.strip()
        while True:
            line = self._readline_locked()
            lines.append(line)
            total += len(line) + 1
            if total > self.max_response_bytes:
                raise ScpiError(f"SCPI response exceeded {self.max_response_bytes} bytes")
            if line.strip() == until or line.strip().startswith(until):
                return "\n".join(lines)

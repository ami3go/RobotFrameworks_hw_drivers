"""Deterministic TCP climate-chamber simulator used by automated tests.

The simulator operates at the same TCP protocol boundary as a real chamber.
It intentionally records every connection event, outbound driver frame, and
inbound simulator response so RFDS-019 can prove protocol conformance rather
than only verifying internal Python method calls.
"""

from __future__ import annotations

import contextlib
import socket
import socketserver
import threading
import time
from dataclasses import dataclass, field
from typing import Any

SEPARATOR = "¶"


@dataclass
class FakeChamberState:
    """Mutable simulator state shared by all client handler threads."""

    setpoint: float = 25.0
    temperature: float = 25.0
    running: bool = False
    dryer: bool = False
    compressed_air: bool = False
    # Auxiliary digital outputs other than the three named above; see the same
    # field on SimulatorState for why arbitrary channels must be modelled.
    digital_outputs: dict[int, bool] = field(default_factory=dict)
    gradient_up: float = 2.0
    gradient_down: float = 2.0
    status: str = "READY"
    model: str = "VT4002EMC"
    serial: str = "FAKE-2601"
    year: str = "2026"
    temperature_step: float = 20.0

    # One-shot fault injection controls used by protocol error tests.
    close_next_request: bool = False
    malformed_next_response: bool = False
    suppress_next_response: bool = False
    response_delay_seconds: float = 0.0
    split_responses: bool = False

    # RFDS-019 trace state. Each item is JSON-serializable.
    trace: list[dict[str, Any]] = field(default_factory=list)
    next_connection_id: int = 1
    next_exchange_id: int = 1
    lock: threading.RLock = field(default_factory=threading.RLock)


class _ThreadingServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class _Handler(socketserver.BaseRequestHandler):
    """Handle one TCP connection and record all protocol-boundary evidence."""

    def handle(self) -> None:
        state: FakeChamberState = self.server.state  # type: ignore[attr-defined]
        with state.lock:
            connection_id = state.next_connection_id
            state.next_connection_id += 1
            state.trace.append(
                {
                    "direction": "event",
                    "event": "connection_open",
                    "connection_id": connection_id,
                    "peer": f"{self.client_address[0]}:{self.client_address[1]}",
                    "timestamp_monotonic": time.monotonic(),
                }
            )

        buffer = bytearray()
        try:
            while True:
                data = self.request.recv(512)
                if not data:
                    return
                buffer.extend(data)
                while b"\r" in buffer:
                    index = buffer.index(b"\r")
                    frame_without_terminator = bytes(buffer[:index])
                    del buffer[: index + 1]
                    self._handle_frame(connection_id, frame_without_terminator, state)
        finally:
            with state.lock:
                state.trace.append(
                    {
                        "direction": "event",
                        "event": "connection_close",
                        "connection_id": connection_id,
                        "timestamp_monotonic": time.monotonic(),
                    }
                )

    def _handle_frame(
        self,
        connection_id: int,
        frame_without_terminator: bytes,
        state: FakeChamberState,
    ) -> None:
        full_frame = frame_without_terminator + b"\r"
        with state.lock:
            exchange_id = state.next_exchange_id
            state.next_exchange_id += 1
            state.trace.append(
                {
                    "direction": "outbound",
                    "connection_id": connection_id,
                    "exchange_id": exchange_id,
                    "raw_text": full_frame.decode("latin-1", errors="backslashreplace"),
                    "raw_hex": full_frame.hex(),
                    "timestamp_monotonic": time.monotonic(),
                }
            )

            if state.close_next_request:
                state.close_next_request = False
                state.trace.append(
                    {
                        "direction": "event",
                        "event": "forced_connection_close",
                        "connection_id": connection_id,
                        "exchange_id": exchange_id,
                        "timestamp_monotonic": time.monotonic(),
                    }
                )
                with contextlib.suppress(OSError):
                    self.request.shutdown(socket.SHUT_RDWR)
                return

            if state.suppress_next_response:
                state.suppress_next_response = False
                state.trace.append(
                    {
                        "direction": "event",
                        "event": "response_suppressed",
                        "connection_id": connection_id,
                        "exchange_id": exchange_id,
                        "timestamp_monotonic": time.monotonic(),
                    }
                )
                return

            response = self._process(frame_without_terminator, state)
            if state.malformed_next_response:
                state.malformed_next_response = False
                response = b"BROKEN\r"
            split = state.split_responses and len(response) > 2
            delay = state.response_delay_seconds
            state.response_delay_seconds = 0.0

        if delay > 0:
            time.sleep(delay)

        if split:
            midpoint = len(response) // 2
            self.request.sendall(response[:midpoint])
            self.request.sendall(response[midpoint:])
        else:
            self.request.sendall(response)

        with state.lock:
            state.trace.append(
                {
                    "direction": "inbound",
                    "connection_id": connection_id,
                    "exchange_id": exchange_id,
                    "raw_text": response.decode("latin-1", errors="backslashreplace"),
                    "raw_hex": response.hex(),
                    "timestamp_monotonic": time.monotonic(),
                }
            )

    @staticmethod
    def _response(value: object | None = None) -> bytes:
        text = "1" if value is None else f"1{SEPARATOR}{value}"
        return text.encode("latin-1") + b"\r"

    def _process(self, raw: bytes, state: FakeChamberState) -> bytes:
        fields = raw.decode("latin-1").split(SEPARATOR)
        if len(fields) < 2:
            return b"0\r"
        command = fields[0]
        args = fields[2:]

        if command == "99997":
            item = args[0] if args else "1"
            return self._response(
                {"1": state.model, "2": state.year, "3": state.serial}.get(item, "UNKNOWN")
            )
        if command == "10012":
            return self._response(state.status)
        if command == "11001":
            state.setpoint = float(args[-1])
            return self._response()
        if command == "11002":
            return self._response(f"{state.setpoint:.2f}")
        if command == "11004":
            if state.running:
                difference = state.setpoint - state.temperature
                step = min(abs(difference), state.temperature_step)
                state.temperature += step if difference >= 0 else -step
            return self._response(f"{state.temperature:.2f}")
        if command == "14001":
            channel = int(args[0])
            value = bool(int(args[1]))
            if channel == 1:
                state.running = value
            elif channel == 7:
                state.compressed_air = value
            elif channel == 8:
                state.dryer = value
            else:
                state.digital_outputs[channel] = value
            return self._response()
        if command == "14003":
            channel = int(args[0])
            values: dict[int, bool] = {
                1: state.running,
                7: state.compressed_air,
                8: state.dryer,
            }
            if channel in values:
                return self._response(1 if values[channel] else 0)
            return self._response(1 if state.digital_outputs.get(channel, False) else 0)
        if command == "11066":
            return self._response(f"{state.gradient_up:.2f}")
        if command == "11068":
            state.gradient_up = float(args[-1])
            return self._response()
        if command == "11070":
            return self._response(f"{state.gradient_down:.2f}")
        if command == "11072":
            state.gradient_down = float(args[-1])
            return self._response()
        return b"0\r"


class FakeChamberServer:
    """Context-manageable local TCP server implementing the used protocol subset."""

    def __init__(self) -> None:
        self.state = FakeChamberState()
        self._server = _ThreadingServer(("127.0.0.1", 0), _Handler)
        self._server.state = self.state  # type: ignore[attr-defined]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    def start(self) -> FakeChamberServer:
        self._thread.start()
        return self

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)

    def clear_trace(self) -> None:
        with self.state.lock:
            self.state.trace.clear()

    def get_trace(self) -> list[dict[str, Any]]:
        with self.state.lock:
            return [dict(item) for item in self.state.trace]

    def __enter__(self) -> FakeChamberServer:
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

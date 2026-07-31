"""Deterministic fake TCP chamber used by unit and Robot acceptance tests."""

from __future__ import annotations

import socket
import socketserver
import threading
from dataclasses import dataclass, field

SEPARATOR = "¶"


@dataclass
class FakeChamberState:
    setpoint: float = 25.0
    temperature: float = 25.0
    running: bool = False
    dryer: bool = False
    compressed_air: bool = False
    gradient_up: float = 2.0
    gradient_down: float = 2.0
    status: str = "READY"
    model: str = "VT4002EMC"
    serial: str = "FAKE-2601"
    year: str = "2026"
    temperature_step: float = 20.0
    close_next_request: bool = False
    malformed_next_response: bool = False
    split_responses: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)


class _ThreadingServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class _Handler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        buffer = bytearray()
        while True:
            data = self.request.recv(512)
            if not data:
                return
            buffer.extend(data)
            while b"\r" in buffer:
                index = buffer.index(b"\r")
                frame = bytes(buffer[:index])
                del buffer[: index + 1]
                state: FakeChamberState = self.server.state  # type: ignore[attr-defined]
                with state.lock:
                    if state.close_next_request:
                        state.close_next_request = False
                        self.request.shutdown(socket.SHUT_RDWR)
                        return
                    response = self._process(frame, state)
                    if state.malformed_next_response:
                        state.malformed_next_response = False
                        response = b"BROKEN\r"
                    split = state.split_responses and len(response) > 2
                if split:
                    midpoint = len(response) // 2
                    self.request.sendall(response[:midpoint])
                    self.request.sendall(response[midpoint:])
                else:
                    self.request.sendall(response)

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
            return self._response({"1": state.model, "2": state.year, "3": state.serial}.get(item, "UNKNOWN"))
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
            return self._response()
        if command == "14003":
            channel = int(args[0])
            values: dict[int, bool] = {1: state.running, 7: state.compressed_air, 8: state.dryer}
            return self._response(1 if values.get(channel, False) else 0)
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

    def __enter__(self) -> FakeChamberServer:
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

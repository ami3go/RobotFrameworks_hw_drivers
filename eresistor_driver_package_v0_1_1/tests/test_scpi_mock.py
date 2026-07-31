from __future__ import annotations

import socket
import threading

import pytest

from eresistor_driver.scpi import ScpiTransport
from eresistor_driver.exceptions import ScpiError


class FakeScpiServer:
    def __init__(self, responses: dict[str, str]):
        self.responses = responses
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.host, self.port = self.sock.getsockname()
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            conn, _addr = self.sock.accept()
        except OSError:
            return
        with conn:
            conn.sendall(b"E-Resistor SCPI ready\n")
            buf = b""
            while not self._stop.is_set():
                data = conn.recv(1024)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    cmd = line.decode().strip()
                    resp = self.responses.get(cmd, "ERR,-113,\"Undefined header\"")
                    conn.sendall(resp.encode() + b"\n")

    def close(self):
        self._stop.set()
        try:
            self.sock.close()
        except OSError:
            pass


def test_scpi_idn_and_mask():
    server = FakeScpiServer({"*IDN?": "OpenBench,E-Resistor,ABC,1.0.0", "CH1:MASK 0001": "OK", "CH1:MASK?": "0001"})
    try:
        tr = ScpiTransport(server.host, server.port, timeout=1, retries=0)
        tr.connect()
        assert tr.request("*IDN?") == "OpenBench,E-Resistor,ABC,1.0.0"
        assert tr.request("CH1:MASK 0001") == "OK"
        assert tr.request("CH1:MASK?") == "0001"
        tr.close()
    finally:
        server.close()


def test_scpi_error_parsed():
    server = FakeScpiServer({"BAD": "ERR,-128,\"Bad mask\""})
    try:
        tr = ScpiTransport(server.host, server.port, timeout=1, retries=0)
        tr.connect()
        with pytest.raises(ScpiError) as exc:
            tr.request("BAD")
        assert exc.value.code == -128
        tr.close()
    finally:
        server.close()

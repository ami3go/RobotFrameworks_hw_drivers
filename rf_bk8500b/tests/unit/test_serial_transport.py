from __future__ import annotations

import sys
import types

import pytest

from bk8500b import (
    ConfigurationError,
    DriverConfig,
    PortBusyError,
    ReadTimeoutError,
    ResponseTooLargeError,
    WriteTimeoutError,
)
import bk8500b.transport.serial as serial_transport


class SerialException(Exception): pass
class SerialTimeoutException(SerialException): pass


class FakeSerial:
    instances = []
    mode = "normal"
    def __init__(self, **kwargs):
        if self.mode == "exclusive_typeerror" and "exclusive" in kwargs:
            raise TypeError("exclusive unsupported")
        if self.mode == "busy":
            raise SerialException("access denied: busy")
        self.kwargs = kwargs
        self.is_open = True
        self.dtr = False
        self.rts = False
        self.write_timeout = kwargs["write_timeout"]
        self.timeout = kwargs["timeout"]
        self.buffer = bytearray()
        self.write_result = None
        self.raise_write_timeout = False
        self.close_failure = False
        self.input_reset = False
        self.output_reset = False
        FakeSerial.instances.append(self)
    def close(self):
        if self.close_failure: raise RuntimeError("close")
        self.is_open = False
    def write(self, data):
        if self.raise_write_timeout: raise SerialTimeoutException("timeout")
        self.buffer += data
        return len(data) if self.write_result is None else self.write_result
    def flush(self): pass
    def read(self, size):
        data = bytes(self.buffer[:size])
        del self.buffer[:size]
        return data
    def reset_input_buffer(self): self.input_reset = True
    def reset_output_buffer(self): self.output_reset = True


class Port:
    device="COM1"; description="Fake"; hwid="HW"; manufacturer="M"; serial_number="S"


def install_fake_serial(monkeypatch):
    serial_mod = types.ModuleType("serial")
    serial_mod.Serial = FakeSerial
    serial_mod.SerialException = SerialException
    serial_mod.SerialTimeoutException = SerialTimeoutException
    tools_mod = types.ModuleType("serial.tools")
    list_ports_mod = types.ModuleType("serial.tools.list_ports")
    list_ports_mod.comports = lambda: [Port()]
    tools_mod.list_ports = list_ports_mod
    monkeypatch.setitem(sys.modules, "serial", serial_mod)
    monkeypatch.setitem(sys.modules, "serial.tools", tools_mod)
    monkeypatch.setitem(sys.modules, "serial.tools.list_ports", list_ports_mod)
    FakeSerial.instances.clear()
    FakeSerial.mode = "normal"


def test_missing_pyserial(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "serial", None)
    with pytest.raises(ConfigurationError):
        serial_transport._import_serial()


def test_list_ports_and_normal_io(monkeypatch) -> None:
    install_fake_serial(monkeypatch)
    assert serial_transport.list_serial_ports()[0].device == "COM1"
    transport = serial_transport.SerialTransport(DriverConfig(port="COM1"))
    transport.open()
    instance = FakeSerial.instances[-1]
    assert instance.dtr and instance.rts and transport.is_open
    assert transport.write(b"abc") == 3
    assert transport.read(2) == b"ab"
    instance.buffer = bytearray(b"x\n")
    assert transport.read_until(b"\n", maximum_bytes=10) == b"x\n"
    transport.reset_input_buffer(); transport.reset_output_buffer()
    assert instance.input_reset and instance.output_reset
    transport.close()
    assert not transport.is_open


def test_exclusive_fallback_and_busy(monkeypatch) -> None:
    install_fake_serial(monkeypatch)
    FakeSerial.mode = "exclusive_typeerror"
    t = serial_transport.SerialTransport(DriverConfig(port="COM1"))
    t.open(); t.close()
    FakeSerial.mode = "busy"
    with pytest.raises(PortBusyError):
        serial_transport.SerialTransport(DriverConfig(port="COM1")).open()


def test_write_and_read_failures(monkeypatch) -> None:
    install_fake_serial(monkeypatch)
    t = serial_transport.SerialTransport(DriverConfig(port="COM1")); t.open()
    instance = FakeSerial.instances[-1]
    instance.write_result = 1
    with pytest.raises(WriteTimeoutError): t.write(b"abc")
    instance.write_result = None; instance.raise_write_timeout = True
    with pytest.raises(WriteTimeoutError): t.write(b"abc")
    instance.raise_write_timeout = False; instance.buffer.clear()
    with pytest.raises(ReadTimeoutError): t.read(1)
    instance.buffer = bytearray(b"abcdef")
    with pytest.raises(ResponseTooLargeError): t.read_until(b"\n", maximum_bytes=2, timeout_s=0.1)
    instance.close_failure = True
    with pytest.raises(Exception): t.close()


def test_additional_serial_validation_and_failures(monkeypatch) -> None:
    install_fake_serial(monkeypatch)
    t = serial_transport.SerialTransport(DriverConfig(port="COM1"))
    t.close()  # close on unopened transport
    with pytest.raises(Exception): t.read(1)
    t.open(); first = FakeSerial.instances[-1]; t.open()  # idempotent open
    with pytest.raises(ValueError): t.write(b"")
    with pytest.raises(ValueError): t.read(-1)
    with pytest.raises(ValueError): t.read_until(b"", maximum_bytes=10)
    first.buffer = bytearray(b"z")
    assert t.read(1, timeout_s=0.01) == b"z"
    assert t.write(b"z", timeout_s=0.01) == 1
    first.write = lambda data: (_ for _ in ()).throw(RuntimeError("broken"))
    with pytest.raises(Exception): t.write(b"z")
    first.read = lambda size: (_ for _ in ()).throw(RuntimeError("broken"))
    with pytest.raises(Exception): t.read(1)
    t.close()


def test_read_until_timeout_without_terminator(monkeypatch) -> None:
    install_fake_serial(monkeypatch)
    t = serial_transport.SerialTransport(DriverConfig(port="COM1")); t.open()
    instance = FakeSerial.instances[-1]
    instance.buffer = bytearray(b"abc")
    with pytest.raises(ReadTimeoutError): t.read_until(b"\n", maximum_bytes=10, timeout_s=0.001)
    t.close()

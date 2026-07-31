from __future__ import annotations

import math
import pytest

from bk8500b import DriverConfig
from bk8500b.enums import RiskClass
from bk8500b.exceptions import MalformedResponseError, ResponseTooLargeError, SCPIProtocolError
from bk8500b.execution import CommandExecutor
from bk8500b.protocol.scpi import (
    SCPICommand, SCPIProtocol, format_number, parse_bool, parse_error,
    parse_float, parse_identity, parse_int,
)


class RawTransport:
    def __init__(self, response: bytes = b"1\n"):
        self.response = response
        self._open = True
        self.writes = []
    @property
    def is_open(self): return self._open
    def open(self): self._open = True
    def close(self): self._open = False
    def write(self, data, *, timeout_s=None): self.writes.append(data); return len(data)
    def read(self, size, *, timeout_s=None): return self.response[:size]
    def read_until(self, terminator, *, maximum_bytes, timeout_s=None): return self.response
    def reset_input_buffer(self): pass
    def reset_output_buffer(self): pass


def protocol(response=b"1\n", *, maximum=4096):
    cfg = DriverConfig(port="x", minimum_command_interval_s=0, maximum_scpi_response_bytes=maximum)
    tr = RawTransport(response)
    return SCPIProtocol(cfg, CommandExecutor(cfg, tr)), tr


@pytest.mark.parametrize("text,is_query", [("", False), ("BAD\x01", False), ("A\nB", False), ("MEAS", True)])
def test_command_rejects_invalid_text(text, is_query):
    with pytest.raises(SCPIProtocolError):
        SCPICommand(text, "bad", is_query=is_query)


def test_write_and_query_direction_are_enforced():
    p, _ = protocol()
    with pytest.raises(SCPIProtocolError):
        p.write(SCPICommand("*IDN?", "id", is_query=True))
    with pytest.raises(SCPIProtocolError):
        p.query_bytes(SCPICommand("*CLS", "clear"))


@pytest.mark.parametrize("response,exc", [
    (b"1", MalformedResponseError),
    (b"a\x00b\n", MalformedResponseError),
    (b"\xff\n", MalformedResponseError),
])
def test_malformed_wire_responses(response, exc):
    p, _ = protocol(response)
    cmd = SCPICommand("MEAS?", "measure", risk=RiskClass.READ_ONLY, is_query=True)
    with pytest.raises(exc):
        p.query_text(cmd)


def test_protocol_rejects_oversize_even_if_transport_does_not():
    p, _ = protocol(b"12345678901234567\n", maximum=16)
    cmd = SCPICommand("MEAS?", "measure", is_query=True)
    with pytest.raises(ResponseTooLargeError):
        p.query_bytes(cmd)


@pytest.mark.parametrize("fn,arg", [
    (parse_float, "abc"), (parse_float, "nan"),
    (parse_int, "abc"), (parse_int, "1.5"),
    (parse_bool, "maybe"),
    (parse_identity, "a,b,c"), (parse_identity, ",MODEL,SN,FW"),
    (parse_error, "0"),
])
def test_parser_rejects_malformed_values(fn, arg):
    with pytest.raises(MalformedResponseError):
        fn(arg)


def test_integer_nr2_and_ranges():
    assert parse_int("1.000") == 1
    with pytest.raises(MalformedResponseError): parse_int("0", minimum=1)
    with pytest.raises(MalformedResponseError): parse_int("2", maximum=1)


def test_error_csv_and_number_formatting():
    e = parse_error('-100,"Bad, command"')
    assert e.code == -100 and e.message == "Bad, command"
    assert format_number(1.25) == "1.25"
    with pytest.raises(ValueError): format_number(math.inf)

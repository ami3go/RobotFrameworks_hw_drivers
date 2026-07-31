"""SCPI framing, command models, and strict response parsers."""
from __future__ import annotations

import csv
from dataclasses import dataclass
import io
import math
import re

from ..config import DriverConfig
from ..enums import RiskClass
from ..exceptions import MalformedResponseError, ResponseTooLargeError, SCPIProtocolError
from ..execution import CommandExecutor
from ..measurements import InstrumentIdentity, SCPIErrorEntry

_COMMAND_RE = re.compile(r"^[\x20-\x7e]+$")


@dataclass(frozen=True, slots=True)
class SCPICommand:
    text: str
    operation: str
    risk: RiskClass = RiskClass.CONFIGURATION
    is_query: bool = False
    retryable: bool = True
    destructive_read: bool = False

    def __post_init__(self) -> None:
        if "\r" in self.text or "\n" in self.text:
            raise SCPIProtocolError("SCPI command must not contain embedded terminators")
        if not self.text or not _COMMAND_RE.fullmatch(self.text):
            raise SCPIProtocolError("SCPI command must contain printable ASCII only")
        if self.is_query and "?" not in self.text:
            raise SCPIProtocolError("Query command must contain '?'")


class SCPIProtocol:
    def __init__(self, config: DriverConfig, executor: CommandExecutor) -> None:
        self.config = config
        self.executor = executor

    def _encode(self, command: SCPICommand) -> bytes:
        return command.text.encode("ascii") + self.config.scpi_write_terminator

    def write(self, command: SCPICommand, *, timeout_s: float | None = None) -> str:
        if command.is_query:
            raise SCPIProtocolError("Cannot send query through write()")
        return self.executor.write(
            self._encode(command),
            operation=command.operation,
            risk=command.risk,
            timeout_s=timeout_s,
        )

    def query_bytes(
        self,
        command: SCPICommand,
        *,
        timeout_s: float | None = None,
    ) -> bytes:
        if not command.is_query:
            raise SCPIProtocolError("query_bytes() requires is_query=True")

        def read_response(deadline: float) -> bytes:
            raw = self.executor.transport.read_until(
                self.config.scpi_read_terminator,
                maximum_bytes=self.config.maximum_scpi_response_bytes,
                timeout_s=deadline,
            )
            if len(raw) > self.config.maximum_scpi_response_bytes:
                raise ResponseTooLargeError("SCPI response exceeded configured maximum")
            return raw

        def validate(raw: bytes) -> bytes:
            if not raw.endswith(self.config.scpi_read_terminator):
                raise MalformedResponseError("SCPI response missing terminator")
            body = raw[: -len(self.config.scpi_read_terminator)]
            if b"\x00" in body:
                raise MalformedResponseError("SCPI response contains NUL byte")
            return body.strip()

        return self.executor.query(
            self._encode(command),
            operation=command.operation,
            read_response=read_response,
            validate_response=validate,
            timeout_s=timeout_s,
            retryable=command.retryable,
            destructive_read=command.destructive_read,
        )

    def query_text(self, command: SCPICommand, *, timeout_s: float | None = None) -> str:
        raw = self.query_bytes(command, timeout_s=timeout_s)
        try:
            return raw.decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise MalformedResponseError("SCPI response is not ASCII") from exc


def parse_float(text: str) -> float:
    try:
        value = float(text.strip())
    except ValueError as exc:
        raise MalformedResponseError("Expected finite numeric SCPI response", context={"raw": text[:128]}) from exc
    if not math.isfinite(value):
        raise MalformedResponseError("SCPI numeric response must be finite", context={"raw": text[:128]})
    return value


def parse_int(text: str, *, minimum: int | None = None, maximum: int | None = None) -> int:
    token = text.strip()
    try:
        value = int(token, 10)
    except ValueError as exc:
        # Some instruments return integral values in NR2 form, e.g. "1.000".
        try:
            as_float = float(token)
        except ValueError:
            raise MalformedResponseError("Expected integer SCPI response", context={"raw": text[:128]}) from exc
        if not math.isfinite(as_float) or not as_float.is_integer():
            raise MalformedResponseError("Expected integral SCPI response", context={"raw": text[:128]}) from exc
        value = int(as_float)
    if minimum is not None and value < minimum:
        raise MalformedResponseError("SCPI integer below expected range", context={"value": value})
    if maximum is not None and value > maximum:
        raise MalformedResponseError("SCPI integer above expected range", context={"value": value})
    return value


def parse_bool(text: str) -> bool:
    token = text.strip().upper()
    if token in {"1", "ON", "TRUE"}:
        return True
    if token in {"0", "OFF", "FALSE"}:
        return False
    raise MalformedResponseError("Expected SCPI boolean response", context={"raw": text[:128]})


def parse_identity(text: str) -> InstrumentIdentity:
    fields = [part.strip() for part in text.split(",")]
    if len(fields) < 4:
        raise MalformedResponseError("*IDN? response must have at least four comma-separated fields", context={"raw": text[:256]})
    manufacturer = fields[0]
    model = fields[1]
    serial = fields[2]
    firmware = ",".join(fields[3:]).strip()
    if not manufacturer or not model:
        raise MalformedResponseError("*IDN? manufacturer and model must be non-empty")
    return InstrumentIdentity(manufacturer, model, serial, firmware, text)


def parse_error(text: str) -> SCPIErrorEntry:
    try:
        row = next(csv.reader(io.StringIO(text), skipinitialspace=True))
    except (csv.Error, StopIteration) as exc:
        raise MalformedResponseError("Malformed SYST:ERR? response", context={"raw": text[:256]}) from exc
    if len(row) < 2:
        raise MalformedResponseError("SYST:ERR? response must contain code and message", context={"raw": text[:256]})
    code = parse_int(row[0])
    message = ",".join(row[1:]).strip().strip('"')
    return SCPIErrorEntry(code=code, message=message, raw=text)


def format_number(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("SCPI values must be finite")
    # 12 significant digits is deterministic and ample for documented resolution.
    return format(value, ".12g")

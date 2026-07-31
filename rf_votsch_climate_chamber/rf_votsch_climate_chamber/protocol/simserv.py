"""Vötsch/SimServ command registry, framing and response parsing.

This module owns protocol syntax only.  It does not open sockets or contain
Robot Framework code, which keeps serialization independently testable.
"""

from __future__ import annotations

from ..exceptions import (
    DriverArgumentTypeError,
    DriverArgumentValueError,
    DriverCommandRejectedError,
    DriverMalformedResponseError,
)

SEPARATOR_BYTE = b"\xb6"
SEPARATOR_TEXT = "¶"
TERMINATOR = b"\r"

COMMAND_NUMBERS: dict[str, str] = {
    "GET CHAMBER INFO": "99997",
    "GET CHAMBER STATUS": "10012",
    "GET CONTROL_VARIABLE SET_POINT": "11002",
    "GET CONTROL_VARIABLE ACTUAL_VALUE": "11004",
    "GET DIGITAL_OUT VALUE": "14003",
    "GET GRADIENT_UP VALUE": "11066",
    "GET GRADIENT_DOWN VALUE": "11070",
    "SET CONTROL_VARIABLE SET_POINT": "11001",
    "SET DIGITAL_OUT VALUE": "14001",
    "SET GRADIENT_UP VALUE": "11068",
    "SET GRADIENT_DOWN VALUE": "11072",
    "START MANUAL_MODE": "14001",
}
COMMAND_NAMES = tuple(sorted(COMMAND_NUMBERS))


def normalize_command_name(command_name: str) -> str:
    if not isinstance(command_name, str):
        raise DriverArgumentTypeError("command name must be a string", operation="protocol.normalize")
    return " ".join(command_name.upper().split())


def command_number(command_name: str) -> str:
    normalized = normalize_command_name(command_name)
    try:
        return COMMAND_NUMBERS[normalized]
    except KeyError as exc:
        raise DriverArgumentValueError(
            f"unsupported protocol command {normalized!r}",
            operation="protocol.command_number",
            details={"supported_count": len(COMMAND_NAMES)},
        ) from exc


def build_frame(command_number_value: str, *arguments: object) -> bytes:
    number = str(command_number_value)
    if not number.isdigit() or len(number) != 5:
        raise DriverArgumentValueError(
            f"command number must contain exactly five digits, received {number!r}",
            operation="protocol.build_frame",
        )
    if len(arguments) > 4:
        raise DriverArgumentValueError(
            f"the protocol permits at most four arguments, received {len(arguments)}",
            operation="protocol.build_frame",
        )
    parts = [number, "1", *(str(argument) for argument in arguments)]
    for part in parts:
        if "\r" in part or "\n" in part or SEPARATOR_TEXT in part:
            raise DriverArgumentValueError(
                "protocol argument contains a reserved separator or terminator",
                operation="protocol.build_frame",
            )
        try:
            part.encode("ascii")
        except UnicodeEncodeError as exc:
            raise DriverArgumentValueError(
                f"protocol argument must be ASCII-compatible, received {part!r}",
                operation="protocol.build_frame",
            ) from exc
    return SEPARATOR_BYTE.join(part.encode("ascii") for part in parts) + TERMINATOR


def build_named_frame(command_name: str, *arguments: object) -> bytes:
    return build_frame(command_number(command_name), *arguments)


def parse_response(command_name: str, arguments: tuple[object, ...], raw_response: bytes) -> list[str]:
    try:
        text = raw_response.decode("latin-1").strip("\r\n")
    except UnicodeDecodeError as exc:  # latin-1 is total; retained as defensive classification.
        raise DriverMalformedResponseError(
            "response cannot be decoded using latin-1",
            operation=command_name,
        ) from exc
    if not text:
        raise DriverMalformedResponseError("device returned an empty response", operation=command_name)
    if "read failed" in text.lower():
        raise DriverCommandRejectedError(
            "device reported read failed",
            operation=command_name,
            details={"arguments": list(arguments)},
        )
    parts = text.split(SEPARATOR_TEXT)
    try:
        status = int(parts[0])
    except ValueError as exc:
        raise DriverMalformedResponseError(
            f"response status is not an integer: {parts[0]!r}",
            operation=command_name,
        ) from exc
    if status != 1:
        raise DriverCommandRejectedError(
            f"device rejected command with status {status}",
            operation=command_name,
            details={"arguments": list(arguments)},
        )
    return parts[1:]


def format_float(value: float) -> str:
    return format(float(value), ".10g")

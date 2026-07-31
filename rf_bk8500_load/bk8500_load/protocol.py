"""Frame-level protocol for the B&K Precision 8500 series DC electronic loads.

The 8500 series speaks a fixed-length binary protocol: every request and every
response is exactly 26 bytes.

    byte 0      0xAA            start of frame
    byte 1      address         instrument address (0x00..0xFE)
    byte 2      command         command code, see :class:`Command`
    bytes 3..24 payload         little-endian integers / ASCII, 0x00 padded
    byte 25     checksum        sum(bytes[0..24]) & 0xFF

For every frame sent, exactly one 26 byte frame must be read back. Commands
that do not return data answer with a *status frame* (command byte 0x12) whose
payload byte 3 carries the result code.

Reference: 8500 Series DC Electronic Loads user manual, "Remote operation",
sections "Summary of commands" and "Command details".
"""

from __future__ import annotations

from enum import IntEnum
from typing import Final

PACKET_LENGTH: Final[int] = 26
START_OF_FRAME: Final[int] = 0xAA
STATUS_COMMAND: Final[int] = 0x12
BROADCAST_FORBIDDEN_ADDRESS: Final[int] = 0xFF

# Unit conversion constants (SI value -> instrument raw integer).
COUNTS_PER_VOLT: Final[float] = 1e3  # 1 count = 1 mV
COUNTS_PER_AMP: Final[float] = 1e4  # 1 count = 0.1 mA
COUNTS_PER_WATT: Final[float] = 1e3  # 1 count = 1 mW
COUNTS_PER_OHM: Final[float] = 1e3  # 1 count = 1 mOhm
COUNTS_PER_SECOND_DWELL: Final[float] = 1e4  # 1 count = 0.1 ms (transient/list)
COUNTS_PER_SECOND_TIMER: Final[float] = 1.0  # 1 count = 1 s (LOAD ON timer)


class Command(IntEnum):
    """Command byte (frame byte 2)."""

    STATUS = 0x12
    SET_REMOTE = 0x20
    SET_INPUT = 0x21
    SET_MAX_VOLTAGE = 0x22
    GET_MAX_VOLTAGE = 0x23
    SET_MAX_CURRENT = 0x24
    GET_MAX_CURRENT = 0x25
    SET_MAX_POWER = 0x26
    GET_MAX_POWER = 0x27
    SET_MODE = 0x28
    GET_MODE = 0x29
    SET_CC_CURRENT = 0x2A
    GET_CC_CURRENT = 0x2B
    SET_CV_VOLTAGE = 0x2C
    GET_CV_VOLTAGE = 0x2D
    SET_CW_POWER = 0x2E
    GET_CW_POWER = 0x2F
    SET_CR_RESISTANCE = 0x30
    GET_CR_RESISTANCE = 0x31
    SET_CC_TRANSIENT = 0x32
    GET_CC_TRANSIENT = 0x33
    SET_CV_TRANSIENT = 0x34
    GET_CV_TRANSIENT = 0x35
    SET_CW_TRANSIENT = 0x36
    GET_CW_TRANSIENT = 0x37
    SET_CR_TRANSIENT = 0x38
    GET_CR_TRANSIENT = 0x39
    SET_LIST_MODE = 0x3A
    GET_LIST_MODE = 0x3B
    SET_LIST_REPEAT = 0x3C
    GET_LIST_REPEAT = 0x3D
    SET_LIST_STEP_COUNT = 0x3E
    GET_LIST_STEP_COUNT = 0x3F
    SET_LIST_STEP_CURRENT = 0x40
    GET_LIST_STEP_CURRENT = 0x41
    SET_LIST_STEP_VOLTAGE = 0x42
    GET_LIST_STEP_VOLTAGE = 0x43
    SET_LIST_STEP_POWER = 0x44
    GET_LIST_STEP_POWER = 0x45
    SET_LIST_STEP_RESISTANCE = 0x46
    GET_LIST_STEP_RESISTANCE = 0x47
    SET_LIST_NAME = 0x48
    GET_LIST_NAME = 0x49
    SET_LIST_PARTITION = 0x4A
    GET_LIST_PARTITION = 0x4B
    SAVE_LIST_FILE = 0x4C
    RECALL_LIST_FILE = 0x4D
    SET_BATTERY_MIN_VOLTAGE = 0x4E
    GET_BATTERY_MIN_VOLTAGE = 0x4F
    SET_LOAD_ON_TIMER = 0x50
    GET_LOAD_ON_TIMER = 0x51
    SET_LOAD_ON_TIMER_STATE = 0x52
    GET_LOAD_ON_TIMER_STATE = 0x53
    SET_ADDRESS = 0x54
    SET_LOCAL_KEY = 0x55
    SET_REMOTE_SENSE = 0x56
    GET_REMOTE_SENSE = 0x57
    SET_TRIGGER_SOURCE = 0x58
    GET_TRIGGER_SOURCE = 0x59
    TRIGGER = 0x5A
    SAVE_SETTINGS = 0x5B
    RECALL_SETTINGS = 0x5C
    SET_FUNCTION = 0x5D
    GET_FUNCTION = 0x5E
    GET_INPUT_VALUES = 0x5F
    GET_PRODUCT_INFO = 0x6A
    GET_BARCODE = 0x6B


QUERY_COMMANDS: Final[frozenset[int]] = frozenset(
    int(command) for command in Command if command.name.startswith("GET_")
)


def command_expects_status(command: int) -> bool:
    """Return whether ``command`` must answer with a 0x12 status packet."""
    return int(command) != int(Command.STATUS) and int(command) not in QUERY_COMMANDS


class StatusCode(IntEnum):
    """Payload byte 3 of a status (0x12) frame."""

    CHECKSUM_INCORRECT = 0x90
    PARAMETER_INCORRECT = 0xA0
    UNRECOGNISED_COMMAND = 0xB0
    INVALID_COMMAND = 0xC0
    SUCCESS = 0x80


STATUS_TEXT: Final[dict[int, str]] = {
    StatusCode.CHECKSUM_INCORRECT: "Checksum of the transmitted frame was incorrect",
    StatusCode.PARAMETER_INCORRECT: "Parameter value out of range or not accepted",
    StatusCode.UNRECOGNISED_COMMAND: "Command cannot be carried out in the current state",
    StatusCode.INVALID_COMMAND: "Invalid command byte",
    StatusCode.SUCCESS: "Command was successful",
}


def checksum(frame: bytes | bytearray) -> int:
    """Return the protocol checksum: sum of the first 25 bytes, modulo 256."""
    return sum(frame[: PACKET_LENGTH - 1]) & 0xFF


def encode_int(value: int, num_bytes: int) -> bytes:
    """Encode a non-negative integer as a little-endian field."""
    if num_bytes not in (1, 2, 4):
        raise ValueError(f"Unsupported field width: {num_bytes}")
    value = int(round(value))
    if value < 0 or value >= 1 << (8 * num_bytes):
        raise ValueError(f"Value {value} does not fit in {num_bytes} byte(s)")
    return value.to_bytes(num_bytes, "little")


def decode_int(data: bytes) -> int:
    """Decode a little-endian unsigned field."""
    return int.from_bytes(data, "little")


def build_frame(address: int, command: int, payload: bytes = b"") -> bytes:
    """Assemble a complete 26 byte request frame including checksum."""
    if not 0 <= address < BROADCAST_FORBIDDEN_ADDRESS:
        raise ValueError(f"Address {address} outside 0x00..0xFE")
    if len(payload) > PACKET_LENGTH - 4:
        raise ValueError("Payload longer than 22 bytes")
    frame = bytearray(PACKET_LENGTH)
    frame[0] = START_OF_FRAME
    frame[1] = address
    frame[2] = int(command)
    frame[3 : 3 + len(payload)] = payload
    frame[PACKET_LENGTH - 1] = checksum(frame)
    return bytes(frame)


def frame_is_well_formed(frame: bytes) -> tuple[bool, str]:
    """Validate a received frame. Returns ``(ok, reason)``."""
    if len(frame) != PACKET_LENGTH:
        return False, f"expected {PACKET_LENGTH} bytes, received {len(frame)}"
    if frame[0] != START_OF_FRAME:
        return False, f"start byte is 0x{frame[0]:02X}, expected 0xAA"
    if frame[1] == BROADCAST_FORBIDDEN_ADDRESS:
        return False, "address byte 0xFF is reserved"
    if frame[PACKET_LENGTH - 1] != checksum(frame):
        return False, (
            f"checksum 0x{frame[PACKET_LENGTH - 1]:02X}, "
            f"calculated 0x{checksum(frame):02X}"
        )
    return True, ""


def format_frame(frame: bytes) -> str:
    """Render a frame as grouped hex, for logs and failure messages."""
    return " ".join(f"{b:02X}" for b in frame)

"""Pure codec for the documented 26-byte B&K/ITECH legacy frame protocol."""
from __future__ import annotations

from dataclasses import dataclass
import math

from ..exceptions import ChecksumError, FrameSyncError, LegacyProtocolError

FRAME_LENGTH = 26
START_BYTE = 0xAA
BROADCAST_ADDRESS = 0xFF
PAYLOAD_LENGTH = 22

VOLTAGE_SCALE_V = 0.001
CURRENT_SCALE_A = 0.0001
POWER_SCALE_W = 0.001
RESISTANCE_SCALE_OHM = 0.001
TRANSIENT_TIME_SCALE_S = 0.0001
TIMER_SCALE_S = 1.0


@dataclass(frozen=True, slots=True)
class LegacyFrame:
    address: int
    command: int
    payload: bytes
    raw: bytes


def checksum(data: bytes) -> int:
    if len(data) != FRAME_LENGTH - 1:
        raise ValueError("Checksum input must contain exactly the first 25 frame bytes")
    return sum(data) & 0xFF


def build_frame(address: int, command: int, payload: bytes = b"") -> bytes:
    if not (0 <= address <= 31 or address == BROADCAST_ADDRESS):
        raise LegacyProtocolError("Legacy address must be 0..31 or 0xFF")
    if not 0 <= command <= 0xFF:
        raise LegacyProtocolError("Legacy command must fit in one byte")
    if len(payload) > PAYLOAD_LENGTH:
        raise LegacyProtocolError("Legacy payload is too large", context={"maximum": PAYLOAD_LENGTH, "actual": len(payload)})
    frame = bytearray(FRAME_LENGTH)
    frame[0] = START_BYTE
    frame[1] = address
    frame[2] = command
    frame[3 : 3 + len(payload)] = payload
    frame[25] = checksum(bytes(frame[:25]))
    return bytes(frame)


def decode_frame(raw: bytes, *, expected_address: int | None = None) -> LegacyFrame:
    if len(raw) != FRAME_LENGTH:
        raise LegacyProtocolError("Legacy frame length must be 26 bytes", context={"actual": len(raw)})
    if raw[0] != START_BYTE:
        raise FrameSyncError("Legacy frame start byte is not 0xAA", context={"start": raw[0]})
    if checksum(raw[:25]) != raw[25]:
        raise ChecksumError(
            "Legacy frame checksum mismatch",
            context={"expected": checksum(raw[:25]), "actual": raw[25]},
        )
    if expected_address is not None and raw[1] not in {expected_address, BROADCAST_ADDRESS}:
        raise LegacyProtocolError(
            "Legacy response address does not match request",
            context={"expected": expected_address, "actual": raw[1]},
        )
    return LegacyFrame(address=raw[1], command=raw[2], payload=bytes(raw[3:25]), raw=raw)


def pack_u16(value: int) -> bytes:
    if not 0 <= value <= 0xFFFF:
        raise LegacyProtocolError("Value does not fit unsigned 16-bit field")
    return value.to_bytes(2, "little", signed=False)


def unpack_u16(data: bytes) -> int:
    if len(data) != 2:
        raise ValueError("u16 requires exactly 2 bytes")
    return int.from_bytes(data, "little", signed=False)


def pack_u24(value: int) -> bytes:
    if not 0 <= value <= 0xFFFFFF:
        raise LegacyProtocolError("Value does not fit unsigned 24-bit field")
    return value.to_bytes(3, "little", signed=False)


def unpack_u24(data: bytes) -> int:
    if len(data) != 3:
        raise ValueError("u24 requires exactly 3 bytes")
    return int.from_bytes(data, "little", signed=False)


def pack_u32(value: int) -> bytes:
    if not 0 <= value <= 0xFFFFFFFF:
        raise LegacyProtocolError("Value does not fit unsigned 32-bit field")
    return value.to_bytes(4, "little", signed=False)


def unpack_u32(data: bytes) -> int:
    if len(data) != 4:
        raise ValueError("u32 requires exactly 4 bytes")
    return int.from_bytes(data, "little", signed=False)


def encode_scaled(value: float, scale: float, *, bits: int = 32) -> int:
    if not math.isfinite(value) or value < 0:
        raise LegacyProtocolError("Scaled legacy value must be finite and non-negative")
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("scale must be finite and positive")
    # Round half away from zero for positive instrument quantities.
    wire = int(math.floor(value / scale + 0.5))
    maximum = (1 << bits) - 1
    if wire > maximum:
        raise LegacyProtocolError("Scaled legacy value exceeds field width", context={"wire": wire, "bits": bits})
    return wire


def decode_scaled(wire: int, scale: float) -> float:
    if wire < 0:
        raise ValueError("wire must be non-negative")
    return wire * scale

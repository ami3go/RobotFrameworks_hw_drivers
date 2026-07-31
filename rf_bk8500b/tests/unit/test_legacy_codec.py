import pytest

from bk8500b import ChecksumError, FrameSyncError
from bk8500b.protocol.legacy_codec import (
    FRAME_LENGTH,
    build_frame,
    checksum,
    decode_frame,
    decode_scaled,
    encode_scaled,
    pack_u16,
    pack_u24,
    pack_u32,
    unpack_u16,
    unpack_u24,
    unpack_u32,
)


def test_empty_frame_golden_vector() -> None:
    frame = build_frame(0, 0x01)
    assert len(frame) == FRAME_LENGTH
    assert frame.hex() == "aa000100000000000000000000000000000000000000000000ab"
    decoded = decode_frame(frame, expected_address=0)
    assert decoded.command == 0x01
    assert decoded.address == 0


def test_checksum_is_sum_of_first_25_bytes() -> None:
    frame = build_frame(3, 0x21, b"\x01")
    assert frame[25] == checksum(frame[:25])


def test_corrupt_checksum_rejected() -> None:
    frame = bytearray(build_frame(0, 0x21, b"\x01"))
    frame[10] ^= 1
    with pytest.raises(ChecksumError):
        decode_frame(bytes(frame))


def test_bad_start_rejected() -> None:
    frame = bytearray(build_frame(0, 0x21))
    frame[0] = 0
    frame[25] = checksum(bytes(frame[:25]))
    with pytest.raises(FrameSyncError):
        decode_frame(bytes(frame))

@pytest.mark.parametrize("value", [0, 1, 255, 65535])
def test_u16_roundtrip(value: int) -> None:
    assert unpack_u16(pack_u16(value)) == value

@pytest.mark.parametrize("value", [0, 1, 65535, 0xFFFFFF])
def test_u24_roundtrip(value: int) -> None:
    assert unpack_u24(pack_u24(value)) == value

@pytest.mark.parametrize("value", [0, 1, 0xFFFFFF, 0xFFFFFFFF])
def test_u32_roundtrip(value: int) -> None:
    assert unpack_u32(pack_u32(value)) == value


def test_scaled_roundtrip_and_half_up_rounding() -> None:
    assert encode_scaled(1.2345, 0.001) == 1235
    assert decode_scaled(1235, 0.001) == pytest.approx(1.235)

from __future__ import annotations

import math
import pytest

from bk8500b.exceptions import LegacyProtocolError, UnsupportedFeatureError
from bk8500b.protocol.legacy_codec import (
    build_frame, decode_frame, decode_scaled, encode_scaled,
    pack_u16, pack_u24, pack_u32,
    unpack_u16, unpack_u24, unpack_u32,
)


@pytest.mark.parametrize("args", [(-1, 1, b""), (256, 1, b""), (0, -1, b""), (0, 256, b""), (0, 1, b"x"*23)])
def test_build_frame_validation(args):
    with pytest.raises(LegacyProtocolError): build_frame(*args)


def test_decode_frame_validation():
    good = build_frame(1, 2, b"abc")
    for bad in (b"", good[:-1], b"\x00" + good[1:]):
        with pytest.raises(LegacyProtocolError): decode_frame(bad)
    with pytest.raises(LegacyProtocolError): decode_frame(good, expected_address=2)
    corrupted = bytearray(good); corrupted[-1] ^= 1
    with pytest.raises(LegacyProtocolError): decode_frame(bytes(corrupted))


@pytest.mark.parametrize("fn,value", [(pack_u16,-1),(pack_u16,65536),(pack_u24,-1),(pack_u24,1<<24),(pack_u32,-1),(pack_u32,1<<32)])
def test_pack_ranges(fn, value):
    with pytest.raises(LegacyProtocolError): fn(value)


@pytest.mark.parametrize("fn,data", [(unpack_u16,b"x"),(unpack_u24,b"xx"),(unpack_u32,b"xxx")])
def test_unpack_lengths(fn, data):
    with pytest.raises(ValueError): fn(data)


@pytest.mark.parametrize("value,scale", [(-1,1),(math.nan,1),(1,0),(1,-1),(1e20,1e9)])
def test_scaled_encode_validation(value, scale):
    with pytest.raises((LegacyProtocolError, ValueError)): encode_scaled(value, scale)


def test_scaled_decode_validation():
    assert decode_scaled(10, 0.1) == 1.0
    with pytest.raises(ValueError): decode_scaled(-1, 1)


def test_checksum_requires_exact_input_length():
    from bk8500b.protocol.legacy_codec import checksum
    with pytest.raises(ValueError):
        checksum(b"short")

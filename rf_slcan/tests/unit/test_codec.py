"""Pure encode/decode/classify round-trips — no transport, no threading."""

from __future__ import annotations

import pytest

from slcan import codec
from slcan.enums import Bitrate, ChannelMode
from slcan.exceptions import SlcanProtocolError, SlcanValidationError
from slcan.models import AdapterStatus, CanFrame


def test_encode_open_and_close():
    assert codec.encode_open(ChannelMode.NORMAL) == b"O\r"
    assert codec.encode_open(ChannelMode.LISTEN_ONLY) == b"L\r"
    assert codec.encode_close() == b"C\r"


def test_encode_set_bitrate():
    assert codec.encode_set_bitrate(Bitrate.BPS_500K) == b"S6\r"
    assert codec.encode_set_bitrate(Bitrate.BPS_10K) == b"S0\r"


def test_encode_status_version_serial_queries():
    assert codec.encode_status_query() == b"F\r"
    assert codec.encode_version_query() == b"V\r"
    assert codec.encode_serial_query() == b"N\r"


def test_encode_transmit_standard_data_frame():
    frame = CanFrame(arbitration_id=0x123, data=b"\xaa\xbb\xcc", dlc=3)
    assert codec.encode_transmit(frame) == b"t1233AABBCC\r"


def test_encode_transmit_extended_data_frame():
    frame = CanFrame(arbitration_id=0x1ABCDEF, data=b"\x01", dlc=1, extended=True)
    assert codec.encode_transmit(frame) == b"T01ABCDEF101\r"


def test_encode_transmit_standard_remote_frame():
    frame = CanFrame(arbitration_id=0x321, data=b"", dlc=4, remote=True)
    assert codec.encode_transmit(frame) == b"r3214\r"


def test_encode_transmit_extended_remote_frame():
    frame = CanFrame(arbitration_id=0x1FFFFFFF, data=b"", dlc=0, extended=True, remote=True)
    assert codec.encode_transmit(frame) == b"R1FFFFFFF0\r"


def test_encode_transmit_rejects_standard_id_out_of_range():
    with pytest.raises(SlcanValidationError, match="out of range"):
        codec.encode_transmit(CanFrame(arbitration_id=0x800, data=b"", dlc=0))


def test_encode_transmit_rejects_extended_id_out_of_range():
    with pytest.raises(SlcanValidationError, match="out of range"):
        codec.encode_transmit(CanFrame(arbitration_id=0x20000000, data=b"", dlc=0, extended=True))


def test_encode_transmit_rejects_dlc_out_of_range():
    with pytest.raises(SlcanValidationError, match="dlc"):
        codec.encode_transmit(CanFrame(arbitration_id=1, data=b"", dlc=9))


def test_encode_transmit_rejects_data_length_mismatch():
    with pytest.raises(SlcanValidationError, match="data length"):
        codec.encode_transmit(CanFrame(arbitration_id=1, data=b"\x01\x02", dlc=3))


def test_classify_line_ack():
    assert codec.classify_line(b"\r") == b""


def test_classify_line_nack():
    assert codec.classify_line(b"\a") == b"\a"


def test_classify_line_status_response_is_returned_as_raw_bytes():
    assert codec.classify_line(b"F06\r") == b"F06"


def test_classify_line_frame_is_parsed():
    result = codec.classify_line(b"t1233AABBCC\r")
    assert result == CanFrame(arbitration_id=0x123, data=b"\xaa\xbb\xcc", dlc=3)


def test_classify_line_extended_remote_frame_round_trip():
    original = CanFrame(arbitration_id=0x1FFFFFFF, data=b"", dlc=5, extended=True, remote=True)
    encoded = codec.encode_transmit(original)
    assert codec.classify_line(encoded) == original


def test_parse_frame_line_rejects_empty():
    with pytest.raises(SlcanProtocolError):
        codec.parse_frame_line(b"")


def test_parse_frame_line_rejects_truncated():
    with pytest.raises(SlcanProtocolError):
        codec.parse_frame_line(b"t123")  # missing dlc


def test_parse_frame_line_rejects_truncated_data():
    with pytest.raises(SlcanProtocolError):
        codec.parse_frame_line(b"t1233AABB")  # dlc=3 but only 2 data bytes


def test_parse_status_flags():
    status = codec.parse_status_flags(b"F00")
    assert status == AdapterStatus(
        rx_queue_full=False,
        tx_queue_full=False,
        error_warning=False,
        data_overrun=False,
        error_passive=False,
        arbitration_lost=False,
        bus_error=False,
        raw_flags=0,
    )


def test_parse_status_flags_decodes_bus_error_bit():
    status = codec.parse_status_flags(b"F80")
    assert status.bus_error is True
    assert status.has_fault is True


def test_parse_status_flags_rejects_malformed():
    with pytest.raises(SlcanProtocolError):
        codec.parse_status_flags(b"FZZ")


def test_parse_version():
    assert codec.parse_version(b"V1013") == ("1.0", "1.3")


def test_parse_serial_number():
    assert codec.parse_serial_number(b"NA123") == "A123"

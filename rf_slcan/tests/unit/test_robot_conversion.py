"""Robot-facing data conversion and argument-normalization helpers."""

from __future__ import annotations

import pytest

from rf_slcan.library import SlcanLibrary, _as_bitrate, _as_bool, _as_bytes, _as_mode, _robot_value
from slcan.enums import Bitrate, ChannelMode
from slcan.exceptions import SlcanValidationError
from slcan.models import AdapterStatus, CanFrame


def test_canframe_dataclass_converts_to_plain_dict():
    frame = CanFrame(arbitration_id=0x123, data=b"\xaa\xbb", dlc=2, extended=False, remote=False)
    result = _robot_value(frame)
    assert result == {
        "arbitration_id": 0x123,
        "data": [0xAA, 0xBB],
        "dlc": 2,
        "extended": False,
        "remote": False,
        "timestamp_ms": None,
    }
    assert not hasattr(result, "arbitration_id")


def test_adapterstatus_dataclass_conversion():
    status = AdapterStatus(
        rx_queue_full=False,
        tx_queue_full=False,
        error_warning=False,
        data_overrun=False,
        error_passive=False,
        arbitration_lost=False,
        bus_error=True,
        raw_flags=0x80,
    )
    result = _robot_value(status)
    assert result["bus_error"] is True
    assert result["raw_flags"] == 0x80


def test_as_bool_accepts_common_forms():
    assert _as_bool(True) is True
    assert _as_bool("true") is True
    assert _as_bool("1") is True
    assert _as_bool("yes") is True
    assert _as_bool(False) is False
    assert _as_bool("false") is False
    assert _as_bool("") is False


def test_as_bool_rejects_garbage():
    with pytest.raises(SlcanValidationError):
        _as_bool("maybe")


def test_as_bitrate_accepts_named_forms():
    assert _as_bitrate("500K") is Bitrate.BPS_500K
    assert _as_bitrate("1m") is Bitrate.BPS_1M


def test_as_bitrate_accepts_raw_index():
    assert _as_bitrate("6") is Bitrate.BPS_500K
    assert _as_bitrate(0) is Bitrate.BPS_10K


def test_as_bitrate_rejects_garbage():
    with pytest.raises(SlcanValidationError):
        _as_bitrate("fast please")


def test_as_mode_accepts_common_forms():
    assert _as_mode("NORMAL") is ChannelMode.NORMAL
    assert _as_mode("listen_only") is ChannelMode.LISTEN_ONLY
    assert _as_mode("L") is ChannelMode.LISTEN_ONLY


def test_as_bytes_accepts_hex_string_list_and_bytes():
    assert _as_bytes("AABBCC") == b"\xaa\xbb\xcc"
    assert _as_bytes([1, 2, 3]) == b"\x01\x02\x03"
    assert _as_bytes(b"\x01\x02") == b"\x01\x02"
    assert _as_bytes("") == b""


def test_as_bytes_rejects_invalid_hex_string():
    with pytest.raises(SlcanValidationError):
        _as_bytes("not hex")


def test_library_receive_frame_returns_none_on_timeout():
    lib = SlcanLibrary()
    lib.connect(alias="can1", simulated=True)
    lib.set_bitrate("500K", alias="can1")
    lib.open_channel("NORMAL", alias="can1")
    assert lib.receive_frame(timeout_s=0.2, alias="can1") is None
    lib.disconnect("can1")


def test_library_end_suite_closes_all_sessions():
    lib = SlcanLibrary()
    lib.connect(alias="a", simulated=True)
    lib.connect(alias="b", simulated=True)
    driver_a = lib._session("a")
    driver_b = lib._session("b")

    lib._end_suite("Suite", {})

    assert driver_a.connected is False
    assert driver_b.connected is False
    assert lib.list_adapter_connections() == []
    assert lib.get_active_adapter() is None

import pytest

from eresistor_driver.validation import active_bits, normalize_mask, validate_channel


def test_normalize_mask():
    assert normalize_mask(1) == "0001"
    assert normalize_mask("0x00ff") == "00FF"
    assert normalize_mask("FFFF") == "FFFF"


def test_normalize_mask_rejects_bad():
    with pytest.raises(ValueError):
        normalize_mask("10000")
    with pytest.raises(ValueError):
        normalize_mask(-1)
    with pytest.raises(ValueError):
        normalize_mask("GGGG")


def test_active_bits():
    assert active_bits("0005") == [0, 2]


def test_validate_channel():
    assert validate_channel(1) == 1
    assert validate_channel(8) == 8
    with pytest.raises(ValueError):
        validate_channel(0)
    with pytest.raises(ValueError):
        validate_channel(9)

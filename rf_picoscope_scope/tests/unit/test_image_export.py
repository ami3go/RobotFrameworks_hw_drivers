"""Per-channel and combined waveform image export.

Every test starts with ``pytest.importorskip("matplotlib")`` since ``plot``
is an optional extra — these tests are meaningful only when it's installed,
and must not fail the suite when it isn't.
"""

from __future__ import annotations

import pytest

from picoscope_scope.driver import PicoScope
from picoscope_scope.exceptions import PicoScopeValidationError

_SAMPLE_INTERVAL_S = 20e-6
_NUM_SAMPLES = 50


@pytest.fixture
def captured_driver():
    d = PicoScope.connect_simulated()
    d.set_channel_enabled("A", True)
    d.set_channel_enabled("B", True)
    d.set_timebase(sample_interval_s=_SAMPLE_INTERVAL_S, num_samples=_NUM_SAMPLES)
    d.capture_block()
    yield d
    d.close()


def test_save_channel_image_writes_a_png(captured_driver, tmp_path):
    pytest.importorskip("matplotlib")
    out = tmp_path / "channel_a.png"
    captured_driver.save_channel_image(out, "A")
    assert out.exists()
    assert out.read_bytes().startswith(b"\x89PNG")


def test_save_channel_image_creates_parent_directories(captured_driver, tmp_path):
    pytest.importorskip("matplotlib")
    out = tmp_path / "nested" / "dir" / "channel_a.png"
    captured_driver.save_channel_image(out, "A")
    assert out.exists()


def test_save_all_channels_image_writes_a_single_png(captured_driver, tmp_path):
    pytest.importorskip("matplotlib")
    out = tmp_path / "all_channels.png"
    captured_driver.save_all_channels_image(out)
    assert out.exists()
    assert out.read_bytes().startswith(b"\x89PNG")


def test_image_export_without_matplotlib_raises_a_clear_error(captured_driver, tmp_path, monkeypatch):
    """Exercises the lazy-import failure path directly, independent of whether
    matplotlib happens to be installed in the environment running this test."""

    import builtins

    real_import = builtins.__import__

    def _blocked_import(name, *args, **kwargs):
        if name == "matplotlib":
            raise ImportError("simulated: matplotlib not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _blocked_import)

    with pytest.raises(PicoScopeValidationError, match="matplotlib is not installed"):
        captured_driver.save_channel_image(tmp_path / "out.png", "A")

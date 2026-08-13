"""matplotlib-rendered waveform images.

PicoScope 2000A units have no display to screenshot (unlike e.g. the
Tektronix TBS1000C), so "picture of a channel"/"picture of all channels" here
means rendering the decoded :class:`~picoscope2000a.models.Waveform` data
this driver already has, not capturing an on-device screen. Import of
``matplotlib`` is deferred to the point of use so the rest of this package
stays importable without it — install ``rf_picoscope2000a[plot]`` for image
export.
"""

from __future__ import annotations

from pathlib import Path

from .exceptions import PicoScope2000AValidationError
from .models import Waveform


def _import_matplotlib_pyplot():
    try:
        import matplotlib

        matplotlib.use("Agg")  # headless: never try to open a GUI window
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised only without the extra installed
        raise PicoScope2000AValidationError(
            "matplotlib is not installed; install rf_picoscope2000a[plot] for image export"
        ) from exc
    return plt


def _unit_label(unit: str) -> str:
    return "Voltage (V)" if unit == "V" else f"Current ({unit})" if unit == "A" else unit


def render_channel_image(waveform: Waveform, path: Path, title: str | None = None) -> None:
    plt = _import_matplotlib_pyplot()
    fig, ax = plt.subplots()
    try:
        ax.plot(waveform.time_s, waveform.values)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(_unit_label(waveform.unit))
        ax.set_title(title or f"Channel {waveform.channel}")
        ax.grid(True)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path)
    finally:
        plt.close(fig)


def render_all_channels_image(
    waveforms: dict[str, Waveform], path: Path, title: str | None = None
) -> None:
    """One figure, stacked subplots (one per channel, shared x-axis).

    Chosen over overlaying every channel on one axes because a mix of
    voltage- and current-probe channels have incompatible units — stacked
    subplots read cleanly regardless of the unit mix, no dual y-axes needed.
    """

    plt = _import_matplotlib_pyplot()
    channels = sorted(waveforms)
    if not channels:
        raise PicoScope2000AValidationError("no waveforms to render")
    fig, axes = plt.subplots(len(channels), 1, sharex=True, squeeze=False)
    try:
        for row, channel in zip(axes, channels):
            ax = row[0]
            waveform = waveforms[channel]
            ax.plot(waveform.time_s, waveform.values)
            ax.set_ylabel(f"CH{channel} ({waveform.unit})")
            ax.grid(True)
        axes[-1][0].set_xlabel("Time (s)")
        fig.suptitle(title or "All channels")
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path)
    finally:
        plt.close(fig)

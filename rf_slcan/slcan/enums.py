"""Enums for SLCAN protocol argument values.

Unlike SCPI, SLCAN has no long/short mnemonic forms — each command is a
single fixed ASCII letter, so there's no need for the prefix-matching
``_missing_`` hook used by the SCPI-flavored sibling drivers' enums.
"""

from __future__ import annotations

from enum import Enum


class Bitrate(Enum):
    """Standard nominal CAN bitrates, valued by their ``S<n>`` command index."""

    BPS_10K = 0
    BPS_20K = 1
    BPS_50K = 2
    BPS_100K = 3
    BPS_125K = 4
    BPS_250K = 5
    BPS_500K = 6
    BPS_800K = 7
    BPS_1M = 8

    @property
    def nominal_bps(self) -> int:
        return _NOMINAL_BPS[self]


_NOMINAL_BPS: dict[Bitrate, int] = {
    Bitrate.BPS_10K: 10_000,
    Bitrate.BPS_20K: 20_000,
    Bitrate.BPS_50K: 50_000,
    Bitrate.BPS_100K: 100_000,
    Bitrate.BPS_125K: 125_000,
    Bitrate.BPS_250K: 250_000,
    Bitrate.BPS_500K: 500_000,
    Bitrate.BPS_800K: 800_000,
    Bitrate.BPS_1M: 1_000_000,
}


class ChannelMode(str, Enum):
    """The channel-open command letter: ``O`` (normal) or ``L`` (listen-only)."""

    NORMAL = "O"
    LISTEN_ONLY = "L"

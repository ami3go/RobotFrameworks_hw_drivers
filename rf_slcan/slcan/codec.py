"""Pure SLCAN wire-format encode/decode/classify — no I/O, no threading.

Every command is a single ASCII line terminated by ``\\r`` (CR) on success.
The adapter acknowledges a command with a bare ``\\r`` (empty body) or
rejects it with a bare ``\\a`` (BEL, 0x07) — and BEL is sent standalone,
never CR-terminated, which is why the reader (``reader.py``) reads until it
sees *either* terminator rather than just ``\\r`` (see ``read_until`` on
:class:`slcan.transport.Transport`).

A received/echoed CAN frame arrives as its own line: ``t``/``T`` for a
standard/extended data frame, ``r``/``R`` for a standard/extended remote
(RTR) frame. Everything else that isn't a frame line (a bare ack, a status/
version/serial query's data response) is returned to the caller as raw
bytes and interpreted contextually by :meth:`slcan.driver.SlcanAdapter.
_send_command`, since SLCAN gives no other way to tell "this is the answer
to the command I just sent" apart from serializing one command at a time.

Bit assignments in :func:`parse_status_flags` and this driver's command set
are drawn from the widely-mirrored Lawicel CAN232/CANUSB ASCII protocol —
see the task document (task §2) for the pinned citation this implementation
was built against.
"""

from __future__ import annotations

from .enums import Bitrate, ChannelMode
from .exceptions import SlcanProtocolError, SlcanValidationError
from .models import AdapterStatus, CanFrame

_FRAME_PREFIXES = (b"t", b"T", b"r", b"R")

BEL = b"\a"
CR = b"\r"
TERMINATORS: tuple[bytes, ...] = (CR, BEL)

_STANDARD_ID_MAX = 0x7FF
_EXTENDED_ID_MAX = 0x1FFFFFFF
_MAX_DLC = 8


# ----------------------------------------------------------------------
# Encoding (driver -> adapter)
# ----------------------------------------------------------------------
def encode_open(mode: ChannelMode) -> bytes:
    return mode.value.encode("ascii") + CR


def encode_close() -> bytes:
    return b"C" + CR


def encode_set_bitrate(bitrate: Bitrate) -> bytes:
    return f"S{bitrate.value}".encode("ascii") + CR


def encode_status_query() -> bytes:
    return b"F" + CR


def encode_version_query() -> bytes:
    return b"V" + CR


def encode_serial_query() -> bytes:
    return b"N" + CR


def encode_transmit(frame: CanFrame) -> bytes:
    """Builds a ``t``/``T``/``r``/``R`` transmit line. Raises
    :class:`SlcanValidationError` for any value that can't be represented
    on the wire — this is the single source of truth for frame validation,
    independently testable without a transport or driver instance."""

    id_max = _EXTENDED_ID_MAX if frame.extended else _STANDARD_ID_MAX
    if not (0 <= frame.arbitration_id <= id_max):
        raise SlcanValidationError(
            f"arbitration_id {frame.arbitration_id:#x} out of range for "
            f"{'extended' if frame.extended else 'standard'} frame (0-{id_max:#x})"
        )
    if not (0 <= frame.dlc <= _MAX_DLC):
        raise SlcanValidationError(f"dlc must be 0-{_MAX_DLC}, got {frame.dlc}")

    id_hex = f"{frame.arbitration_id:08X}" if frame.extended else f"{frame.arbitration_id:03X}"
    head = ("R" if frame.extended else "r") if frame.remote else ("T" if frame.extended else "t")

    if frame.remote:
        body = f"{head}{id_hex}{frame.dlc:01X}"
    else:
        if len(frame.data) != frame.dlc:
            raise SlcanValidationError(
                f"data length {len(frame.data)} does not match dlc {frame.dlc}"
            )
        body = f"{head}{id_hex}{frame.dlc:01X}{frame.data.hex().upper()}"
    return body.encode("ascii") + CR


# ----------------------------------------------------------------------
# Decoding / classification (adapter -> driver)
# ----------------------------------------------------------------------
def classify_line(raw: bytes) -> CanFrame | bytes:
    """Routes one terminated line from the adapter.

    Returns a parsed :class:`CanFrame` if the line is a frame notification;
    otherwise returns the line's body with the terminator stripped (``b""``
    for a bare ack, ``b"\\a"`` for a nack, or the raw data of a query
    response such as ``b"F06"``/``b"V1013"``/``b"NA123"``) for the caller to
    interpret.
    """

    if raw == BEL:
        return BEL
    body = raw[:-1] if raw.endswith(CR) else raw
    if body[:1] in _FRAME_PREFIXES:
        return parse_frame_line(body)
    return body


def parse_frame_line(body: bytes) -> CanFrame:
    if not body:
        raise SlcanProtocolError("empty frame line")
    try:
        text = body.decode("ascii")
    except UnicodeDecodeError as exc:
        raise SlcanProtocolError(f"non-ASCII frame line: {body!r}") from exc

    head = text[0]
    if head not in ("t", "T", "r", "R"):
        raise SlcanProtocolError(f"unrecognized line: {text!r}")
    extended = head in ("T", "R")
    remote = head in ("r", "R")
    id_len = 8 if extended else 3
    rest = text[1:]
    if len(rest) < id_len + 1:
        raise SlcanProtocolError(f"truncated frame line: {text!r}")

    id_hex, dlc_hex = rest[:id_len], rest[id_len]
    try:
        arbitration_id = int(id_hex, 16)
        dlc = int(dlc_hex, 16)
    except ValueError as exc:
        raise SlcanProtocolError(f"malformed frame line: {text!r}") from exc
    if dlc > _MAX_DLC:
        raise SlcanProtocolError(f"dlc out of range in frame line: {text!r}")

    data_hex = rest[id_len + 1 :]
    if remote:
        data = b""
    else:
        expected_len = dlc * 2
        if len(data_hex) < expected_len:
            raise SlcanProtocolError(f"truncated frame data: {text!r}")
        try:
            data = bytes.fromhex(data_hex[:expected_len])
        except ValueError as exc:
            raise SlcanProtocolError(f"malformed frame data: {text!r}") from exc

    return CanFrame(
        arbitration_id=arbitration_id, data=data, dlc=dlc, extended=extended, remote=remote
    )


def parse_status_flags(raw: bytes) -> AdapterStatus:
    """Parses an ``F<hex-byte>`` status response.

    Bit layout per the task document's cited source: bit0 RX queue full,
    bit1 TX queue full, bit2 error warning, bit3 data overrun, bit4
    reserved/unused, bit5 error passive, bit6 arbitration lost, bit7 bus
    error.
    """

    text = raw.decode("ascii", errors="replace")
    if not text.startswith("F") or len(text) < 3:
        raise SlcanProtocolError(f"malformed status response: {text!r}")
    try:
        flags = int(text[1:3], 16)
    except ValueError as exc:
        raise SlcanProtocolError(f"malformed status response: {text!r}") from exc
    return AdapterStatus(
        rx_queue_full=bool(flags & 0x01),
        tx_queue_full=bool(flags & 0x02),
        error_warning=bool(flags & 0x04),
        data_overrun=bool(flags & 0x08),
        error_passive=bool(flags & 0x20),
        arbitration_lost=bool(flags & 0x40),
        bus_error=bool(flags & 0x80),
        raw_flags=flags,
    )


def parse_version(raw: bytes) -> tuple[str, str]:
    """Parses a ``V<hw:2hex><sw:2hex>`` response into (hardware, software)."""

    text = raw.decode("ascii", errors="replace")
    if not text.startswith("V") or len(text) < 5:
        raise SlcanProtocolError(f"malformed version response: {text!r}")
    hw, sw = text[1:3], text[3:5]
    return f"{hw[0]}.{hw[1]}", f"{sw[0]}.{sw[1]}"


def parse_serial_number(raw: bytes) -> str:
    """Parses an ``N<4hex>`` response into its serial-number string."""

    text = raw.decode("ascii", errors="replace")
    if not text.startswith("N") or len(text) < 5:
        raise SlcanProtocolError(f"malformed serial-number response: {text!r}")
    return text[1:5]

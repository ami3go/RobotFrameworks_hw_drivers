"""Robot Framework adapter for :mod:`slcan`.

Keeps SLCAN command construction/parsing and the background reader thread
entirely in the core driver — this module only converts arguments/results
and manages named sessions. ``_end_suite`` is the critical safety net here:
it guarantees background reader threads don't leak past a suite that
forgets ``Disconnect``.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

try:  # Robot Framework is optional at import time so pytest can run standalone.
    from robot.api import logger as _rf_logger
    from robot.api.deco import keyword, library
except ImportError:  # pragma: no cover

    class _FallbackLogger:
        @staticmethod
        def info(message: str, *_args: Any, **_kwargs: Any) -> None:
            print(message)

        warn = error = debug = info

    _rf_logger = _FallbackLogger()

    def keyword(name: str | None = None, tags: tuple[str, ...] = ()):  # type: ignore[misc]
        def decorate(func):
            func.robot_name = name or func.__name__.replace("_", " ").title()
            func.robot_tags = tags
            return func

        return decorate

    def library(**_kwargs: Any):  # type: ignore[misc]
        return lambda cls: cls


from slcan import SlcanAdapter
from slcan.enums import Bitrate, ChannelMode
from slcan.exceptions import SlcanConnectionError, SlcanValidationError

_BITRATE_BY_NAME = {
    "10K": Bitrate.BPS_10K,
    "20K": Bitrate.BPS_20K,
    "50K": Bitrate.BPS_50K,
    "100K": Bitrate.BPS_100K,
    "125K": Bitrate.BPS_125K,
    "250K": Bitrate.BPS_250K,
    "500K": Bitrate.BPS_500K,
    "800K": Bitrate.BPS_800K,
    "1M": Bitrate.BPS_1M,
}


def _as_bool(value: Any, name: str = "value") -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off", "", "none"}:
            return False
    raise SlcanValidationError(f"{name} must be a Boolean, got {value!r}")


def _as_bitrate(value: Any) -> Bitrate:
    if isinstance(value, Bitrate):
        return value
    token = str(value).strip().upper()
    if token in _BITRATE_BY_NAME:
        return _BITRATE_BY_NAME[token]
    try:
        return Bitrate(int(token))
    except (ValueError, KeyError) as exc:
        known = ", ".join(sorted(_BITRATE_BY_NAME))
        raise SlcanValidationError(f"bitrate must be one of {known} (or an S-index), got {value!r}") from exc


def _as_mode(value: Any) -> ChannelMode:
    if isinstance(value, ChannelMode):
        return value
    token = str(value).strip().upper()
    if token in ("NORMAL", "O"):
        return ChannelMode.NORMAL
    if token in ("LISTEN_ONLY", "LISTEN-ONLY", "L"):
        return ChannelMode.LISTEN_ONLY
    raise SlcanValidationError(f"mode must be NORMAL or LISTEN_ONLY, got {value!r}")


def _as_register_value(value: Any, name: str) -> int:
    """Accepts an int, or a string in decimal or ``0x``-prefixed hex — for the
    acceptance code/mask registers (Gate 3), which are naturally hex values."""

    if isinstance(value, int) and not isinstance(value, bool):
        return value
    try:
        return int(str(value).strip(), 0)
    except ValueError as exc:
        raise SlcanValidationError(f"{name} must be an integer or hex string, got {value!r}") from exc


def _robot_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _robot_value(v) for k, v in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, bytes):
        return list(value)
    if isinstance(value, (list, tuple)):
        return [_robot_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _robot_value(v) for k, v in value.items()}
    return value


@library(scope="SUITE", version="26.1", auto_keywords=False)
class SlcanLibrary:
    """Robot Framework keywords for SLCAN (serial-line CAN) interface adapters.

    The RFDS-002 canonical connection keywords (``Connect``, ``Disconnect``,
    ``Is Connected``, ``Get Connection State``, ``Check Communication``,
    ``Get Identity``) are the primary, documented connection API — see the
    task document, task §7. No hardware is touched on library import.
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = "26.1"

    def __init__(self) -> None:
        self._sessions: dict[str, SlcanAdapter] = {}
        self._active_alias: str | None = None
        self.ROBOT_LIBRARY_LISTENER = self

    def _end_suite(self, name: str, attributes: dict[str, Any]) -> None:
        del name, attributes
        for alias in list(self._sessions):
            try:
                self._sessions[alias].close()
            except Exception as exc:  # noqa: BLE001 - cleanup must not hide an earlier suite failure
                _rf_logger.warn(f"Slcan: cleanup for {alias!r} reported: {exc}")  # noqa: G010
        self._sessions.clear()
        self._active_alias = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_alias(self, alias: str | None) -> str | None:
        return str(alias) if alias not in (None, "") else self._active_alias

    def _session(self, alias: str | None = None) -> SlcanAdapter:
        selected = self._resolve_alias(alias)
        if selected is None:
            raise SlcanConnectionError("no SLCAN connection is active; call 'Connect' first")
        try:
            return self._sessions[selected]
        except KeyError as exc:
            known = ", ".join(sorted(self._sessions)) or "none"
            raise SlcanConnectionError(f"unknown SLCAN alias {selected!r}; known aliases: {known}") from exc

    def _connection_state(self, alias: str, driver: SlcanAdapter) -> dict[str, Any]:
        """RFDS-002 Section 12.1 normalized connection-state dictionary."""

        if not driver.connected:
            return {
                "alias": alias,
                "resource": None,
                "connected": False,
                "communication_ok": False,
                "transport": None,
                "identity": None,
                "timeout_s": None,
                "state": "disconnected",
            }
        identity_str: str | None = None
        try:
            identity_str = driver.identify(refresh=False).raw
        except Exception:  # noqa: BLE001 - a stale/failed identity read must not prevent
            # reporting connection state; communication_ok below already reflects this as False.
            identity_str = None
        return {
            "alias": alias,
            "resource": driver.resource,
            "connected": True,
            "communication_ok": identity_str is not None,
            "transport": type(driver.transport).__name__,
            "identity": identity_str,
            "timeout_s": driver.timeout_s,
            "state": "connected",
        }

    # ------------------------------------------------------------------
    # RFDS-002 canonical connection keywords (task §7)
    # ------------------------------------------------------------------
    @keyword("Connect")
    def connect(
        self,
        resource: str | None = None,
        alias: str = "default",
        timeout_s: float | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        """Connect over a serial port, or the bundled simulator with ``simulated=True``.

        Idempotent when ``alias`` is already connected to the same ``resource``.
        """

        selected_alias = str(alias).strip() or "default"
        if selected_alias in self._sessions:
            existing = self._sessions[selected_alias]
            if resource and existing.connected and str(existing.resource) != str(resource):
                raise SlcanConnectionError(
                    f"alias {selected_alias!r} is already connected to {existing.resource!r}; "
                    f"disconnect it before connecting it to {resource!r}."
                )
            self._active_alias = selected_alias
            return self._connection_state(selected_alias, existing)

        simulated = _as_bool(options.pop("simulated", False), "simulated")
        if simulated:
            driver = SlcanAdapter.connect_simulated(timeout_s=timeout_s or 2.0)
        else:
            if not resource:
                raise SlcanValidationError("resource is required (a serial port) unless simulated=True")
            driver = SlcanAdapter.connect_serial(str(resource), timeout_s=timeout_s or 2.0)
        self._sessions[selected_alias] = driver
        self._active_alias = selected_alias
        _rf_logger.info(f"Slcan: connected alias={selected_alias!r} resource={driver.resource!r}")
        return self._connection_state(selected_alias, driver)

    @keyword("Disconnect")
    def disconnect(self, alias: str | None = None) -> None:
        """Idempotent: succeeds even if already disconnected."""

        selected = self._resolve_alias(alias)
        if selected is None or selected not in self._sessions:
            return
        self._sessions.pop(selected).close()
        if self._active_alias == selected:
            self._active_alias = next(iter(self._sessions), None)

    @keyword("Is Connected")
    def is_connected(self, alias: str | None = None) -> bool:
        selected = self._resolve_alias(alias)
        if selected is None or selected not in self._sessions:
            return False
        return self._sessions[selected].connected

    @keyword("Get Connection State")
    def get_connection_state(self, alias: str | None = None, refresh: bool = False) -> dict[str, Any]:
        selected = self._resolve_alias(alias)
        if selected is None or selected not in self._sessions:
            return {
                "alias": selected or "default",
                "resource": None,
                "connected": False,
                "communication_ok": False,
                "transport": None,
                "identity": None,
                "timeout_s": None,
                "state": "disconnected",
            }
        driver = self._sessions[selected]
        if _as_bool(refresh, "refresh") and driver.connected:
            try:
                driver.check_communication()
            except Exception:  # noqa: BLE001, S110 - a failed probe is itself the answer: it
                # shows up as communication_ok=False below, not as a raised error here.
                pass
        return self._connection_state(selected, driver)

    @keyword("Check Communication")
    def check_communication(self, alias: str | None = None) -> bool:
        return self._session(alias).check_communication()

    @keyword("Get Identity")
    def get_identity(self, alias: str | None = None, refresh: bool = True) -> str:
        return self._session(alias).identify(refresh=_as_bool(refresh, "refresh")).raw

    @keyword("Switch Adapter")
    def switch_adapter(self, alias: str) -> str:
        self._session(alias)
        self._active_alias = str(alias)
        return self._active_alias

    @keyword("Get Active Adapter")
    def get_active_adapter(self) -> str | None:
        return self._active_alias

    @keyword("List Adapter Connections")
    def list_adapter_connections(self) -> list[str]:
        return sorted(self._sessions)

    # ------------------------------------------------------------------
    # Channel control
    # ------------------------------------------------------------------
    @keyword("Set Bitrate")
    def set_bitrate(self, bitrate: Any, alias: str | None = None) -> None:
        """``bitrate`` accepts ``10K``/``20K``/.../``1M`` or a raw ``S<n>`` index (0-8)."""

        self._session(alias).set_bitrate(_as_bitrate(bitrate))

    @keyword("Open Channel")
    def open_channel(self, mode: Any = "NORMAL", alias: str | None = None) -> None:
        """``mode`` is ``NORMAL`` (default) or ``LISTEN_ONLY``."""

        self._session(alias).open_channel(_as_mode(mode))

    @keyword("Close Channel")
    def close_channel(self, alias: str | None = None) -> None:
        self._session(alias).close_channel()

    @keyword("Is Channel Open")
    def is_channel_open(self, alias: str | None = None) -> bool:
        return self._session(alias).channel_open

    # ------------------------------------------------------------------
    # Acceptance filter (Gate 3) — rejected by the adapter while the
    # channel is open, same as Set Bitrate.
    # ------------------------------------------------------------------
    @keyword("Set Acceptance Code")
    def set_acceptance_code(self, code: Any, alias: str | None = None) -> None:
        self._session(alias).set_acceptance_code(_as_register_value(code, "code"))

    @keyword("Get Acceptance Code")
    def get_acceptance_code(self, alias: str | None = None) -> int | None:
        """Read-only, driver-tracked — the adapter has no query form for this."""

        return self._session(alias).get_acceptance_code()

    @keyword("Set Acceptance Mask")
    def set_acceptance_mask(self, mask: Any, alias: str | None = None) -> None:
        self._session(alias).set_acceptance_mask(_as_register_value(mask, "mask"))

    @keyword("Get Acceptance Mask")
    def get_acceptance_mask(self, alias: str | None = None) -> int | None:
        """Read-only, driver-tracked — the adapter has no query form for this."""

        return self._session(alias).get_acceptance_mask()

    # ------------------------------------------------------------------
    # Timestamp mode (Gate 3)
    # ------------------------------------------------------------------
    @keyword("Set Timestamps Enabled")
    def set_timestamps_enabled(self, enabled: bool, alias: str | None = None) -> None:
        self._session(alias).set_timestamps_enabled(_as_bool(enabled, "enabled"))

    @keyword("Get Timestamps Enabled")
    def get_timestamps_enabled(self, alias: str | None = None) -> bool:
        """Read-only, driver-tracked — the adapter has no query form for this."""

        return self._session(alias).get_timestamps_enabled()

    # ------------------------------------------------------------------
    # Frames
    # ------------------------------------------------------------------
    @keyword("Send Frame")
    def send_frame(
        self,
        arbitration_id: int,
        data: Any = b"",
        extended: bool = False,
        remote: bool = False,
        alias: str | None = None,
    ) -> None:
        """``data`` accepts bytes, a list/tuple of ints, or a hex string like ``"AABBCC"``."""

        payload = _as_bytes(data)
        self._session(alias).send_frame(
            int(arbitration_id),
            payload,
            extended=_as_bool(extended, "extended"),
            remote=_as_bool(remote, "remote"),
        )

    @keyword("Receive Frame")
    def receive_frame(self, timeout_s: float = 1.0, alias: str | None = None) -> dict[str, Any] | None:
        """Blocks up to ``timeout_s``. Returns ``${None}`` on timeout — receiving
        nothing is a normal outcome, not an error."""

        frame = self._session(alias).receive_frame(timeout_s=float(timeout_s))
        return _robot_value(frame) if frame is not None else None

    @keyword("Drain Received Frames")
    def drain_received_frames(self, max_count: Any = None, alias: str | None = None) -> list[dict[str, Any]]:
        count = None if max_count in (None, "") else int(max_count)
        frames = self._session(alias).drain_received_frames(max_count=count)
        return [_robot_value(frame) for frame in frames]

    @keyword("Get Received Frame Count")
    def get_received_frame_count(self, alias: str | None = None) -> int:
        return self._session(alias).get_received_frame_count()

    @keyword("Clear Received Frames")
    def clear_received_frames(self, alias: str | None = None) -> None:
        self._session(alias).clear_received_frames()

    @keyword("Get Receive Overflow Count")
    def get_receive_overflow_count(self, alias: str | None = None) -> int:
        """Read-only. Counts frames dropped because the receive queue was full
        (no keyword drained it fast enough)."""

        return self._session(alias).get_receive_overflow_count()

    # ------------------------------------------------------------------
    # Status / identity queries
    # ------------------------------------------------------------------
    @keyword("Get Status")
    def get_status(self, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_status())

    @keyword("Get Version")
    def get_version(self, alias: str | None = None) -> str:
        return str(self._session(alias).get_version())

    @keyword("Get Serial Number")
    def get_serial_number(self, alias: str | None = None) -> str:
        return str(self._session(alias).get_serial_number())

    # ------------------------------------------------------------------
    # Raw escape hatch
    # ------------------------------------------------------------------
    @keyword("Enable Raw SLCAN")
    def enable_raw_slcan(self, confirmation: str, alias: str | None = None) -> None:
        self._session(alias).enable_raw_slcan(confirmation)

    @keyword("Raw SLCAN Command")
    def raw_slcan_command(self, command: str, expects_data: bool = False, alias: str | None = None) -> str:
        """Bypasses typed validation."""

        return self._session(alias).raw_command(command, expects_data=_as_bool(expects_data, "expects_data"))


def _as_bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, (list, tuple)):
        return bytes(int(v) for v in value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return b""
        try:
            return bytes.fromhex(text)
        except ValueError as exc:
            raise SlcanValidationError(f"data must be a valid hex string, got {value!r}") from exc
    raise SlcanValidationError(f"data must be bytes, a list of ints, or a hex string, got {value!r}")

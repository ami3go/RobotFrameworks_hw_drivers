"""Robot Framework adapter for :mod:`tbs1000c`.

Keeps SCPI construction, waveform decode, and validation entirely in the
core driver (task §5.2) — this module only converts arguments/results and
manages named sessions.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
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


from tbs1000c import Tbs1000c
from tbs1000c.exceptions import Tbs1000cConnectionError, Tbs1000cValidationError


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
    raise Tbs1000cValidationError(f"{name} must be a Boolean, got {value!r}")


def _robot_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _robot_value(v) for k, v in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (list, tuple)):
        return [_robot_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _robot_value(v) for k, v in value.items()}
    return value


@library(scope="SUITE", version="26.1", auto_keywords=False)
class Tbs1000cLibrary:
    """Robot Framework keywords for the Tektronix TBS1000C series oscilloscopes.

    The RFDS-002 canonical connection keywords (``Connect``, ``Disconnect``,
    ``Is Connected``, ``Get Connection State``, ``Check Communication``,
    ``Get Identity``) are the primary, documented connection API — see the
    task document, task §7. No hardware is touched on library import.
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = "26.1"

    def __init__(self) -> None:
        self._sessions: dict[str, Tbs1000c] = {}
        self._active_alias: str | None = None
        self.ROBOT_LIBRARY_LISTENER = self

    # Robot listener hook: best-effort cleanup at suite end.
    def _end_suite(self, name: str, attributes: dict[str, Any]) -> None:
        del name, attributes
        for alias in list(self._sessions):
            try:
                self._sessions[alias].close()
            except Exception as exc:  # noqa: BLE001 - cleanup must not hide an earlier suite failure
                _rf_logger.warn(f"TBS1000C: cleanup for {alias!r} reported: {exc}")  # noqa: G010 - robot.api.logger has no .warning
        self._sessions.clear()
        self._active_alias = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_alias(self, alias: str | None) -> str | None:
        return str(alias) if alias not in (None, "") else self._active_alias

    def _session(self, alias: str | None = None) -> Tbs1000c:
        selected = self._resolve_alias(alias)
        if selected is None:
            raise Tbs1000cConnectionError("no TBS1000C connection is active; call 'Connect' first")
        try:
            return self._sessions[selected]
        except KeyError as exc:
            known = ", ".join(sorted(self._sessions)) or "none"
            raise Tbs1000cConnectionError(
                f"unknown TBS1000C alias {selected!r}; known aliases: {known}"
            ) from exc

    def _connection_state(self, alias: str, driver: Tbs1000c) -> dict[str, Any]:
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
        """Connect to a TBS1000C over USBTMC, or the bundled simulator with ``simulated=True``.

        Idempotent when ``alias`` is already connected to the same ``resource``.
        """

        selected_alias = str(alias).strip() or "default"
        if selected_alias in self._sessions:
            existing = self._sessions[selected_alias]
            if resource and existing.connected and str(existing.resource) != str(resource):
                raise Tbs1000cConnectionError(
                    f"alias {selected_alias!r} is already connected to {existing.resource!r}; "
                    f"disconnect it before connecting it to {resource!r}."
                )
            self._active_alias = selected_alias
            return self._connection_state(selected_alias, existing)

        simulated = _as_bool(options.pop("simulated", False), "simulated")
        if simulated:
            driver = Tbs1000c.connect_simulated()
        else:
            if not resource:
                raise Tbs1000cValidationError("resource is required unless simulated=True")
            driver = Tbs1000c.connect_usbtmc(str(resource), timeout_s=timeout_s or 5.0)
        self._sessions[selected_alias] = driver
        self._active_alias = selected_alias
        _rf_logger.info(f"TBS1000C: connected alias={selected_alias!r} resource={driver.resource!r}")
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

    @keyword("Switch Oscilloscope")
    def switch_oscilloscope(self, alias: str) -> str:
        self._session(alias)
        self._active_alias = str(alias)
        return self._active_alias

    @keyword("Get Active Oscilloscope")
    def get_active_oscilloscope(self) -> str | None:
        return self._active_alias

    @keyword("List Oscilloscope Connections")
    def list_oscilloscope_connections(self) -> list[str]:
        return sorted(self._sessions)

    # ------------------------------------------------------------------
    # Channel configuration (task §8)
    # ------------------------------------------------------------------
    @keyword("Set Channel Scale")
    def set_channel_scale(self, channel: int, volts_per_div: float, alias: str | None = None) -> None:
        self._session(alias).set_channel_scale(channel, float(volts_per_div))

    @keyword("Get Channel Scale")
    def get_channel_scale(self, channel: int, alias: str | None = None) -> float:
        return self._session(alias).get_channel_scale(channel)

    @keyword("Set Channel Position")
    def set_channel_position(self, channel: int, divisions: float, alias: str | None = None) -> None:
        self._session(alias).set_channel_position(channel, float(divisions))

    @keyword("Get Channel Position")
    def get_channel_position(self, channel: int, alias: str | None = None) -> float:
        return self._session(alias).get_channel_position(channel)

    @keyword("Set Channel Offset")
    def set_channel_offset(self, channel: int, volts: float, alias: str | None = None) -> None:
        self._session(alias).set_channel_offset(channel, float(volts))

    @keyword("Get Channel Offset")
    def get_channel_offset(self, channel: int, alias: str | None = None) -> float:
        return self._session(alias).get_channel_offset(channel)

    @keyword("Set Channel Coupling")
    def set_channel_coupling(self, channel: int, coupling: str, alias: str | None = None) -> None:
        self._session(alias).set_channel_coupling(channel, coupling)

    @keyword("Get Channel Coupling")
    def get_channel_coupling(self, channel: int, alias: str | None = None) -> str:
        return self._session(alias).get_channel_coupling(channel).value

    @keyword("Set Channel Bandwidth Limit")
    def set_channel_bandwidth_limit(
        self, channel: int, value: str, alias: str | None = None
    ) -> None:
        self._session(alias).set_channel_bandwidth_limit(channel, value)

    @keyword("Get Channel Bandwidth Limit")
    def get_channel_bandwidth_limit(self, channel: int, alias: str | None = None) -> str:
        return self._session(alias).get_channel_bandwidth_limit(channel)

    @keyword("Set Channel Probe Gain")
    def set_channel_probe_gain(self, channel: int, gain: float, alias: str | None = None) -> None:
        self._session(alias).set_channel_probe_gain(channel, float(gain))

    @keyword("Get Channel Probe Gain")
    def get_channel_probe_gain(self, channel: int, alias: str | None = None) -> float:
        return self._session(alias).get_channel_probe_gain(channel)

    @keyword("Set Channel Name")
    def set_channel_name(self, channel: int, name: str | None = None, alias: str | None = None) -> None:
        """CH<x>:LABel. Max 30 characters; rejected before any device I/O if too long."""

        self._session(alias).set_channel_name(channel, name)

    @keyword("Get Channel Name")
    def get_channel_name(self, channel: int, alias: str | None = None) -> str:
        return self._session(alias).get_channel_name(channel)

    @keyword("Get Channel Settings")
    def get_channel_settings(self, channel: int, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_channel_settings(channel))

    # ------------------------------------------------------------------
    # Trigger (task §8)
    # ------------------------------------------------------------------
    @keyword("Set Trigger Source")
    def set_trigger_source(self, channel: int, alias: str | None = None) -> None:
        self._session(alias).set_trigger_source(channel)

    @keyword("Get Trigger Source")
    def get_trigger_source(self, alias: str | None = None) -> str:
        return self._session(alias).get_trigger_source()

    @keyword("Set Trigger Slope")
    def set_trigger_slope(self, slope: str, alias: str | None = None) -> None:
        self._session(alias).set_trigger_slope(slope)

    @keyword("Get Trigger Slope")
    def get_trigger_slope(self, alias: str | None = None) -> str:
        return self._session(alias).get_trigger_slope().value

    @keyword("Set Trigger Coupling")
    def set_trigger_coupling(self, coupling: str, alias: str | None = None) -> None:
        self._session(alias).set_trigger_coupling(coupling)

    @keyword("Get Trigger Coupling")
    def get_trigger_coupling(self, alias: str | None = None) -> str:
        return self._session(alias).get_trigger_coupling().value

    @keyword("Set Trigger Level")
    def set_trigger_level(self, level_v: float, alias: str | None = None) -> None:
        self._session(alias).set_trigger_level(float(level_v))

    @keyword("Get Trigger Level")
    def get_trigger_level(self, alias: str | None = None) -> float:
        return self._session(alias).get_trigger_level()

    @keyword("Auto Set Trigger Level")
    def auto_set_trigger_level(self, alias: str | None = None) -> None:
        self._session(alias).auto_set_trigger_level()

    @keyword("Force Trigger")
    def force_trigger(self, alias: str | None = None) -> None:
        self._session(alias).force_trigger()

    @keyword("Get Trigger Settings")
    def get_trigger_settings(self, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_trigger_settings())

    # ------------------------------------------------------------------
    # Acquisition and autoset (task §6 item 1, §8)
    # ------------------------------------------------------------------
    @keyword("Run Autoset")
    def run_autoset(self, alias: str | None = None) -> None:
        """Changes vertical scale, trigger level, and timebase. Logged; never automatic."""

        self._session(alias).run_autoset()

    @keyword("Start Acquisition")
    def start_acquisition(self, alias: str | None = None) -> None:
        self._session(alias).start_acquisition()

    @keyword("Stop Acquisition")
    def stop_acquisition(self, alias: str | None = None) -> None:
        self._session(alias).stop_acquisition()

    @keyword("Set Acquisition Mode")
    def set_acquisition_mode(self, mode: str, alias: str | None = None) -> None:
        self._session(alias).set_acquisition_mode(mode)

    @keyword("Get Acquisition Mode")
    def get_acquisition_mode(self, alias: str | None = None) -> str:
        return self._session(alias).get_acquisition_mode().value

    @keyword("Get Acquisition Count")
    def get_acquisition_count(self, alias: str | None = None) -> int:
        return self._session(alias).get_acquisition_count()

    # ------------------------------------------------------------------
    # Calibration (task §6 item 2, §8)
    # ------------------------------------------------------------------
    @keyword("Run Internal Calibration")
    def run_internal_calibration(self, alias: str | None = None) -> None:
        """Takes the instrument offline for the duration. Never runs automatically."""

        self._session(alias).run_internal_calibration()

    @keyword("Get Calibration Status")
    def get_calibration_status(self, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_calibration_status())

    @keyword("Get Calibration Results")
    def get_calibration_results(self, alias: str | None = None) -> str:
        return self._session(alias).get_calibration_results()

    # ------------------------------------------------------------------
    # Measurement (task §6 item 4, §9)
    # ------------------------------------------------------------------
    @keyword("Get Immediate Measurement")
    def get_immediate_measurement(
        self, measurement_type: str, channel: int, alias: str | None = None
    ) -> float:
        """Raises rather than returning a fabricated/clipped value for an overloaded reading."""

        return self._session(alias).get_immediate_measurement(measurement_type, channel)

    @keyword("Measurement Should Be Within")
    def measurement_should_be_within(
        self,
        measurement_type: str,
        channel: int,
        minimum: float,
        maximum: float,
        alias: str | None = None,
    ) -> float:
        minimum, maximum = float(minimum), float(maximum)
        if minimum > maximum:
            raise Tbs1000cValidationError(f"minimum {minimum} must not be greater than maximum {maximum}")
        value = self.get_immediate_measurement(measurement_type, channel, alias)
        if not minimum <= value <= maximum:
            raise AssertionError(
                f"{measurement_type} on CH{channel} was {value:g}, expected between "
                f"{minimum:g} and {maximum:g}"
            )
        _rf_logger.info(f"{measurement_type} on CH{channel} = {value:g}, within [{minimum:g}, {maximum:g}]")
        return value

    # ------------------------------------------------------------------
    # Waveform (task §9) — the primary, host-side path
    # ------------------------------------------------------------------
    @keyword("Get Waveform")
    def get_waveform(self, channel: int, alias: str | None = None) -> dict[str, Any]:
        """Returns decoded time_s/volts arrays plus the full preamble that produced them."""

        return _robot_value(self._session(alias).get_waveform(channel))

    # ------------------------------------------------------------------
    # File transfer: screen image, waveform export, setup save/restore (task §10)
    # ------------------------------------------------------------------
    @keyword("Save Screen Image")
    def save_screen_image(
        self,
        path: str,
        image_format: str | None = None,
        layout: str | None = None,
        alias: str | None = None,
    ) -> None:
        """Saves the current display to a host file. A live acquisition means a live view,
        not a frozen record — call 'Stop Acquisition' first if you need a specific trace."""

        self._session(alias).save_screen_image(Path(path), image_format, layout)

    @keyword("Save Waveform To CSV")
    def save_waveform_to_csv(self, path: str, channel: int, alias: str | None = None) -> None:
        """Primary implementation: host-side decode of 'Get Waveform'. No instrument storage."""

        self._session(alias).save_waveform_to_csv(Path(path), channel)

    @keyword("Save Waveform To CSV On Instrument")
    def save_waveform_to_csv_on_instrument(
        self, path: str, channel: int, alias: str | None = None
    ) -> None:
        """Vendor-native alternate via SAVe:WAVEform, for cross-checking the driver's own CSV."""

        self._session(alias).save_waveform_to_csv_on_instrument(Path(path), channel)

    @keyword("Save Waveform To Reference Memory")
    def save_waveform_to_reference_memory(self, channel: int, ref: int, alias: str | None = None) -> None:
        """Instrument-side SAVe:WAVEform CH<x>,REF<y> — no host file transfer (Gate 3)."""

        self._session(alias).save_waveform_to_reference_memory(int(channel), int(ref))

    @keyword("Recall Waveform From Host File")
    def recall_waveform_from_host_file(self, path: str, ref: int, alias: str | None = None) -> None:
        """Uploads a host file to the instrument and loads it into reference memory,
        the round-trip counterpart to 'Save Waveform To CSV On Instrument' (Gate 3)."""

        self._session(alias).recall_waveform_from_host_file(Path(path), int(ref))

    @keyword("Save Setup")
    def save_setup(self, path: str, alias: str | None = None) -> None:
        """Primary implementation: *LRN? written verbatim to a host file. No instrument file."""

        self._session(alias).save_setup(Path(path))

    @keyword("Restore Setup")
    def restore_setup(self, path: str, alias: str | None = None) -> None:
        """Resends a *LRN?-captured setup string; verified via the instrument's event queue."""

        self._session(alias).restore_setup(Path(path))

    @keyword("Save Setup To Instrument Memory")
    def save_setup_to_instrument_memory(self, slot: int, alias: str | None = None) -> None:
        self._session(alias).save_setup_to_instrument_memory(slot)

    @keyword("Restore Setup From Instrument Memory")
    def restore_setup_from_instrument_memory(self, slot: int, alias: str | None = None) -> None:
        self._session(alias).restore_setup_from_instrument_memory(slot)

    @keyword("Restore Factory Setup")
    def restore_factory_setup(self, alias: str | None = None) -> None:
        self._session(alias).restore_factory_setup()

    # ------------------------------------------------------------------
    # Raw SCPI escape hatch (task §11)
    # ------------------------------------------------------------------
    @keyword("Enable Raw SCPI")
    def enable_raw_scpi(self, confirmation: str, alias: str | None = None) -> None:
        self._session(alias).enable_raw_scpi(confirmation)

    @keyword("Raw SCPI Query")
    def raw_scpi_query(self, command: str, alias: str | None = None) -> str:
        """Bypasses typed validation and waveform-preamble consistency checks."""

        return self._session(alias).raw_query(command)

    @keyword("Raw SCPI Write")
    def raw_scpi_write(self, command: str, alias: str | None = None) -> None:
        """Bypasses typed validation and waveform-preamble consistency checks."""

        self._session(alias).raw_write(command)

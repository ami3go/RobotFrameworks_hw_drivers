"""Robot Framework adapter for :mod:`picoscope2000a`.

Keeps backend selection, capture, decode, CSV/image rendering, and
validation entirely in the core driver — this module only converts
arguments/results and manages named sessions, mirroring the split used by
``rf_tbs1000c``/``rf_phidget_relay``.

Every public keyword is wrapped (see ``_evidenced`` below) with an RFDS-008
evidence operation record. See ``evidence.py``. Pass
``evidence_enabled=${FALSE}`` to the ``Library`` import to disable it.
"""

from __future__ import annotations

import functools
import inspect
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from . import evidence as _evidence

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


from picoscope2000a import PicoScope2000A
from picoscope2000a.exceptions import PicoScope2000AConnectionError, PicoScope2000AValidationError


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
    raise PicoScope2000AValidationError(f"{name} must be a Boolean, got {value!r}")


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


def _evidenced(func):
    """Wrap a keyword method with an RFDS-008 evidence operation record.

    Session alias is taken from the bound ``alias`` argument when present,
    else the library's current active alias, else ``"default"``. Must sit
    *below* ``@keyword(...)`` in the decorator stack (closest to ``def``).
    """
    signature = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(self: PicoScope2000ALibrary, *args: Any, **kwargs: Any):
        capability = getattr(wrapper, "robot_name", None) or func.__name__.replace("_", " ").title()
        run = self._ensure_evidence()
        bound = signature.bind_partial(self, *args, **kwargs)
        bound.apply_defaults()
        arguments = {key: value for key, value in bound.arguments.items() if key != "self"}
        session_alias = arguments.get("alias") or self._active_alias or "default"
        with run.record_operation(capability, arguments=arguments, session_alias=session_alias) as op:
            result = func(self, *args, **kwargs)
            op.set_result(_robot_value(result))
            return result

    return wrapper


@library(scope="SUITE", version="26.1", auto_keywords=False)
class PicoScope2000ALibrary:
    """Robot Framework keywords for the PicoScope 2000A-family (ps2000a) oscilloscopes.

    The RFDS-002 canonical connection keywords (``Connect``, ``Disconnect``,
    ``Is Connected``, ``Get Connection State``, ``Check Communication``,
    ``Get Identity``) are the primary, documented connection API. No
    hardware is touched on library import.
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = "26.1"

    def __init__(self, evidence_enabled: Any = True) -> None:
        self._sessions: dict[str, PicoScope2000A] = {}
        self._active_alias: str | None = None
        self._evidence_enabled = _as_bool(evidence_enabled, "evidence_enabled")
        self._evidence: Any | None = None
        self.ROBOT_LIBRARY_LISTENER = self

    def _ensure_evidence(self) -> Any:
        """Lazily create (or return) this library instance's :class:`evidence.EvidenceRun`.

        One evidence run covers the whole library instance's lifetime, since
        this driver supports multiple simultaneous aliased sessions with no
        single "disconnect everything" keyword. Finalized from
        ``_end_suite`` (Robot's own suite-end listener hook), or explicitly
        via ``EvidenceRun.finalize()``/``Export Diagnostic Bundle`` outside
        Robot Framework.
        """
        if self._evidence is None:
            if self._evidence_enabled:
                self._evidence = _evidence.EvidenceRun(driver_id="rf_picoscope2000a", activity="session")
            else:
                self._evidence = _evidence.NullEvidenceRun()
        return self._evidence

    # Robot listener hook: best-effort cleanup at suite end.
    def _end_suite(self, name: str, attributes: dict[str, Any]) -> None:
        del name, attributes
        for alias in list(self._sessions):
            try:
                self._sessions[alias].close()
            except Exception as exc:  # noqa: BLE001 - cleanup must not hide an earlier suite failure
                _rf_logger.warn(f"PicoScope2000A: cleanup for {alias!r} reported: {exc}")  # noqa: G010
        self._sessions.clear()
        self._active_alias = None
        if self._evidence is not None:
            self._evidence.finalize(status="PASS")
            self._evidence = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_alias(self, alias: str | None) -> str | None:
        return str(alias) if alias not in (None, "") else self._active_alias

    def _session(self, alias: str | None = None) -> PicoScope2000A:
        selected = self._resolve_alias(alias)
        if selected is None:
            raise PicoScope2000AConnectionError("no PicoScope2000A connection is active; call 'Connect' first")
        try:
            return self._sessions[selected]
        except KeyError as exc:
            known = ", ".join(sorted(self._sessions)) or "none"
            raise PicoScope2000AConnectionError(
                f"unknown PicoScope2000A alias {selected!r}; known aliases: {known}"
            ) from exc

    def _connection_state(self, alias: str, driver: PicoScope2000A) -> dict[str, Any]:
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
            "transport": type(driver.backend).__name__,
            "identity": identity_str,
            "timeout_s": None,
            "state": "connected",
        }

    # ------------------------------------------------------------------
    # RFDS-002 canonical connection keywords
    # ------------------------------------------------------------------
    @keyword("Connect")
    @_evidenced
    def connect(self, resource: str | None = None, alias: str = "default", **options: Any) -> dict[str, Any]:
        """Connect to a PicoScope over USB, or the bundled simulator with ``simulated=True``.

        ``resource`` is the device serial; omit it (on either real or
        simulated hardware) to autodetect the single connected device — this
        raises if zero or more than one are found. Idempotent when ``alias``
        is already connected to the same ``resource``.
        """

        selected_alias = str(alias).strip() or "default"
        if selected_alias in self._sessions:
            existing = self._sessions[selected_alias]
            if resource and existing.connected and str(existing.resource) != str(resource):
                raise PicoScope2000AConnectionError(
                    f"alias {selected_alias!r} is already connected to {existing.resource!r}; "
                    f"disconnect it before connecting it to {resource!r}."
                )
            self._active_alias = selected_alias
            return self._connection_state(selected_alias, existing)

        simulated = _as_bool(options.pop("simulated", False), "simulated")
        driver = (
            PicoScope2000A.connect_simulated(resource) if simulated else PicoScope2000A.connect(resource)
        )
        evidence_run = self._ensure_evidence()
        evidence_run.note_execution_mode("SIMULATOR" if simulated else "REAL_HARDWARE")
        self._sessions[selected_alias] = driver
        self._active_alias = selected_alias
        _rf_logger.info(f"PicoScope2000A: connected alias={selected_alias!r} resource={driver.resource!r}")
        state = self._connection_state(selected_alias, driver)
        evidence_run.record_device_identity(
            session_alias=selected_alias,
            manufacturer="Pico Technology",
            model_family="PicoScope 2000A",
            resource=state.get("resource"),
            identity=state.get("identity"),
            simulated=simulated,
        )
        return state

    @keyword("Disconnect")
    @_evidenced
    def disconnect(self, alias: str | None = None) -> None:
        """Idempotent: succeeds even if already disconnected."""

        selected = self._resolve_alias(alias)
        if selected is None or selected not in self._sessions:
            return
        self._sessions.pop(selected).close()
        if self._active_alias == selected:
            self._active_alias = next(iter(self._sessions), None)

    @keyword("Is Connected")
    @_evidenced
    def is_connected(self, alias: str | None = None) -> bool:
        selected = self._resolve_alias(alias)
        if selected is None or selected not in self._sessions:
            return False
        return self._sessions[selected].connected

    @keyword("Get Connection State")
    @_evidenced
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
    @_evidenced
    def check_communication(self, alias: str | None = None) -> bool:
        return self._session(alias).check_communication()

    @keyword("Get Identity")
    @_evidenced
    def get_identity(self, alias: str | None = None, refresh: bool = True) -> str:
        return self._session(alias).identify(refresh=_as_bool(refresh, "refresh")).raw

    @keyword("Find Devices")
    @_evidenced
    def find_devices(self, simulated: bool = False, alias: str | None = None) -> list[str]:
        """Lists connected device serials without opening any of them.

        Uses the already-connected session named by ``alias`` if one exists
        (any real or simulated session can enumerate); otherwise opens a
        throwaway backend just to enumerate — pass ``simulated=${TRUE}`` to
        probe the bundled simulator instead of real hardware in that case.
        """

        selected = self._resolve_alias(alias)
        if selected is not None and selected in self._sessions:
            return self._sessions[selected].enumerate_devices()
        from picoscope2000a.backend import RealPs2000aBackend
        from picoscope2000a.simulator import SimulatedBackend

        backend = SimulatedBackend() if _as_bool(simulated, "simulated") else RealPs2000aBackend()
        return backend.enumerate_devices()

    @keyword("Switch Oscilloscope")
    @_evidenced
    def switch_oscilloscope(self, alias: str) -> str:
        self._session(alias)
        self._active_alias = str(alias)
        return self._active_alias

    @keyword("Get Active Oscilloscope")
    @_evidenced
    def get_active_oscilloscope(self) -> str | None:
        return self._active_alias

    @keyword("List Oscilloscope Connections")
    @_evidenced
    def list_oscilloscope_connections(self) -> list[str]:
        return sorted(self._sessions)

    # ------------------------------------------------------------------
    # Channel configuration
    # ------------------------------------------------------------------
    @keyword("Set Channel Enabled")
    @_evidenced
    def set_channel_enabled(self, channel: str, enabled: bool, alias: str | None = None) -> None:
        self._session(alias).set_channel_enabled(channel, _as_bool(enabled, "enabled"))

    @keyword("Get Channel Enabled")
    @_evidenced
    def get_channel_enabled(self, channel: str, alias: str | None = None) -> bool:
        return self._session(alias).get_channel_enabled(channel)

    @keyword("Set Channel Range")
    @_evidenced
    def set_channel_range(self, channel: str, range_v: float, alias: str | None = None) -> float:
        return self._session(alias).set_channel_range(channel, float(range_v))

    @keyword("Get Channel Range")
    @_evidenced
    def get_channel_range(self, channel: str, alias: str | None = None) -> float:
        return self._session(alias).get_channel_range(channel)

    @keyword("Set Channel Coupling")
    @_evidenced
    def set_channel_coupling(self, channel: str, coupling: str, alias: str | None = None) -> None:
        self._session(alias).set_channel_coupling(channel, coupling)

    @keyword("Get Channel Coupling")
    @_evidenced
    def get_channel_coupling(self, channel: str, alias: str | None = None) -> str:
        return self._session(alias).get_channel_coupling(channel)

    @keyword("Set Channel Offset")
    @_evidenced
    def set_channel_offset(self, channel: str, offset_v: float, alias: str | None = None) -> None:
        self._session(alias).set_channel_offset(channel, float(offset_v))

    @keyword("Get Channel Offset")
    @_evidenced
    def get_channel_offset(self, channel: str, alias: str | None = None) -> float:
        return self._session(alias).get_channel_offset(channel)

    @keyword("Set Channel Probe")
    @_evidenced
    def set_channel_probe(
        self, channel: str, probe_type: str, scale: float = 1.0, alias: str | None = None
    ) -> None:
        """``probe_type`` is ``VOLTAGE`` or ``CURRENT``. ``scale`` is native units per
        volt at the ADC input — e.g. a 100 mV/A current clamp uses ``scale=10``,
        after which ``Get Waveform`` on this channel reports amps, not volts."""

        self._session(alias).set_channel_probe(channel, probe_type, float(scale))

    @keyword("Get Channel Probe")
    @_evidenced
    def get_channel_probe(self, channel: str, alias: str | None = None) -> dict[str, Any]:
        return self._session(alias).get_channel_probe(channel)

    @keyword("Get Channel Settings")
    @_evidenced
    def get_channel_settings(self, channel: str, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_channel_settings(channel))

    @keyword("Get Enabled Channels")
    @_evidenced
    def get_enabled_channels(self, alias: str | None = None) -> list[str]:
        return self._session(alias).get_enabled_channels()

    # ------------------------------------------------------------------
    # Timebase (main time settings)
    # ------------------------------------------------------------------
    @keyword("Set Timebase")
    @_evidenced
    def set_timebase(
        self,
        sample_interval_s: float,
        num_samples: int,
        pre_trigger_ratio: float = 0.0,
        alias: str | None = None,
    ) -> dict[str, Any]:
        return _robot_value(
            self._session(alias).set_timebase(
                float(sample_interval_s), int(num_samples), float(pre_trigger_ratio)
            )
        )

    @keyword("Get Timebase Settings")
    @_evidenced
    def get_timebase_settings(self, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_timebase_settings())

    # ------------------------------------------------------------------
    # Trigger
    # ------------------------------------------------------------------
    @keyword("Set Trigger")
    @_evidenced
    def set_trigger(
        self,
        channel: str,
        threshold_v: float,
        direction: str = "RISING",
        delay_samples: int = 0,
        auto_trigger_ms: int = 0,
        alias: str | None = None,
    ) -> None:
        self._session(alias).set_trigger(
            channel, float(threshold_v), direction, int(delay_samples), int(auto_trigger_ms)
        )

    @keyword("Disable Trigger")
    @_evidenced
    def disable_trigger(self, alias: str | None = None) -> None:
        self._session(alias).disable_trigger()

    @keyword("Get Trigger Settings")
    @_evidenced
    def get_trigger_settings(self, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_trigger_settings())

    # ------------------------------------------------------------------
    # Block capture + waveform retrieval
    # ------------------------------------------------------------------
    @keyword("Capture Block")
    @_evidenced
    def capture_block(self, timeout_s: float | None = None, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(
            self._session(alias).capture_block(float(timeout_s) if timeout_s is not None else None)
        )

    @keyword("Get Waveform")
    @_evidenced
    def get_waveform(self, channel: str, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_waveform(channel))

    @keyword("Get All Waveforms")
    @_evidenced
    def get_all_waveforms(self, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_all_waveforms())

    # ------------------------------------------------------------------
    # Standard measurements
    # ------------------------------------------------------------------
    @keyword("Get Measurements")
    @_evidenced
    def get_measurements(self, channel: str, alias: str | None = None) -> dict[str, Any]:
        """Every standard measurement (amplitude, peak-to-peak, frequency, period,
        rise/fall time, duty cycle, overshoot, etc.) for this channel's last capture at once.

        Computed host-side from the decoded waveform — ``picosdk`` has no on-device
        measurement call. See the package README for the full list and algorithms."""

        return _robot_value(self._session(alias).get_measurements(channel))

    @keyword("Get Measurement")
    @_evidenced
    def get_measurement(self, channel: str, measurement_type: str, alias: str | None = None) -> float:
        """One named measurement, e.g. ``AMPLITUDE``, ``PK2Pk``, ``FREQUENCY``, ``RMS``,
        ``RISe``, ``PDUty``. Raises if it can't be determined from this capture (e.g. too
        few cycles captured for frequency/period/edge-timing measurements)."""

        return self._session(alias).get_measurement(channel, measurement_type)

    @keyword("Measurement Should Be Within")
    @_evidenced
    def measurement_should_be_within(
        self,
        channel: str,
        measurement_type: str,
        minimum: float,
        maximum: float,
        alias: str | None = None,
    ) -> float:
        return self._session(alias).measurement_should_be_within(
            channel, measurement_type, float(minimum), float(maximum)
        )

    # ------------------------------------------------------------------
    # Cross-channel timing measurements
    # ------------------------------------------------------------------
    @keyword("Get Channel Delay")
    @_evidenced
    def get_channel_delay(
        self,
        reference_channel: str,
        target_channel: str,
        edge: str = "RISING",
        alias: str | None = None,
    ) -> float:
        """Time (seconds) from ``reference_channel``'s first qualifying edge to the
        nearest corresponding edge on ``target_channel``. Positive means
        ``target_channel`` lags; negative means it leads. Both channels must have been
        enabled and captured together in the last ``Capture Block`` call — they then
        share one sample clock, so the delay is directly meaningful."""

        return self._session(alias).get_channel_delay(reference_channel, target_channel, edge)

    @keyword("Get Channel Phase")
    @_evidenced
    def get_channel_phase(
        self,
        reference_channel: str,
        target_channel: str,
        edge: str = "RISING",
        alias: str | None = None,
    ) -> float:
        """Phase of ``target_channel`` relative to ``reference_channel``, in degrees,
        using ``reference_channel``'s own measured period as the 360-degree reference."""

        return self._session(alias).get_channel_phase(reference_channel, target_channel, edge)

    @keyword("Channel Delay Should Be Within")
    @_evidenced
    def channel_delay_should_be_within(
        self,
        reference_channel: str,
        target_channel: str,
        minimum: float,
        maximum: float,
        edge: str = "RISING",
        alias: str | None = None,
    ) -> float:
        return self._session(alias).channel_delay_should_be_within(
            reference_channel, target_channel, float(minimum), float(maximum), edge
        )

    @keyword("Channel Phase Should Be Within")
    @_evidenced
    def channel_phase_should_be_within(
        self,
        reference_channel: str,
        target_channel: str,
        minimum: float,
        maximum: float,
        edge: str = "RISING",
        alias: str | None = None,
    ) -> float:
        return self._session(alias).channel_phase_should_be_within(
            reference_channel, target_channel, float(minimum), float(maximum), edge
        )

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------
    @keyword("Save Waveform To CSV")
    @_evidenced
    def save_waveform_to_csv(self, path: str, channel: str, alias: str | None = None) -> None:
        self._session(alias).save_waveform_to_csv(path, channel)

    @keyword("Save All Waveforms To CSV")
    @_evidenced
    def save_all_waveforms_to_csv(self, path: str, alias: str | None = None) -> None:
        self._session(alias).save_all_waveforms_to_csv(path)

    # ------------------------------------------------------------------
    # Image export
    # ------------------------------------------------------------------
    @keyword("Save Channel Image")
    @_evidenced
    def save_channel_image(
        self, path: str, channel: str, title: str | None = None, alias: str | None = None
    ) -> None:
        """These units have no display to screenshot: renders the decoded ``Get
        Waveform`` data with matplotlib. Requires the ``rf_picoscope2000a[plot]`` extra."""

        self._session(alias).save_channel_image(path, channel, title)

    @keyword("Save All Channels Image")
    @_evidenced
    def save_all_channels_image(self, path: str, title: str | None = None, alias: str | None = None) -> None:
        self._session(alias).save_all_channels_image(path, title)

    # ------------------------------------------------------------------
    # AWG (built-in signal generator)
    # ------------------------------------------------------------------
    @keyword("Set AWG Waveform")
    @_evidenced
    def set_awg_waveform(
        self,
        wave_type: str,
        frequency_hz: float,
        peak_to_peak_v: float,
        offset_v: float = 0.0,
        alias: str | None = None,
    ) -> None:
        """Raises if the connected model has no built-in AWG (not every 2000-series
        unit does — see the package README for the supported model list)."""

        self._session(alias).set_awg_waveform(
            wave_type, float(frequency_hz), float(peak_to_peak_v), float(offset_v)
        )

    @keyword("Stop AWG")
    @_evidenced
    def stop_awg(self, alias: str | None = None) -> None:
        self._session(alias).stop_awg()

    @keyword("Get AWG Settings")
    @_evidenced
    def get_awg_settings(self, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_awg_settings())

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------
    @keyword("Save Preset")
    @_evidenced
    def save_preset(self, path: str, alias: str | None = None) -> None:
        self._session(alias).save_preset(path)

    @keyword("Load Preset")
    @_evidenced
    def load_preset(self, path: str, alias: str | None = None) -> None:
        self._session(alias).load_preset(path)

    # ------------------------------------------------------------------
    # RFDS-008 evidence
    # ------------------------------------------------------------------
    @keyword("Export Diagnostic Bundle")
    @_evidenced
    def export_diagnostic_bundle(self, destination: str | None = None) -> str | None:
        """Zip this library instance's current RFDS-008 evidence run for troubleshooting.

        Works whether or not any session is connected, and does not finalize
        the run. Returns the archive path, or ``None`` if
        ``evidence_enabled=False`` was passed to this library instance.
        """
        run = self._ensure_evidence()
        return run.export_diagnostic_bundle(None if destination in (None, "") else str(destination))

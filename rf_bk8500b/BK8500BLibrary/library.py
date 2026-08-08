"""Robot Framework keyword library for B&K Precision 8500B electronic loads.

Every public keyword is wrapped (see ``_evidenced`` below) with an RFDS-008
evidence operation record, and the default device factory wires an
``EvidenceAuditSink``/``EvidenceMetricsSink``/``TracingTransport`` into every
connected device so the existing ``CommandExecutor`` audit seam and the raw
serial bytes both flow into the same evidence run. See ``bk8500b/evidence.py``
and ``docs/logging_and_evidence.md`` for what gets recorded. Pass
``evidence_enabled=False`` to disable it (errors still reach the standard
Python logger and Robot's own log either way).
"""
from __future__ import annotations

import csv
import functools
import inspect
import json
import math
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from robot.api import logger
from robot.api.deco import keyword, library, not_keyword

from bk8500b import (
    BK8500B,
    BK8500BError,
    DriverConfig,
    DynamicMode,
    OperatingMode,
    Protocol,
    ReconnectPolicy,
    SafeEnableConfig,
    SafetyPolicy,
    SafetyToken,
    SessionState,
    TransientConfig,
)
from bk8500b import evidence as _evidence
from bk8500b.transport import SerialTransport

from .conversion import as_bool, as_float, as_int, to_robot


class BK8500BRobotError(RuntimeError):
    """Raised when a driver error is translated for Robot Framework output."""


def _evidenced(func: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a keyword method with an RFDS-008 evidence operation record.

    Applied uniformly to every ``@keyword`` method (not only the ones that
    happen to route through ``_translate``), so keyword-level evidence
    coverage does not depend on auditing every method body. Must sit *below*
    ``@keyword(...)`` in the decorator stack — see the ``rf_phidget_relay``
    reference implementation this was adapted from for why reading
    ``wrapper.robot_name`` via closure at call time (not decoration time)
    is required.
    """
    signature = inspect.signature(func)

    _DISCONNECT_CAPABILITIES = {"Disconnect Electronic Load", "Disconnect All Electronic Loads", "Disconnect"}

    @functools.wraps(func)
    def wrapper(self: BK8500BLibrary, *args: Any, **kwargs: Any) -> Any:
        capability = getattr(wrapper, "robot_name", None) or func.__name__.replace("_", " ").title()
        run = self._ensure_evidence()
        bound = signature.bind_partial(self, *args, **kwargs)
        bound.apply_defaults()
        arguments = {key: value for key, value in bound.arguments.items() if key != "self"}
        session_alias = arguments.get("alias") or self._active_alias
        status = "PASS"
        try:
            with run.record_operation(capability, arguments=arguments, session_alias=session_alias) as op:
                result = func(self, *args, **kwargs)
                op.set_result(result)
            return result
        except Exception:
            status = "FAIL"
            raise
        finally:
            # One evidence run per library instance, not per alias (see
            # _ensure_evidence) — only finalize once every alias is
            # disconnected, so disconnecting one of several instruments does
            # not prematurely close a still-active multi-alias evidence run.
            if capability in _DISCONNECT_CAPABILITIES and self._evidence is not None and not self._devices:
                self._evidence.finalize(status=status)
                self._evidence = None

    return wrapper


@library(scope="SUITE", version="26.05", converters={bool: as_bool})
class BK8500BLibrary:
    """Control B&K Precision 8500B Series DC electronic loads.

    The library is an adapter over the bundled :mod:`bk8500b` Python driver. It supports
    multiple instruments by alias and returns Robot-friendly dictionaries for structured
    driver results.

    Typical use::

        *** Settings ***
        Library    BK8500BLibrary
        Suite Setup       Connect To Electronic Load    COM5
        Suite Teardown    Disconnect All Electronic Loads

        *** Test Cases ***
        Sink One Ampere
            Configure And Enable Load    CC    1.0    current_limit=1.2
            ${voltage}=    Measure Voltage
            Voltage Should Be Within Range    11.5    12.5
            Disable Input

    Safety notes:

    - Input is turned off during disconnect by default.
    - Reconfiguration while input is on is blocked by the underlying driver policy.
    - Short-circuit mode is disabled unless explicitly allowed when connecting.
    - Enabling short-circuit mode additionally requires the confirmation text
      ``I UNDERSTAND``.
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = "26.05"

    def __init__(
        self,
        default_port: str | None = None,
        default_alias: str = "default",
        auto_connect: bool = False,
        evidence_enabled: bool = True,
    ) -> None:
        self.default_port = default_port
        self.default_alias = str(default_alias)
        self._devices: dict[str, BK8500B] = {}
        self._active_alias: str | None = None
        self._device_factory: Callable[..., BK8500B] = self._default_device_factory
        self._evidence_enabled = as_bool(evidence_enabled, name="evidence_enabled")
        self._evidence: _evidence.EvidenceRun | _evidence.NullEvidenceRun | None = None
        self._pending_connect_alias: str | None = None
        self.ROBOT_LIBRARY_LISTENER = self
        if as_bool(auto_connect, name="auto_connect"):
            if not default_port:
                raise ValueError("default_port is required when auto_connect is enabled")
            self.connect_to_electronic_load(default_port, alias=self.default_alias)

    @not_keyword
    def _ensure_evidence(self) -> _evidence.EvidenceRun | _evidence.NullEvidenceRun:
        """Lazily create (or return) this library instance's evidence run.

        One evidence run per ``BK8500BLibrary`` instance (matching its
        ``SUITE`` scope), not one per alias — individual events/operations are
        still tagged with the resolved ``session_alias`` so a multi-alias
        suite's evidence remains attributable per instrument.
        """
        if self._evidence is None:
            if self._evidence_enabled:
                self._evidence = _evidence.EvidenceRun(driver_id="rf_bk8500b", activity="session")
            else:
                self._evidence = _evidence.NullEvidenceRun()
        return self._evidence

    @not_keyword
    def _default_device_factory(self, config: DriverConfig) -> BK8500B:
        """Default ``_device_factory``: wires evidence recording into a real serial device.

        Tests and callers that assign their own ``library._device_factory =
        factory`` (a single-argument ``factory(config)`` callable, as this
        library has always supported) bypass this method entirely and get no
        protocol-level tracing — that's correct, since a fake transport has no
        real wire bytes to trace; those keyword calls are still covered by the
        ``_evidenced`` operation-level recording regardless of which factory
        built the device.
        """
        run = self._ensure_evidence()
        alias = self._pending_connect_alias
        transport = _evidence.TracingTransport(SerialTransport(config), run, session_alias=alias)
        audit_sink = _evidence.EvidenceAuditSink(run, session_alias=alias)
        metrics_sink = _evidence.EvidenceMetricsSink(run, session_alias=alias)
        return BK8500B(config, transport=transport, audit_sink=audit_sink, metrics_sink=metrics_sink)

    @keyword("Export Diagnostic Bundle")
    @_evidenced
    def export_diagnostic_bundle(self, destination: str | None = None) -> str | None:
        """Zip this session's RFDS-008 evidence run to ``destination`` for troubleshooting.

        Works whether or not any load is currently connected, and does not
        finalize the run — disconnecting (any of the ``Disconnect*``
        keywords) remains the point at which ``run_summary.json``/
        ``evidence_manifest.json`` are written for the last time. Returns the
        archive path, or ``None`` if ``evidence_enabled=False`` was passed to
        this library instance.
        """
        run = self._ensure_evidence()
        return run.export_diagnostic_bundle(None if destination in (None, "") else str(destination))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @not_keyword
    def _end_suite(self, data: Any, result: Any) -> None:  # Robot listener API v3
        del data, result
        self._cleanup_all()
        if self._evidence is not None:
            # Safety-net finalization: normal finalization happens in the
            # Disconnect* keywords below; this only does anything if a suite
            # ended without an explicit disconnect (e.g. a crash), so evidence
            # is never silently lost (RFDS-008 §6.7 finite finalization).
            self._evidence.finalize(status="ABORTED")

    @not_keyword
    def _cleanup_all(self) -> None:
        for alias, device in list(self._devices.items()):
            try:
                device.close()
            except Exception as exc:  # cleanup must not hide an earlier suite failure
                logger.warn(f"Failed to close electronic load {alias!r}: {exc}")
        self._devices.clear()
        self._active_alias = None

    @not_keyword
    def _translate(self, action: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except BK8500BError as exc:
            context = getattr(exc, "context", None)
            suffix = f"; context={dict(context)!r}" if context else ""
            raise BK8500BRobotError(
                f"{action} failed: {type(exc).__name__}: {exc}{suffix}"
            ) from exc

    _PUBLIC_STATE = {
        SessionState.DISCONNECTED: "disconnected",
        SessionState.CONNECTING: "connecting",
        SessionState.IDENTIFYING: "connecting",
        SessionState.CONNECTED_UNSYNCHRONIZED: "connected",
        SessionState.CONNECTED_READY: "connected",
        SessionState.DEGRADED: "degraded",
        SessionState.RECONNECTING: "recovering",
        SessionState.CLOSING: "disconnected",
        SessionState.FAILED: "faulted",
    }

    @not_keyword
    def _connection_state(self, alias: str, device: BK8500B) -> dict[str, Any]:
        """Build the RFDS-002 Section 12.1 normalized connection-state dictionary."""
        identity_str: str | None = None
        if device.connected:
            try:
                identity_str = str(to_robot(device.identify()).get("raw") or None)
            except Exception:
                identity_str = None
        return {
            "alias": alias,
            "resource": device.config.port,
            "connected": bool(device.connected),
            "communication_ok": bool(device.connected),
            "transport": to_robot(device.config.protocol),
            "identity": identity_str,
            "timeout_s": device.config.query_timeout_s,
            "state": self._PUBLIC_STATE.get(device.session_state, "faulted"),
        }

    @not_keyword
    def _device(self, alias: str | None = None) -> BK8500B:
        selected = str(alias) if alias not in (None, "") else self._active_alias
        if selected is None:
            raise BK8500BRobotError("No active electronic load. Connect to an instrument first.")
        try:
            return self._devices[selected]
        except KeyError as exc:
            known = ", ".join(sorted(self._devices)) or "none"
            raise BK8500BRobotError(
                f"Unknown electronic load alias {selected!r}. Known aliases: {known}."
            ) from exc

    @not_keyword
    def _mode(self, value: Any) -> OperatingMode:
        if isinstance(value, OperatingMode):
            return value
        token = str(value).strip().lower().replace("_", "").replace("-", "")
        aliases = {
            "cc": OperatingMode.CURRENT,
            "current": OperatingMode.CURRENT,
            "curr": OperatingMode.CURRENT,
            "cv": OperatingMode.VOLTAGE,
            "voltage": OperatingMode.VOLTAGE,
            "volt": OperatingMode.VOLTAGE,
            "cp": OperatingMode.POWER,
            "cw": OperatingMode.POWER,
            "power": OperatingMode.POWER,
            "cr": OperatingMode.RESISTANCE,
            "resistance": OperatingMode.RESISTANCE,
            "res": OperatingMode.RESISTANCE,
            "dynamic": OperatingMode.DYNAMIC,
            "dyn": OperatingMode.DYNAMIC,
            "led": OperatingMode.LED,
            "impedance": OperatingMode.IMPEDANCE,
            "imp": OperatingMode.IMPEDANCE,
        }
        try:
            return aliases[token]
        except KeyError as exc:
            raise ValueError(
                f"Unknown operating mode {value!r}. Use CC, CV, CP, CR, dynamic, LED, or impedance."
            ) from exc

    @not_keyword
    def _dynamic_mode(self, value: Any) -> DynamicMode:
        if isinstance(value, DynamicMode):
            return value
        token = str(value).strip().lower()
        aliases = {
            "continuous": DynamicMode.CONTINUOUS,
            "cont": DynamicMode.CONTINUOUS,
            "pulse": DynamicMode.PULSE,
            "toggle": DynamicMode.TOGGLE,
        }
        try:
            return aliases[token]
        except KeyError as exc:
            raise ValueError("Dynamic mode must be continuous, pulse, or toggle") from exc

    @not_keyword
    def _measurement(self, kind: str, alias: str | None = None) -> float:
        device = self._device(alias)
        methods = {
            "voltage": device.measure_voltage,
            "current": device.measure_current,
            "power": device.measure_power,
            "resistance": device.measure_resistance,
        }
        return float(self._translate(f"Measure {kind}", methods[kind]).value)

    @not_keyword
    def _assert_range(self, name: str, actual: float, minimum: Any, maximum: Any) -> None:
        low = as_float(minimum, name="minimum")
        high = as_float(maximum, name="maximum")
        if low > high:
            raise ValueError(f"minimum {low} must not be greater than maximum {high}")
        if not low <= actual <= high:
            raise AssertionError(f"{name} {actual:g} is outside allowed range [{low:g}, {high:g}]")
        logger.info(f"{name} {actual:g} is within [{low:g}, {high:g}]")

    # ------------------------------------------------------------------
    # Connections and sessions
    # ------------------------------------------------------------------
    @keyword("Connect To Electronic Load")
    @_evidenced
    def connect_to_electronic_load(
        self,
        port: str | None = None,
        alias: str = "default",
        protocol: str = "scpi",
        baud_rate: int = 9600,
        address: int = 0,
        read_timeout: float = 2.0,
        write_timeout: float = 2.0,
        query_timeout: float = 2.0,
        verify_writes: bool = True,
        turn_input_off_on_close: bool = True,
        require_enable_token: bool = False,
        allow_short: bool = False,
        reconnect: bool = False,
    ) -> dict[str, Any]:
        """Connect to an electronic load and select it as the active session.

        ``port`` is typically ``COM5`` on Windows or ``/dev/ttyUSB0`` on Linux.
        ``alias`` allows multiple loads to be used in one suite. Existing aliases are
        rejected to prevent accidentally replacing a live connection.
        """
        selected_port = port or self.default_port
        if not selected_port:
            raise ValueError("port is required")
        selected_alias = str(alias).strip()
        if not selected_alias:
            raise ValueError("alias must not be empty")
        if selected_alias in self._devices:
            raise BK8500BRobotError(
                f"Alias {selected_alias!r} already exists. Disconnect it before reconnecting."
            )
        try:
            selected_protocol = Protocol(str(protocol).strip().lower())
        except ValueError as exc:
            raise ValueError("protocol must be scpi, legacy, or auto") from exc
        config = DriverConfig(
            port=str(selected_port),
            protocol=selected_protocol,
            address=as_int(address, name="address"),
            baud_rate=as_int(baud_rate, name="baud_rate"),
            read_timeout_s=as_float(read_timeout, name="read_timeout"),
            write_timeout_s=as_float(write_timeout, name="write_timeout"),
            query_timeout_s=as_float(query_timeout, name="query_timeout"),
            reconnect=ReconnectPolicy(enabled=as_bool(reconnect, name="reconnect")),
            safety=SafetyPolicy(
                verify_critical_writes=as_bool(verify_writes, name="verify_writes"),
                turn_input_off_on_close=as_bool(
                    turn_input_off_on_close, name="turn_input_off_on_close"
                ),
                require_enable_token=as_bool(require_enable_token, name="require_enable_token"),
                allow_short=as_bool(allow_short, name="allow_short"),
            ),
        )
        self._pending_connect_alias = selected_alias
        try:
            device = self._device_factory(config)
        finally:
            self._pending_connect_alias = None
        self._translate("Connect", device.connect)
        self._devices[selected_alias] = device
        self._active_alias = selected_alias
        identity = to_robot(self._translate("Identify", device.identify))
        result = {
            "alias": selected_alias,
            "port": str(selected_port),
            "session_state": device.session_state.value,
            **identity,
        }
        if self._evidence is not None:
            self._evidence.record_device_identity(
                manufacturer="B&K Precision",
                model=identity.get("model"),
                serial_number=identity.get("serial") or identity.get("serial_number"),
                firmware_version=identity.get("firmware") or identity.get("firmware_version"),
                port=str(selected_port),
                protocol=selected_protocol.value,
                alias=selected_alias,
            )
        logger.info(f"Connected {identity['model']} at {selected_port} as {selected_alias!r}")
        return result

    @keyword("Disconnect Electronic Load")
    @_evidenced
    def disconnect_electronic_load(self, alias: str | None = None) -> None:
        """Disconnect one load. The input is turned off first by default."""
        selected = str(alias) if alias not in (None, "") else self._active_alias
        device = self._device(selected)
        self._translate("Disconnect", device.close)
        assert selected is not None
        del self._devices[selected]
        self._active_alias = next(iter(self._devices), None)

    @keyword("Disconnect All Electronic Loads")
    @_evidenced
    def disconnect_all_electronic_loads(self) -> None:
        """Disconnect all known loads, raising the first close error after cleanup."""
        first_error: Exception | None = None
        for alias, device in list(self._devices.items()):
            try:
                self._translate(f"Disconnect {alias}", device.close)
            except Exception as exc:
                if first_error is None:
                    first_error = exc
        self._devices.clear()
        self._active_alias = None
        if first_error is not None:
            raise first_error

    @keyword("Switch Electronic Load")
    @_evidenced
    def switch_electronic_load(self, alias: str) -> str:
        """Select which connected alias subsequent keywords use."""
        self._device(alias)
        self._active_alias = str(alias)
        return self._active_alias

    @keyword("Get Active Electronic Load")
    @_evidenced
    def get_active_electronic_load(self) -> str | None:
        """Return the current alias, or ``None`` when no session exists."""
        return self._active_alias

    @keyword("List Electronic Load Sessions")
    @_evidenced
    def list_electronic_load_sessions(self) -> list[dict[str, Any]]:
        """Return aliases and connection states for all sessions."""
        return [
            {
                "alias": alias,
                "active": alias == self._active_alias,
                "connected": device.connected,
                "session_state": device.session_state.value,
                "port": device.config.port,
            }
            for alias, device in self._devices.items()
        ]

    @keyword("Reconnect Electronic Load")
    @_evidenced
    def reconnect_electronic_load(self, alias: str | None = None) -> None:
        """Run the configured reconnect policy for a connected load."""
        device = self._device(alias)
        self._translate("Reconnect", device.reconnect)

    @keyword("Synchronize Electronic Load State")
    @_evidenced
    def synchronize_electronic_load_state(self, alias: str | None = None) -> dict[str, Any]:
        """Read key state from the instrument and return it as a dictionary."""
        return to_robot(self._translate("Synchronize state", self._device(alias).synchronize_state))

    @keyword("Electronic Load Should Be Connected")
    @_evidenced
    def electronic_load_should_be_connected(self, alias: str | None = None) -> None:
        """Fail unless the selected electronic load is connected."""
        device = self._device(alias)
        if not device.connected:
            raise AssertionError("Electronic load is not connected")

    # ------------------------------------------------------------------
    # RFDS-002 mandatory universal keywords
    #
    # These are thin, idempotent wrappers over the device-specific keywords
    # above, kept for generic/cross-driver tooling that expects the RFDS
    # canonical names. The device-specific keywords remain the primary,
    # documented API for this driver.
    # ------------------------------------------------------------------
    @keyword("Connect")
    @_evidenced
    def connect(
        self,
        resource: str | None = None,
        alias: str = "default",
        timeout_s: float | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        """RFDS-002 generic connect. ``resource`` is the serial port (see ``Connect To Electronic Load``).

        Idempotent when ``alias`` is already connected to the same ``resource``.
        """
        selected_alias = str(alias).strip() or self.default_alias
        port = resource or self.default_port
        if selected_alias in self._devices:
            existing = self._devices[selected_alias]
            if port and str(existing.config.port) != str(port):
                raise BK8500BRobotError(
                    f"Alias {selected_alias!r} is already connected to {existing.config.port!r}; "
                    f"disconnect it before connecting it to {port!r}."
                )
            return self._connection_state(selected_alias, existing)
        connect_kwargs: dict[str, Any] = dict(options)
        if timeout_s is not None:
            for key in ("read_timeout", "write_timeout", "query_timeout"):
                connect_kwargs.setdefault(key, timeout_s)
        self.connect_to_electronic_load(port, alias=selected_alias, **connect_kwargs)
        return self._connection_state(selected_alias, self._devices[selected_alias])

    @keyword("Disconnect")
    @_evidenced
    def disconnect(self, alias: str | None = None) -> None:
        """RFDS-002 generic disconnect. Idempotent: succeeds even if already disconnected."""
        selected = str(alias) if alias not in (None, "") else self._active_alias
        if selected is None or selected not in self._devices:
            return
        self.disconnect_electronic_load(selected)

    @keyword("Is Connected")
    @_evidenced
    def is_connected(self, alias: str | None = None) -> bool:
        """Return whether ``alias`` (or the active session) is connected."""
        selected = str(alias) if alias not in (None, "") else self._active_alias
        if selected is None or selected not in self._devices:
            return False
        return bool(self._devices[selected].connected)

    @keyword("Get Connection State")
    @_evidenced
    def get_connection_state(self, alias: str | None = None, refresh: bool = False) -> dict[str, Any]:
        """Return the RFDS-002 Section 12.1 normalized connection-state dictionary."""
        selected = str(alias) if alias not in (None, "") else self._active_alias
        if selected is None or selected not in self._devices:
            return {
                "alias": selected or self.default_alias,
                "resource": None,
                "connected": False,
                "communication_ok": False,
                "transport": None,
                "identity": None,
                "timeout_s": None,
                "state": "disconnected",
            }
        device = self._devices[selected]
        if as_bool(refresh, name="refresh") and device.connected:
            try:
                self._translate("Health check", device.health_check)
            except BK8500BRobotError:
                pass
        return self._connection_state(selected, device)

    @keyword("Check Communication")
    @_evidenced
    def check_communication(self, alias: str | None = None) -> bool:
        """Perform a bounded, non-destructive communication check. Raises on failure."""
        device = self._device(alias)
        self._translate("Check communication", device.health_check)
        return True

    @keyword("Get Identity")
    @_evidenced
    def get_identity(self, alias: str | None = None, refresh: bool = True) -> str:
        """Return a stable human-readable identity string.

        The underlying driver caches identity for the life of the session, so
        ``refresh`` only forces the first query rather than repeating it.
        """
        del refresh
        device = self._device(alias)
        ident = to_robot(self._translate("Identify", device.identify))
        raw = ident.get("raw")
        if raw:
            return str(raw)
        parts = [str(ident[key]) for key in ("manufacturer", "model", "serial_number", "firmware_revision") if ident.get(key)]
        return ", ".join(parts) if parts else "BK8500B"

    # ------------------------------------------------------------------
    # Identity, status, diagnostics
    # ------------------------------------------------------------------
    @keyword("Identify Electronic Load")
    @_evidenced
    def identify_electronic_load(self, alias: str | None = None) -> dict[str, Any]:
        """Return manufacturer, model, serial number, and firmware revision."""
        return to_robot(self._translate("Identify", self._device(alias).identify))

    @keyword("Get Electronic Load Capabilities")
    @_evidenced
    def get_electronic_load_capabilities(
        self, refresh: bool = False, alias: str | None = None
    ) -> dict[str, Any]:
        """Return model ratings, supported features, and evidence metadata."""
        return to_robot(
            self._translate(
                "Get capabilities",
                self._device(alias).get_capabilities,
                refresh=as_bool(refresh, name="refresh"),
            )
        )

    @keyword("Get Electronic Load Status")
    @_evidenced
    def get_electronic_load_status(self, alias: str | None = None) -> dict[str, Any]:
        """Return input, short, mode, status registers, and protection flags."""
        return to_robot(self._translate("Get status", self._device(alias).get_device_status))

    @keyword("Run Electronic Load Health Check")
    @_evidenced
    def run_electronic_load_health_check(self, alias: str | None = None) -> dict[str, Any]:
        """Return a health report with latency and consecutive failure count."""
        return to_robot(self._translate("Health check", self._device(alias).health_check))

    @keyword("Get Electronic Load Diagnostic Snapshot")
    @_evidenced
    def get_electronic_load_diagnostic_snapshot(
        self, alias: str | None = None
    ) -> dict[str, Any]:
        """Return a structured diagnostic snapshot suitable for report attachments."""
        return to_robot(self._translate("Diagnostic snapshot", self._device(alias).diagnostic_snapshot))

    @keyword("Run Electronic Load Self Test")
    @_evidenced
    def run_electronic_load_self_test(
        self, timeout: float | None = None, alias: str | None = None
    ) -> dict[str, Any]:
        """Run ``*TST?`` and fail when the instrument reports a non-zero code."""
        timeout_s = None if timeout in (None, "") else as_float(timeout, name="timeout")
        result = self._translate("Self test", self._device(alias).self_test, timeout_s=timeout_s)
        if not result.passed:
            raise AssertionError(f"Electronic load self-test failed with code {result.code}")
        return to_robot(result)

    @keyword("Clear Electronic Load Status")
    @_evidenced
    def clear_electronic_load_status(self, alias: str | None = None) -> None:
        """Clear SCPI status registers and error queue using ``*CLS``."""
        self._translate("Clear status", self._device(alias).clear_status)

    @keyword("Drain Electronic Load Error Queue")
    @_evidenced
    def drain_electronic_load_error_queue(
        self, maximum: int | None = None, alias: str | None = None
    ) -> list[dict[str, Any]]:
        """Read errors until the instrument reports no error or ``maximum`` is reached."""
        limit = None if maximum in (None, "") else as_int(maximum, name="maximum")
        return to_robot(
            self._translate("Drain error queue", self._device(alias).drain_error_queue, maximum=limit)
        )

    # ------------------------------------------------------------------
    # Modes, setpoints, protections, input
    # ------------------------------------------------------------------
    @keyword("Set Electronic Load Mode")
    @_evidenced
    def set_electronic_load_mode(self, mode: str, alias: str | None = None) -> str:
        """Set CC, CV, CP/CW, CR, dynamic, LED, or impedance mode."""
        selected = self._mode(mode)
        self._translate("Set operating mode", self._device(alias).set_operating_mode, selected)
        return selected.value

    @keyword("Get Electronic Load Mode")
    @_evidenced
    def get_electronic_load_mode(self, alias: str | None = None) -> str:
        """Return the current driver mode token."""
        return self._translate("Get operating mode", self._device(alias).get_operating_mode).value

    @keyword("Enable Electronic Load Input")
    @_evidenced
    def enable_electronic_load_input(self, alias: str | None = None) -> None:
        """Enable input. A short-lived safety token is supplied when policy requires it."""
        device = self._device(alias)
        token = SafetyToken.issue("enable_input")
        self._translate("Enable input", device.set_input_enabled, True, token=token)

    @keyword("Disable Electronic Load Input")
    @_evidenced
    def disable_electronic_load_input(self, alias: str | None = None) -> None:
        """Disable load input and verify the state when verification is enabled."""
        self._translate("Disable input", self._device(alias).set_input_enabled, False)

    @keyword("Electronic Load Input Should Be On")
    @_evidenced
    def electronic_load_input_should_be_on(self, alias: str | None = None) -> None:
        """Fail unless load input is on."""
        if not self._translate("Read input state", self._device(alias).get_input_enabled):
            raise AssertionError("Electronic load input is OFF")

    @keyword("Electronic Load Input Should Be Off")
    @_evidenced
    def electronic_load_input_should_be_off(self, alias: str | None = None) -> None:
        """Fail unless load input is off."""
        if self._translate("Read input state", self._device(alias).get_input_enabled):
            raise AssertionError("Electronic load input is ON")

    @keyword("Configure And Enable Load")
    @_evidenced
    def configure_and_enable_load(
        self,
        mode: str,
        setpoint: float,
        current_limit: float | None = None,
        power_limit: float | None = None,
        remote_sense: bool = False,
        alias: str | None = None,
    ) -> dict[str, Any]:
        """Safely configure a fixed mode and enable input as one rollback-aware operation."""
        config = SafeEnableConfig(
            mode=self._mode(mode),
            setpoint=as_float(setpoint, name="setpoint"),
            current_limit_a=(
                None
                if current_limit in (None, "")
                else as_float(current_limit, name="current_limit")
            ),
            power_limit_w=(
                None if power_limit in (None, "") else as_float(power_limit, name="power_limit")
            ),
            remote_sense=as_bool(remote_sense, name="remote_sense"),
        )
        result = self._translate(
            "Configure and enable load",
            self._device(alias).configure_and_enable,
            config,
            token=SafetyToken.issue("enable_input"),
        )
        return to_robot(result)

    @keyword("Set Current Setpoint")
    @_evidenced
    def set_current_setpoint(self, amperes: float, alias: str | None = None) -> dict[str, Any]:
        """Set and read back the CC setpoint in amperes."""
        return to_robot(
            self._translate(
                "Set current", self._device(alias).set_current_setpoint, as_float(amperes)
            )
        )

    @keyword("Get Current Setpoint")
    @_evidenced
    def get_current_setpoint(self, alias: str | None = None) -> float:
        return float(self._translate("Get current", self._device(alias).get_current_setpoint))

    @keyword("Set Voltage Setpoint")
    @_evidenced
    def set_voltage_setpoint(self, volts: float, alias: str | None = None) -> dict[str, Any]:
        """Set and read back the CV setpoint in volts."""
        return to_robot(
            self._translate("Set voltage", self._device(alias).set_voltage_setpoint, as_float(volts))
        )

    @keyword("Get Voltage Setpoint")
    @_evidenced
    def get_voltage_setpoint(self, alias: str | None = None) -> float:
        return float(self._translate("Get voltage", self._device(alias).get_voltage_setpoint))

    @keyword("Set Power Setpoint")
    @_evidenced
    def set_power_setpoint(self, watts: float, alias: str | None = None) -> dict[str, Any]:
        """Set and read back the CP setpoint in watts."""
        return to_robot(
            self._translate("Set power", self._device(alias).set_power_setpoint, as_float(watts))
        )

    @keyword("Get Power Setpoint")
    @_evidenced
    def get_power_setpoint(self, alias: str | None = None) -> float:
        return float(self._translate("Get power", self._device(alias).get_power_setpoint))

    @keyword("Set Resistance Setpoint")
    @_evidenced
    def set_resistance_setpoint(self, ohms: float, alias: str | None = None) -> dict[str, Any]:
        """Set and read back the CR setpoint in ohms."""
        return to_robot(
            self._translate(
                "Set resistance", self._device(alias).set_resistance_setpoint, as_float(ohms)
            )
        )

    @keyword("Get Resistance Setpoint")
    @_evidenced
    def get_resistance_setpoint(self, alias: str | None = None) -> float:
        return float(self._translate("Get resistance", self._device(alias).get_resistance_setpoint))

    @keyword("Set Current Protection")
    @_evidenced
    def set_current_protection(self, amperes: float, alias: str | None = None) -> dict[str, Any]:
        """Set over-current protection in amperes."""
        return to_robot(
            self._translate(
                "Set current protection",
                self._device(alias).set_current_protection,
                as_float(amperes),
            )
        )

    @keyword("Get Current Protection")
    @_evidenced
    def get_current_protection(self, alias: str | None = None) -> float:
        return float(self._translate("Get current protection", self._device(alias).get_current_protection))

    @keyword("Set Power Protection")
    @_evidenced
    def set_power_protection(self, watts: float, alias: str | None = None) -> dict[str, Any]:
        """Set over-power protection in watts."""
        return to_robot(
            self._translate(
                "Set power protection", self._device(alias).set_power_protection, as_float(watts)
            )
        )

    @keyword("Get Power Protection")
    @_evidenced
    def get_power_protection(self, alias: str | None = None) -> float:
        return float(self._translate("Get power protection", self._device(alias).get_power_protection))

    @keyword("Set Remote Sense")
    @_evidenced
    def set_remote_sense(self, enabled: bool, alias: str | None = None) -> None:
        """Enable or disable remote sense. Input must be off when policy requires it."""
        self._translate(
            "Set remote sense",
            self._device(alias).set_remote_sense,
            as_bool(enabled, name="enabled"),
        )

    @keyword("Get Remote Sense")
    @_evidenced
    def get_remote_sense(self, alias: str | None = None) -> bool:
        return bool(self._translate("Get remote sense", self._device(alias).get_remote_sense))

    @keyword("Set Current Range")
    @_evidenced
    def set_current_range(self, amperes: float, alias: str | None = None) -> dict[str, Any]:
        return to_robot(
            self._translate("Set current range", self._device(alias).set_current_range, as_float(amperes))
        )

    @keyword("Get Current Range")
    @_evidenced
    def get_current_range(self, alias: str | None = None) -> float:
        return float(self._translate("Get current range", self._device(alias).get_current_range))

    @keyword("Set Voltage Range")
    @_evidenced
    def set_voltage_range(self, volts: float, alias: str | None = None) -> dict[str, Any]:
        return to_robot(
            self._translate("Set voltage range", self._device(alias).set_voltage_range, as_float(volts))
        )

    @keyword("Get Voltage Range")
    @_evidenced
    def get_voltage_range(self, alias: str | None = None) -> float:
        return float(self._translate("Get voltage range", self._device(alias).get_voltage_range))

    @keyword("Set Voltage Autorange")
    @_evidenced
    def set_voltage_autorange(self, enabled: bool, alias: str | None = None) -> None:
        self._translate(
            "Set voltage autorange",
            self._device(alias).set_voltage_autorange,
            as_bool(enabled, name="enabled"),
        )

    @keyword("Get Voltage Autorange")
    @_evidenced
    def get_voltage_autorange(self, alias: str | None = None) -> bool:
        return bool(self._translate("Get voltage autorange", self._device(alias).get_voltage_autorange))

    @keyword("Set Current Slew Rate")
    @_evidenced
    def set_current_slew_rate(
        self,
        rise_a_per_us: float,
        fall_a_per_us: float | None = None,
        alias: str | None = None,
    ) -> dict[str, Any]:
        """Set rise and fall current slew rates. Omit fall to set both equally."""
        device = self._device(alias)
        rise = as_float(rise_a_per_us, name="rise_a_per_us")
        if fall_a_per_us in (None, ""):
            return to_robot(self._translate("Set slew rate", device.set_current_slew, rise))
        fall = as_float(fall_a_per_us, name="fall_a_per_us")
        rise_result = self._translate("Set rise slew", device.set_current_slew_rise, rise)
        fall_result = self._translate("Set fall slew", device.set_current_slew_fall, fall)
        return {"rise": to_robot(rise_result), "fall": to_robot(fall_result)}

    @keyword("Get Current Slew Rate")
    @_evidenced
    def get_current_slew_rate(self, alias: str | None = None) -> dict[str, Any]:
        return to_robot(self._translate("Get slew rate", self._device(alias).get_current_slew))

    @keyword("Set Load Voltage Thresholds")
    @_evidenced
    def set_load_voltage_thresholds(
        self, on_voltage: float, off_voltage: float, alias: str | None = None
    ) -> dict[str, Any]:
        """Set load-on and load-off voltage thresholds."""
        device = self._device(alias)
        on_result = self._translate(
            "Set load-on voltage", device.set_load_on_voltage, as_float(on_voltage)
        )
        off_result = self._translate(
            "Set load-off voltage", device.set_load_off_voltage, as_float(off_voltage)
        )
        return {"on": to_robot(on_result), "off": to_robot(off_result)}

    @keyword("Clear Electronic Load Protection")
    @_evidenced
    def clear_electronic_load_protection(self, alias: str | None = None) -> None:
        """Clear latched protection using a short-lived purpose-specific safety token."""
        self._translate(
            "Clear protection",
            self._device(alias).clear_protection,
            token=SafetyToken.issue("clear_protection"),
        )

    @keyword("Set Short Circuit Mode")
    @_evidenced
    def set_short_circuit_mode(
        self,
        enabled: bool,
        confirmation: str = "",
        alias: str | None = None,
    ) -> None:
        """Enable or disable short-circuit mode.

        Enabling requires ``allow_short=True`` during connection and confirmation exactly
        equal to ``I UNDERSTAND``. Disabling does not require the confirmation text.
        """
        state = as_bool(enabled, name="enabled")
        if state and confirmation != "I UNDERSTAND":
            raise BK8500BRobotError(
                "Enabling short-circuit mode requires confirmation='I UNDERSTAND'"
            )
        self._translate(
            "Set short-circuit mode",
            self._device(alias).set_short_enabled,
            state,
            token=SafetyToken.issue("enable_short"),
        )

    # ------------------------------------------------------------------
    # Measurements and assertions
    # ------------------------------------------------------------------
    @keyword("Measure Voltage")
    @_evidenced
    def measure_voltage(self, alias: str | None = None) -> float:
        """Return measured voltage in volts."""
        return self._measurement("voltage", alias)

    @keyword("Measure Current")
    @_evidenced
    def measure_current(self, alias: str | None = None) -> float:
        """Return measured current in amperes."""
        return self._measurement("current", alias)

    @keyword("Measure Power")
    @_evidenced
    def measure_power(self, alias: str | None = None) -> float:
        """Return measured power in watts."""
        return self._measurement("power", alias)

    @keyword("Measure Resistance")
    @_evidenced
    def measure_resistance(self, alias: str | None = None) -> float:
        """Return measured resistance in ohms."""
        return self._measurement("resistance", alias)

    @keyword("Get Measurement Snapshot")
    @_evidenced
    def get_measurement_snapshot(self, alias: str | None = None) -> dict[str, Any]:
        """Return voltage, current, power, optional resistance, and status metadata."""
        return to_robot(self._translate("Measure all", self._device(alias).measure_all))

    @keyword("Measurement Should Be Within Range")
    @_evidenced
    def measurement_should_be_within_range(
        self, actual: float, minimum: float, maximum: float, name: str = "Measurement"
    ) -> None:
        """Assert that a supplied numeric value is inclusively inside a range."""
        self._assert_range(str(name), as_float(actual, name="actual"), minimum, maximum)

    @keyword("Voltage Should Be Within Range")
    @_evidenced
    def voltage_should_be_within_range(
        self, minimum: float, maximum: float, alias: str | None = None
    ) -> float:
        """Measure voltage, assert an inclusive range, and return the reading."""
        actual = self.measure_voltage(alias)
        self._assert_range("Voltage", actual, minimum, maximum)
        return actual

    @keyword("Current Should Be Within Range")
    @_evidenced
    def current_should_be_within_range(
        self, minimum: float, maximum: float, alias: str | None = None
    ) -> float:
        """Measure current, assert an inclusive range, and return the reading."""
        actual = self.measure_current(alias)
        self._assert_range("Current", actual, minimum, maximum)
        return actual

    @keyword("Power Should Be Within Range")
    @_evidenced
    def power_should_be_within_range(
        self, minimum: float, maximum: float, alias: str | None = None
    ) -> float:
        """Measure power, assert an inclusive range, and return the reading."""
        actual = self.measure_power(alias)
        self._assert_range("Power", actual, minimum, maximum)
        return actual

    @keyword("Wait Until Measurement Is Within Range")
    @_evidenced
    def wait_until_measurement_is_within_range(
        self,
        measurement: str,
        minimum: float,
        maximum: float,
        timeout: float = 10.0,
        interval: float = 0.25,
        alias: str | None = None,
    ) -> float:
        """Poll voltage, current, power, or resistance until it enters a range."""
        kind = str(measurement).strip().lower()
        if kind not in {"voltage", "current", "power", "resistance"}:
            raise ValueError("measurement must be voltage, current, power, or resistance")
        low = as_float(minimum, name="minimum")
        high = as_float(maximum, name="maximum")
        timeout_s = as_float(timeout, name="timeout")
        interval_s = as_float(interval, name="interval")
        if low > high:
            raise ValueError("minimum must not be greater than maximum")
        if timeout_s <= 0 or interval_s <= 0:
            raise ValueError("timeout and interval must be positive")
        deadline = time.monotonic() + timeout_s
        last = math.nan
        while True:
            last = self._measurement(kind, alias)
            if low <= last <= high:
                return last
            if time.monotonic() >= deadline:
                raise AssertionError(
                    f"{kind.title()} did not enter [{low:g}, {high:g}] within {timeout_s:g} s; "
                    f"last value was {last:g}"
                )
            time.sleep(min(interval_s, max(0.0, deadline - time.monotonic())))

    @keyword("Log Measurements To CSV")
    @_evidenced
    def log_measurements_to_csv(
        self,
        path: str,
        samples: int = 10,
        interval: float = 1.0,
        include_resistance: bool = False,
        alias: str | None = None,
    ) -> str:
        """Record a finite number of timestamped measurement snapshots to CSV.

        The file contains UTC timestamp, monotonic timestamp, voltage, current, power,
        resistance (optional), input state, mode, and protection flags.
        """
        count = as_int(samples, name="samples")
        interval_s = as_float(interval, name="interval")
        if count < 1:
            raise ValueError("samples must be at least 1")
        if interval_s < 0:
            raise ValueError("interval must be non-negative")
        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "sample",
            "timestamp_utc",
            "monotonic_timestamp_s",
            "voltage_v",
            "current_a",
            "power_w",
        ]
        if as_bool(include_resistance, name="include_resistance"):
            fields.append("resistance_ohm")
        fields.extend(["input_enabled", "operating_mode", "protection_flags"])
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for index in range(1, count + 1):
                snapshot = self._translate("Measure all", self._device(alias).measure_all)
                row: dict[str, Any] = {
                    "sample": index,
                    "timestamp_utc": snapshot.voltage.wall_timestamp_utc.isoformat(),
                    "monotonic_timestamp_s": snapshot.voltage.monotonic_timestamp_s,
                    "voltage_v": snapshot.voltage.value,
                    "current_a": snapshot.current.value,
                    "power_w": snapshot.power.value,
                    "input_enabled": (
                        snapshot.status.input_enabled if snapshot.status is not None else ""
                    ),
                    "operating_mode": (
                        snapshot.status.operating_mode.value
                        if snapshot.status is not None and snapshot.status.operating_mode is not None
                        else ""
                    ),
                    "protection_flags": (
                        int(snapshot.status.protection_flags) if snapshot.status is not None else ""
                    ),
                }
                if "resistance_ohm" in fields:
                    row["resistance_ohm"] = (
                        snapshot.resistance.value if snapshot.resistance is not None else ""
                    )
                writer.writerow(row)
                handle.flush()
                if index != count and interval_s:
                    time.sleep(interval_s)
        logger.info(f"Wrote {count} measurement samples to {output}")
        return str(output)

    # ------------------------------------------------------------------
    # Dynamic, peak, state and raw SCPI operations
    # ------------------------------------------------------------------
    @keyword("Configure Transient Load")
    @_evidenced
    def configure_transient_load(
        self,
        high_level: float,
        high_dwell: float,
        low_level: float,
        low_dwell: float,
        slew_a_per_us: float,
        mode: str = "continuous",
        alias: str | None = None,
    ) -> None:
        """Configure dynamic load levels, dwell times, slew, and dynamic mode."""
        config = TransientConfig(
            high_level=as_float(high_level),
            high_dwell_s=as_float(high_dwell),
            low_level=as_float(low_level),
            low_dwell_s=as_float(low_dwell),
            slew_a_per_us=as_float(slew_a_per_us),
            mode=self._dynamic_mode(mode),
        )
        self._translate("Configure transient", self._device(alias).configure_transient, config)

    @keyword("Get Transient Load Configuration")
    @_evidenced
    def get_transient_load_configuration(self, alias: str | None = None) -> dict[str, Any]:
        return to_robot(
            self._translate("Get transient configuration", self._device(alias).get_transient_config)
        )

    @keyword("Trigger Electronic Load")
    @_evidenced
    def trigger_electronic_load(self, alias: str | None = None) -> None:
        """Send the SCPI trigger command."""
        self._translate("Trigger", self._device(alias).trigger)

    @keyword("Enable Peak Capture")
    @_evidenced
    def enable_peak_capture(self, enabled: bool = True, alias: str | None = None) -> None:
        self._translate(
            "Set peak capture",
            self._device(alias).set_peak_enabled,
            as_bool(enabled, name="enabled"),
        )

    @keyword("Clear Peak Capture")
    @_evidenced
    def clear_peak_capture(self, alias: str | None = None) -> None:
        self._translate("Clear peak capture", self._device(alias).clear_peak)

    @keyword("Read Peak Measurements")
    @_evidenced
    def read_peak_measurements(self, alias: str | None = None) -> dict[str, float]:
        """Return maximum/minimum captured voltage and current."""
        device = self._device(alias)
        return {
            "voltage_maximum_v": self._translate(
                "Read peak voltage maximum", device.read_peak_voltage_maximum
            ).value,
            "voltage_minimum_v": self._translate(
                "Read peak voltage minimum", device.read_peak_voltage_minimum
            ).value,
            "current_maximum_a": self._translate(
                "Read peak current maximum", device.read_peak_current_maximum
            ).value,
            "current_minimum_a": self._translate(
                "Read peak current minimum", device.read_peak_current_minimum
            ).value,
        }

    @keyword("Save Electronic Load State")
    @_evidenced
    def save_electronic_load_state(self, slot: int, alias: str | None = None) -> None:
        self._translate("Save state", self._device(alias).save_state, as_int(slot, name="slot"))

    @keyword("Recall Electronic Load State")
    @_evidenced
    def recall_electronic_load_state(self, slot: int, alias: str | None = None) -> None:
        device = self._device(alias)
        self._translate("Recall state", device.recall_state, as_int(slot, name="slot"))
        self._translate("Synchronize state", device.synchronize_state)

    @keyword("Reset Electronic Load")
    @_evidenced
    def reset_electronic_load(self, alias: str | None = None) -> None:
        """Reset the instrument and resynchronize driver state."""
        device = self._device(alias)
        self._translate("Reset device", device.reset_device)
        self._translate("Synchronize state", device.synchronize_state)

    @keyword("Set Electronic Load Remote")
    @_evidenced
    def set_electronic_load_remote(self, local_lockout: bool = False, alias: str | None = None) -> None:
        device = self._device(alias)
        method = device.set_remote_with_local_lockout if as_bool(local_lockout) else device.set_remote
        self._translate("Set remote control", method)

    @keyword("Set Electronic Load Local")
    @_evidenced
    def set_electronic_load_local(self, alias: str | None = None) -> None:
        """Return front-panel control and resynchronize the driver state."""
        device = self._device(alias)
        self._translate("Set local control", device.set_local)
        self._translate("Synchronize state", device.synchronize_state)

    @keyword("Query Raw SCPI")
    @_evidenced
    def query_raw_scpi(
        self, command: str, timeout: float | None = None, alias: str | None = None
    ) -> str:
        """Send an expert-level raw SCPI query and return its response."""
        timeout_s = None if timeout in (None, "") else as_float(timeout, name="timeout")
        return self._translate(
            "Raw SCPI query",
            self._device(alias).query_raw_scpi,
            str(command),
            timeout_s=timeout_s,
        )

    @keyword("Write Raw SCPI")
    @_evidenced
    def write_raw_scpi(
        self, command: str, timeout: float | None = None, alias: str | None = None
    ) -> None:
        """Send an expert-level raw SCPI command. Driver safety restrictions still apply."""
        timeout_s = None if timeout in (None, "") else as_float(timeout, name="timeout")
        self._translate(
            "Raw SCPI write",
            self._device(alias).write_raw_scpi,
            str(command),
            timeout_s=timeout_s,
        )

    @keyword("Export Diagnostic Snapshot")
    @_evidenced
    def export_diagnostic_snapshot(self, path: str, alias: str | None = None) -> str:
        """Write a diagnostic snapshot as formatted UTF-8 JSON and return its path."""
        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        snapshot = self.get_electronic_load_diagnostic_snapshot(alias)
        output.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
        return str(output)

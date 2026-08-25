"""Explicit Robot Framework keyword surface for Keysight 34970A/34972A."""
from __future__ import annotations

import platform
from importlib.metadata import PackageNotFoundError, version as package_version
from typing import Any

from ._rfds_compat import BaseInstrumentLibrary
from ._robot_compat import keyword, library
from .capabilities import CAPABILITY_IDS
from .converters import as_slot
from .core import Keysight349xxCore, MeasurementEngine
from .core.measurement import canonical_channel, channel_exists, list_measurement_channels
from .exceptions import DriverDeviceError, DriverResponseError
from .protocol.parsers import parse_identity
from .transports import TransportFactory
from .version import __release_class__, __version__

try:
    _robot_version = package_version("robotframework")
except PackageNotFoundError:
    _robot_version = "NOT_INSTALLED"

METADATA = {
    "name": "rf_keysight349xx",
    "package_version": __version__,
    "api_version": "1.0.0",
    "api_spec": "RFDS-002",
    "api_spec_version": "1.1",
    "robot_framework_min_version": "7.0",
    "python_min_version": "3.10",
    "library_scope": "SUITE",
    "transport_types": ["simulator", "visa"],
    "capability_ids": list(CAPABILITY_IDS),
    "simulation_supported": True,
    "identity_source": "device_query",
    "vendor": "Keysight Technologies / Agilent Technologies",
    "model_family": "34970A/34972A",
    "release_class": __release_class__,
    "rfds_core_runtime": "embedded_compat_DEV-RFDSCORE-001",
    "robot_framework_runtime": _robot_version,
    "python_runtime": platform.python_version(),
}


@library(scope="SUITE", version=__version__, auto_keywords=False)
class Keysight349xxLibrary(BaseInstrumentLibrary):
    """Robot Framework driver for Keysight/Agilent 34970A and 34972A.

    The current D0 implementation covers deterministic connection, identity,
    installed-module discovery, SCPI-version and error-queue operations, plus
    validated single-channel voltage, current, resistance, frequency, and period
    measurements.  Scanning and switching remain intentionally deferred.
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = __version__
    ROBOT_AUTO_KEYWORDS = False

    def __init__(self, default_timeout_s: object = 5.0, default_resource: str | None = None) -> None:
        from .converters import as_timeout
        self._transport_factory = TransportFactory()
        super().__init__(
            metadata=METADATA,
            capabilities=CAPABILITY_IDS,
            default_timeout_s=as_timeout(default_timeout_s, name="default_timeout_s"),
            default_resource=default_resource,
        )

    def _build_transport(self, resource: str, timeout_s: float, options: dict[str, Any]):
        return self._transport_factory.create(resource, timeout_s=timeout_s, options=options)

    def _probe_communication(self, session, timeout_s: float) -> None:
        core = Keysight349xxCore(session.transport)
        operation_id = "connect.probe" if session.state == "connecting" else "communication.check"
        identity = core.read_identity(timeout_s=min(timeout_s, 2.0), operation_id=operation_id)
        if session.state == "connecting":
            session.probe_identity_raw = identity.raw_response

    def _read_identity(self, session, timeout_s: float):
        if session.probe_identity_raw:
            raw = session.probe_identity_raw
            session.probe_identity_raw = None
            return parse_identity(raw)
        return Keysight349xxCore(session.transport).read_identity(
            timeout_s=min(timeout_s, 2.0), operation_id="identity.refresh"
        )

    def _on_connected(self, session, timeout_s: float) -> None:
        core = Keysight349xxCore(session.transport)
        session.modules = core.get_modules(timeout_s=min(timeout_s, 2.0))

    @keyword("Get Installed Modules", tags=["rfds:query", "rfds:low_risk"])
    def get_installed_modules(self, alias=None) -> list[dict]:
        """Return cached module identities captured during connection."""
        session = self._session(alias)
        return [session.modules[slot].as_dict() for slot in (100, 200, 300) if session.modules[slot].installed]

    @keyword("Get Module Information", tags=["rfds:query", "rfds:low_risk"])
    def get_module_information(self, slot, alias=None, refresh=False) -> dict:
        """Return module information for slot 100, 200, or 300."""
        normalized = as_slot(slot)
        session = self._session(alias)
        if str(refresh).strip().lower() in {"1", "true", "yes", "on"}:
            session.modules[normalized] = Keysight349xxCore(session.transport).get_module(
                normalized, timeout_s=session.timeout_s, operation_id=f"module.{normalized}.refresh"
            )
        return session.modules[normalized].as_dict()

    @keyword("Get SCPI Version", tags=["rfds:query", "rfds:low_risk"])
    def get_scpi_version(self, alias=None) -> str:
        """Return the SCPI standard version reported by ``SYST:VERS?``."""
        return self._execute_operation(
            "get_scpi_version",
            lambda session, timeout: Keysight349xxCore(session.transport).get_scpi_version(timeout_s=timeout),
            alias=alias,
        )

    @keyword("Get Device Error", tags=["rfds:query", "rfds:low_risk"])
    def get_device_error(self, alias=None) -> dict:
        """Read and clear one device error using ``SYST:ERR?``."""
        return self._execute_operation(
            "get_device_error",
            lambda session, timeout: Keysight349xxCore(session.transport).get_device_error(timeout_s=timeout),
            alias=alias,
        )

    @keyword("Get All Device Errors", tags=["rfds:query", "rfds:low_risk"])
    def get_all_device_errors(self, alias=None, max_count=100) -> list[dict]:
        """Drain the device error queue, bounded by ``max_count``."""
        try:
            limit = int(max_count)
        except (TypeError, ValueError) as exc:
            from .exceptions import DriverValidationError
            raise DriverValidationError("max_count must be a positive integer") from exc
        if limit <= 0:
            from .exceptions import DriverValidationError
            raise DriverValidationError("max_count must be a positive integer")
        errors: list[dict] = []
        for _ in range(limit):
            item = self.get_device_error(alias)
            if int(item["code"]) == 0:
                return errors
            errors.append(item)
        raise DriverDeviceError(
            f"device error queue did not reach the no-error sentinel within max_count={limit}",
            code="RFDS-DEV-002",
            operation="Get All Device Errors",
            alias=str(alias) if alias is not None else None,
        )

    @keyword("Clear Device Errors", tags=["rfds:command", "rfds:low_risk"])
    def clear_device_errors(self, alias=None) -> None:
        """Clear the SCPI status/error queues using ``*CLS``."""
        self._execute_operation(
            "clear_device_errors",
            lambda session, timeout: Keysight349xxCore(session.transport).clear_device_errors(timeout_s=timeout),
            alias=alias,
        )

    @keyword("Device Error Queue Should Be Empty", tags=["rfds:assertion", "rfds:low_risk"])
    def device_error_queue_should_be_empty(self, alias=None) -> None:
        """Assert that ``SYST:ERR?`` reports no device error."""
        item = self.get_device_error(alias)
        if int(item["code"]) != 0:
            raise AssertionError(f"device error queue is not empty: {item['raw']}")

    @keyword("List Channels", tags=["rfds:query", "rfds:channel", "rfds:low_risk"])
    def list_channels(self, alias=None) -> list[str]:
        """Return canonical channels supported by the implemented measurement group."""
        session = self._session(alias)
        return list_measurement_channels(session.modules)

    @keyword("Validate Channel", tags=["rfds:query", "rfds:channel", "rfds:low_risk"])
    def validate_channel(self, channel, alias=None) -> bool:
        """Return whether a well-formed channel exists in the implemented measurement set."""
        session = self._session(alias)
        canonical_channel(channel)
        return channel_exists(session.modules, channel)

    def _measure_scalar(self, measurement_key: str, channel, range_value=None, resolution=None, alias=None) -> float:
        return self._execute_operation(
            f"measure_{measurement_key}",
            lambda session, timeout: MeasurementEngine(session.transport).measure(
                measurement_key,
                session.modules,
                channel,
                range_value=range_value,
                resolution=resolution,
                timeout_s=timeout,
            ),
            alias=alias,
        )

    @keyword("Measure DC Voltage", tags=["rfds:measurement", "rfds:low_risk"])
    def measure_dc_voltage(self, channel, range_value=None, resolution=None, alias=None) -> float:
        """Acquire one DC voltage reading in volts from a supported multiplexer channel."""
        return self._measure_scalar("dc_voltage", channel, range_value, resolution, alias)

    @keyword("Measure AC Voltage", tags=["rfds:measurement", "rfds:low_risk"])
    def measure_ac_voltage(self, channel, range_value=None, resolution=None, alias=None) -> float:
        """Acquire one AC voltage reading in volts from a supported multiplexer channel."""
        return self._measure_scalar("ac_voltage", channel, range_value, resolution, alias)

    @keyword("Measure DC Current", tags=["rfds:measurement", "rfds:low_risk"])
    def measure_dc_current(self, channel, range_value=None, resolution=None, alias=None) -> float:
        """Acquire one DC current reading in amperes."""
        return self._measure_scalar("dc_current", channel, range_value, resolution, alias)

    @keyword("Measure AC Current", tags=["rfds:measurement", "rfds:low_risk"])
    def measure_ac_current(self, channel, range_value=None, resolution=None, alias=None) -> float:
        """Acquire one AC current reading in amperes from 34901A channel 21 or 22."""
        return self._measure_scalar("ac_current", channel, range_value, resolution, alias)

    @keyword("Measure Resistance", tags=["rfds:measurement", "rfds:medium_risk"])
    def measure_resistance(self, channel, range_value=None, resolution=None, alias=None) -> float:
        """Acquire one two-wire resistance reading in ohms."""
        return self._measure_scalar("resistance", channel, range_value, resolution, alias)

    @keyword("Measure 4 Wire Resistance", tags=["rfds:measurement", "rfds:medium_risk"])
    def measure_4_wire_resistance(self, channel, range_value=None, resolution=None, alias=None) -> float:
        """Acquire one four-wire resistance reading in ohms."""
        return self._measure_scalar("four_wire_resistance", channel, range_value, resolution, alias)

    @keyword("Measure Frequency", tags=["rfds:measurement", "rfds:low_risk"])
    def measure_frequency(self, channel, range_value=None, resolution=None, alias=None) -> float:
        """Acquire one frequency reading in hertz."""
        return self._measure_scalar("frequency", channel, range_value, resolution, alias)

    @keyword("Measure Period", tags=["rfds:measurement", "rfds:low_risk"])
    def measure_period(self, channel, range_value=None, resolution=None, alias=None) -> float:
        """Acquire one period reading in seconds."""
        return self._measure_scalar("period", channel, range_value, resolution, alias)

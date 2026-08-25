"""Phase 3 Robot Framework keyword surface for Keysight 34970A/34972A."""
from __future__ import annotations

from ._robot_compat import keyword, library
from .core import AcquisitionEngine, MeasurementEngine
from .library_base import Keysight349xxLibrary as _Phase2Library
from .version import __version__


@library(scope="SUITE", version=__version__, auto_keywords=False)
class Keysight349xxLibrary(_Phase2Library):
    """Extend the validated Phase 2 library with scan/trigger configuration."""

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = __version__
    ROBOT_AUTO_KEYWORDS = False

    def _configure_scalar(self, measurement_key: str, channel, range_value=None, resolution=None, alias=None) -> str:
        return self._execute_operation(
            f"configure_{measurement_key}",
            lambda session, timeout: MeasurementEngine(session.transport).configure(
                measurement_key,
                session.modules,
                channel,
                range_value=range_value,
                resolution=resolution,
                timeout_s=timeout,
            ),
            alias=alias,
        )

    @keyword("Configure DC Voltage", tags=["rfds:configuration", "rfds:measurement", "rfds:low_risk"])
    def configure_dc_voltage(self, channel, range_value=None, resolution=None, alias=None) -> str:
        return self._configure_scalar("dc_voltage", channel, range_value, resolution, alias)

    @keyword("Configure AC Voltage", tags=["rfds:configuration", "rfds:measurement", "rfds:low_risk"])
    def configure_ac_voltage(self, channel, range_value=None, resolution=None, alias=None) -> str:
        return self._configure_scalar("ac_voltage", channel, range_value, resolution, alias)

    @keyword("Configure DC Current", tags=["rfds:configuration", "rfds:measurement", "rfds:low_risk"])
    def configure_dc_current(self, channel, range_value=None, resolution=None, alias=None) -> str:
        return self._configure_scalar("dc_current", channel, range_value, resolution, alias)

    @keyword("Configure AC Current", tags=["rfds:configuration", "rfds:measurement", "rfds:low_risk"])
    def configure_ac_current(self, channel, range_value=None, resolution=None, alias=None) -> str:
        return self._configure_scalar("ac_current", channel, range_value, resolution, alias)

    @keyword("Configure Resistance", tags=["rfds:configuration", "rfds:measurement", "rfds:medium_risk"])
    def configure_resistance(self, channel, range_value=None, resolution=None, alias=None) -> str:
        return self._configure_scalar("resistance", channel, range_value, resolution, alias)

    @keyword("Configure 4 Wire Resistance", tags=["rfds:configuration", "rfds:measurement", "rfds:medium_risk"])
    def configure_4_wire_resistance(self, channel, range_value=None, resolution=None, alias=None) -> str:
        return self._configure_scalar("four_wire_resistance", channel, range_value, resolution, alias)

    @keyword("Configure Frequency", tags=["rfds:configuration", "rfds:measurement", "rfds:low_risk"])
    def configure_frequency(self, channel, range_value=None, resolution=None, alias=None) -> str:
        return self._configure_scalar("frequency", channel, range_value, resolution, alias)

    @keyword("Configure Period", tags=["rfds:configuration", "rfds:measurement", "rfds:low_risk"])
    def configure_period(self, channel, range_value=None, resolution=None, alias=None) -> str:
        return self._configure_scalar("period", channel, range_value, resolution, alias)

    @keyword("Configure Scan List", tags=["rfds:scan", "rfds:configuration", "rfds:low_risk"])
    def configure_scan_list(self, channels, alias=None) -> list[str]:
        return self._execute_operation(
            "configure_scan_list",
            lambda session, timeout: AcquisitionEngine(session.transport).configure_scan_list(
                channels, session.modules, timeout_s=timeout
            ),
            alias=alias,
        )

    @keyword("Get Scan List", tags=["rfds:scan", "rfds:query", "rfds:low_risk"])
    def get_scan_list(self, alias=None) -> list[str]:
        return self._execute_operation(
            "get_scan_list",
            lambda session, timeout: AcquisitionEngine(session.transport).get_scan_list(timeout_s=timeout),
            alias=alias,
        )

    @keyword("Clear Scan List", tags=["rfds:scan", "rfds:configuration", "rfds:low_risk"])
    def clear_scan_list(self, alias=None) -> None:
        self._execute_operation(
            "clear_scan_list",
            lambda session, timeout: AcquisitionEngine(session.transport).clear_scan_list(timeout_s=timeout),
            alias=alias,
        )

    @keyword("Configure Trigger Source", tags=["rfds:trigger", "rfds:configuration", "rfds:low_risk"])
    def configure_trigger_source(self, source, alias=None) -> str:
        return self._execute_operation(
            "configure_trigger_source",
            lambda session, timeout: AcquisitionEngine(session.transport).set_trigger_source(source, timeout_s=timeout),
            alias=alias,
        )

    @keyword("Get Trigger Source", tags=["rfds:trigger", "rfds:query", "rfds:low_risk"])
    def get_trigger_source(self, alias=None) -> str:
        return self._execute_operation(
            "get_trigger_source",
            lambda session, timeout: AcquisitionEngine(session.transport).get_trigger_source(timeout_s=timeout),
            alias=alias,
        )

    @keyword("Set Trigger Count", tags=["rfds:trigger", "rfds:configuration", "rfds:low_risk"])
    def set_trigger_count(self, count, alias=None):
        return self._execute_operation(
            "set_trigger_count",
            lambda session, timeout: AcquisitionEngine(session.transport).set_trigger_count(count, timeout_s=timeout),
            alias=alias,
        )

    @keyword("Get Trigger Count", tags=["rfds:trigger", "rfds:query", "rfds:low_risk"])
    def get_trigger_count(self, alias=None):
        return self._execute_operation(
            "get_trigger_count",
            lambda session, timeout: AcquisitionEngine(session.transport).get_trigger_count(timeout_s=timeout),
            alias=alias,
        )

    @keyword("Set Trigger Timer", tags=["rfds:trigger", "rfds:configuration", "rfds:low_risk"])
    def set_trigger_timer(self, seconds, alias=None) -> float:
        return self._execute_operation(
            "set_trigger_timer",
            lambda session, timeout: AcquisitionEngine(session.transport).set_trigger_timer(seconds, timeout_s=timeout),
            alias=alias,
        )

    @keyword("Get Trigger Timer", tags=["rfds:trigger", "rfds:query", "rfds:low_risk"])
    def get_trigger_timer(self, alias=None) -> float:
        return self._execute_operation(
            "get_trigger_timer",
            lambda session, timeout: AcquisitionEngine(session.transport).get_trigger_timer(timeout_s=timeout),
            alias=alias,
        )

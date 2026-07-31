"""Authoritative Robot Framework keyword library for Vötsch climate chambers.

The public API follows RFDS-002 v1.1 and exposes canonical keyword names only.
Construction is hardware-independent; connections are opened explicitly.
"""

from __future__ import annotations

import math
from typing import Any

from .lifecycle import SuiteLifecycleListener
from .capabilities import get_capability_ids, get_capability_model
from .configuration import ConfigurationManager
from .converters import (
    sanitize,
    to_bool,
    to_float,
    to_int,
    to_nonnegative_seconds,
    to_positive_seconds,
)
from .diagnostics import export_diagnostics as write_diagnostics
from .diagnostics import get_diagnostics as build_diagnostics
from .exceptions import DriverError, DriverSafetyError, DriverStateError
from .models import SessionState
from .robot_compat import keyword, library, logger
from .sessions import SessionRegistry
from .version import (
    API_SPEC,
    API_SPEC_VERSION,
    API_VERSION,
    PEP440_VERSION,
    RELEASE_CLASS,
    RELEASE_VERSION,
)


@library(scope="SUITE", auto_keywords=False, version=PEP440_VERSION)
class VotschClimateChamberLibrary:
    """Suite-scoped RFDS climate-chamber driver.

    Construction is hardware-independent.  Call ``Connect`` with a TCP
    resource or an explicit ``SIM::`` resource before device-facing keywords.
    Multiple named chamber sessions are supported within one suite instance.
    """

    ROBOT_LIBRARY_DOC_FORMAT = "ROBOT"

    def __init__(
        self,
        default_resource: str | None = None,
        default_timeout_s: float | str = 5.0,
        managed_configuration_root: str | None = None,
    ) -> None:
        timeout = to_positive_seconds(default_timeout_s, "default_timeout_s")
        assert timeout is not None
        self._configuration = ConfigurationManager(managed_root=managed_configuration_root)
        default_config = self._configuration.get_default()
        if default_resource is None:
            default_resource = default_config["settings"]["connection"]["resource"]
        self._registry = SessionRegistry(default_timeout_s=timeout, default_resource=default_resource)
        self._last_progress_log_s = -math.inf
        self._suite_listener = SuiteLifecycleListener(
            self._registry,
            safe_shutdown_policy=lambda: bool(
                self._configuration.get_effective()["settings"]["safety"][
                    "safe_shutdown_on_disconnect"
                ]
            ),
        )
        self.ROBOT_LIBRARY_LISTENER = self._suite_listener

    # ------------------------------------------------------------------
    # Internal helpers; auto_keywords=False prevents accidental export.
    # ------------------------------------------------------------------

    def _handle(self, alias: str | None = None):  # type: ignore[no-untyped-def]
        return self._registry.get(alias)

    def _effective_connection_options(self, options: dict[str, Any]) -> dict[str, Any]:
        configuration = self._configuration.get_effective()
        settings = configuration["settings"]
        merged = {
            "response_timeout_s": settings["connection"]["response_timeout_s"],
            "query_retries": settings["connection"]["query_retries"],
            "retry_delay_s": settings["connection"]["retry_delay_s"],
            "tcp_keepalive": settings["connection"]["tcp_keepalive"],
            "temperature_min_c": settings["safety"]["temperature_min_c"],
            "temperature_max_c": settings["safety"]["temperature_max_c"],
            "verify_writes": settings["operation"]["verify_writes"],
            "setpoint_verify_tolerance_c": settings["operation"]["setpoint_verify_tolerance_c"],
            "setpoint_verify_timeout_s": settings["operation"]["setpoint_verify_timeout_s"],
            "setpoint_verify_poll_interval_s": settings["operation"][
                "setpoint_verify_poll_interval_s"
            ],
            "state_change_timeout_s": settings["operation"]["state_change_timeout_s"],
            "dryer_output_channel": settings["auxiliary_outputs"]["dryer_output_channel"],
            "compressed_air_output_channel": settings["auxiliary_outputs"][
                "compressed_air_output_channel"
            ],
        }
        merged.update(options)
        return merged

    def _log_progress(self, state: dict[str, Any]) -> None:
        elapsed = float(state.get("elapsed_s", 0.0))
        interval = float(
            self._configuration.get_effective()["settings"]["operation"]["progress_log_interval_s"]
        )
        stable = int(state.get("stable_count", 0))
        required = int(state.get("stable_samples", 1))
        if elapsed - self._last_progress_log_s >= interval or stable in {1, required}:
            if "remaining_s" in state:
                logger.info(
                    f"Dwell temperature {float(state['temperature_c']):.2f} °C; "
                    f"remaining {float(state['remaining_s']):.1f} s."
                )
            else:
                logger.info(
                    f"Temperature {float(state['temperature_c']):.2f} °C; "
                    f"target {float(state['target_c']):.2f} °C ± {float(state['tolerance_c']):.2f} °C; "
                    f"stable samples {stable}/{required}; elapsed {elapsed:.1f} s."
                )
            self._last_progress_log_s = elapsed


    # ------------------------------------------------------------------
    # RFDS-002 mandatory universal API.
    # ------------------------------------------------------------------

    @keyword("Connect", tags=["rfds:connection", "rfds:low_risk"])
    def connect(
        self,
        resource: str | None = None,
        alias: str = "default",
        timeout_s: float | str | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        """Connect a chamber or simulator and return a ``connection_state`` dictionary.

        ``resource`` accepts ``tcp://host:port``, ``host``, ``host:port``, or
        ``SIM::<profile>``.  Connection is idempotent for the same alias and
        normalized resource.  Functional chamber state is not changed.
        """
        timeout = None if timeout_s is None else to_positive_seconds(timeout_s, "timeout_s")
        merged = self._effective_connection_options(options)
        handle = self._registry.connect(resource, alias=alias, timeout_s=timeout, options=merged)
        logger.info(f"Connected alias={handle.record.alias} resource={handle.record.resource}.")
        return sanitize(handle.record.to_robot_dict())

    @keyword("Disconnect", tags=["rfds:connection", "rfds:high_risk"])
    def disconnect(self, alias: str | None = None) -> None:
        """Apply the configured safe state, close the session, and release resources.

        The operation is idempotent.  It is bounded by a 20 s cleanup budget.
        """
        policy = self._configuration.get_effective()["settings"]["safety"]["safe_shutdown_on_disconnect"]
        self._registry.disconnect(alias, safe_shutdown=bool(policy), timeout_s=20.0)

    @keyword("Is Connected", tags=["rfds:connection", "rfds:none_risk"])
    def is_connected(self, alias: str | None = None) -> bool:
        """Return cached transport state without device I/O."""
        try:
            return bool(self._registry.get(alias, require_connected=False).core.is_connected)
        except DriverError:
            return False

    @keyword("Get Connection State", tags=["rfds:connection", "rfds:none_risk"])
    def get_connection_state(self, alias: str | None = None, refresh: bool | str = False) -> dict[str, Any]:
        """Return stable connection-state fields; optionally perform a safe live probe."""
        state = self._registry.state_for(alias)
        if to_bool(refresh, "refresh") and state["connected"]:
            try:
                ok = self._registry.get(alias).core.check_communication()
                state["communication_ok"] = ok
            except DriverError as exc:
                state["communication_ok"] = False
                state["last_error"] = exc.to_dict()
                raise
        return sanitize(state)

    @keyword("Check Communication", tags=["rfds:connection", "rfds:none_risk"])
    def check_communication(self, alias: str | None = None) -> bool:
        """Perform a bounded non-destructive chamber-status query and return ``True``."""
        return self._handle(alias).core.check_communication()

    @keyword("Get Identity", tags=["rfds:identity", "rfds:none_risk"])
    def get_identity(self, alias: str | None = None, refresh: bool | str = False) -> str:
        """Return cached connection identity by default; ``refresh=True`` queries the chamber."""
        return self._handle(alias).core.read_identity(refresh=to_bool(refresh, "refresh")).identity

    @keyword("Get Driver Information", tags=["rfds:metadata", "rfds:none_risk"])
    def get_driver_information(self) -> dict[str, Any]:
        """Return static driver metadata without device I/O."""
        return {
            "name": "rf_votsch_climate_chamber",
            "package_version": RELEASE_VERSION,
            "api_version": API_VERSION,
            "api_spec": API_SPEC,
            "api_spec_version": API_SPEC_VERSION,
            "robot_framework_min_version": "7.0",
            "python_min_version": "3.11",
            "library_scope": "SUITE",
            "transport_types": ["tcp", "simulator"],
            "capability_ids": get_capability_ids(),
            "simulation_supported": True,
            "identity_source": "device_query",
            "release_class": RELEASE_CLASS,
            "rfds_core_version": None,
            "rfds_core_version_status": "UNAVAILABLE",
        }

    @keyword("Get Driver Capabilities", tags=["rfds:metadata", "rfds:none_risk"])
    def get_driver_capabilities(self) -> list[str]:
        """Return the sorted RFDS-002 capability identifiers."""
        return get_capability_ids()

    @keyword("Set Communication Timeout", tags=["rfds:connection", "rfds:low_risk"])
    def set_communication_timeout(self, timeout_s: float | str, alias: str | None = None) -> float:
        """Apply a finite positive communication timeout and return seconds."""
        value = to_positive_seconds(timeout_s, "timeout_s")
        assert value is not None
        if alias is None and self._registry.active_alias is None:
            self._registry.default_timeout_s = value
            return value
        handle = self._handle(alias)
        applied = handle.core.set_timeout(value)
        handle.record.timeout_s = applied
        return applied

    @keyword("Get Communication Timeout", tags=["rfds:connection", "rfds:none_risk"])
    def get_communication_timeout(self, alias: str | None = None) -> float:
        """Return the selected session timeout or the unconnected driver default."""
        if alias is None and self._registry.active_alias is None:
            return float(self._registry.default_timeout_s)
        return self._handle(alias).core.get_timeout()

    # ------------------------------------------------------------------
    # Multi-connection capability.
    # ------------------------------------------------------------------

    @keyword("List Connections", tags=["rfds:connection", "rfds:none_risk"])
    def list_connections(self) -> list[dict[str, Any]]:
        return sanitize(self._registry.list_states())

    @keyword("Select Connection", tags=["rfds:connection", "rfds:low_risk"])
    def select_connection(self, alias: str) -> dict[str, Any]:
        return sanitize(self._registry.select(alias))

    @keyword("Disconnect All", tags=["rfds:connection", "rfds:high_risk"])
    def disconnect_all(self) -> None:
        policy = self._configuration.get_effective()["settings"]["safety"][
            "safe_shutdown_on_disconnect"
        ]
        self._registry.disconnect_all(safe_shutdown=bool(policy), timeout_s=20.0)

    @keyword("Get Active Connection", tags=["rfds:connection", "rfds:none_risk"])
    def get_active_connection(self) -> str | None:
        return self._registry.active_alias

    @keyword("Reconnect", tags=["rfds:connection", "rfds:low_risk"])
    def reconnect(self, alias: str | None = None) -> dict[str, Any]:
        handle = self._handle(alias)
        identity = handle.core.reconnect()
        handle.record.communication_ok = True
        handle.record.identity = identity
        handle.record.state = SessionState.CONNECTED
        return sanitize(handle.record.to_robot_dict())

    # ------------------------------------------------------------------
    # Temperature source, measurement, operation, and auxiliary outputs.
    # ------------------------------------------------------------------

    @keyword("Set Temperature", tags=["rfds:temperature_control", "rfds:high_risk"])
    def set_temperature(self, value_c: float, alias: str | None = None) -> None:
        self._handle(alias).core.set_temperature_c(to_float(value_c, "value_c"))

    @keyword("Get Temperature Setpoint", tags=["rfds:temperature_control", "rfds:none_risk"])
    def get_temperature_setpoint(self, alias: str | None = None) -> float:
        return self._handle(alias).core.get_temperature_setpoint_c()

    @keyword("Get Temperature Limits", tags=["rfds:temperature_control", "rfds:none_risk"])
    def get_temperature_limits(self, alias: str | None = None) -> dict[str, Any]:
        return self._handle(alias).core.get_temperature_limits()

    @keyword("Set Temperature Limits", tags=["rfds:temperature_control", "rfds:low_risk"])
    def set_temperature_limits(self, minimum_c: float, maximum_c: float, alias: str | None = None) -> dict[str, Any]:
        return self._handle(alias).core.set_temperature_limits(minimum_c, maximum_c)

    @keyword("Measure Temperature", tags=["rfds:temperature_measurement", "rfds:none_risk"])
    def measure_temperature(self, alias: str | None = None) -> float:
        """Trigger a live chamber temperature query and return degrees Celsius."""
        return self._handle(alias).core.measure_temperature_c()

    @keyword("Start Chamber", tags=["rfds:operation", "rfds:high_risk"])
    def start_chamber(self, alias: str | None = None) -> None:
        self._handle(alias).core.start()

    @keyword("Stop Chamber", tags=["rfds:operation", "rfds:high_risk"])
    def stop_chamber(self, alias: str | None = None) -> None:
        self._handle(alias).core.stop()

    @keyword("Get Chamber Running State", tags=["rfds:operation", "rfds:none_risk"])
    def get_chamber_running_state(self, alias: str | None = None) -> bool:
        return self._handle(alias).core.get_running()

    @keyword("Set Temperature And Wait", tags=["rfds:temperature_control", "rfds:high_risk", "rfds:long_running"])
    def set_temperature_and_wait(
        self,
        value_c: float,
        dwell_s: float | str = 0.0,
        tolerance_c: float = 0.8,
        poll_interval_s: float | str = 10.0,
        settle_timeout_s: float | str = 14_400.0,
        stable_samples: int = 3,
        start_chamber: bool | str = True,
        alias: str | None = None,
    ) -> float:
        dwell = to_nonnegative_seconds(dwell_s, "dwell_s")
        poll = to_positive_seconds(poll_interval_s, "poll_interval_s")
        timeout = to_positive_seconds(settle_timeout_s, "settle_timeout_s")
        assert poll is not None and timeout is not None
        self._last_progress_log_s = -math.inf
        return self._handle(alias).core.set_temperature_and_wait(
            to_float(value_c, "value_c"),
            dwell_s=dwell,
            tolerance_c=to_float(tolerance_c, "tolerance_c"),
            poll_interval_s=poll,
            settle_timeout_s=timeout,
            stable_samples=to_int(stable_samples, "stable_samples", minimum=1),
            start_chamber=to_bool(start_chamber, "start_chamber"),
            progress=self._log_progress,
        )

    @keyword("Wait For Temperature Stability", tags=["rfds:temperature_measurement", "rfds:high_risk", "rfds:long_running"])
    def wait_for_temperature_stability(
        self,
        target_c: float | None = None,
        tolerance_c: float = 0.8,
        stable_samples: int = 3,
        poll_interval_s: float | str = 10.0,
        settle_timeout_s: float | str = 14_400.0,
        alias: str | None = None,
    ) -> float:
        handle = self._handle(alias)
        target = handle.core.get_temperature_setpoint_c() if target_c is None else to_float(target_c, "target_c")
        poll = to_positive_seconds(poll_interval_s, "poll_interval_s")
        timeout = to_positive_seconds(settle_timeout_s, "settle_timeout_s")
        assert poll is not None and timeout is not None
        self._last_progress_log_s = -math.inf
        return handle.core.wait_for_temperature(
            target,
            tolerance_c=to_float(tolerance_c, "tolerance_c"),
            stable_samples=to_int(stable_samples, "stable_samples", minimum=1),
            poll_interval_s=poll,
            settle_timeout_s=timeout,
            progress=self._log_progress,
        )

    @keyword("Wait For Dwell", tags=["rfds:temperature_measurement", "rfds:medium_risk", "rfds:long_running"])
    def wait_for_dwell(
        self,
        duration_s: float | str,
        poll_interval_s: float | str = 60.0,
        alias: str | None = None,
    ) -> float:
        duration = to_nonnegative_seconds(duration_s, "duration_s")
        poll = to_positive_seconds(poll_interval_s, "poll_interval_s")
        assert poll is not None
        self._last_progress_log_s = -math.inf
        return self._handle(alias).core.dwell(duration, poll_interval_s=poll, progress=self._log_progress)

    @keyword("Cancel Current Operation", tags=["rfds:operation", "rfds:high_risk"])
    def cancel_current_operation(self, alias: str | None = None) -> None:
        self._handle(alias).core.cancel()

    @keyword("Set Heating Gradient", tags=["rfds:temperature_control", "rfds:medium_risk"])
    def set_heating_gradient(self, value_c_per_min: float, alias: str | None = None) -> None:
        self._handle(alias).core.set_heating_gradient_c_per_min(value_c_per_min)

    @keyword("Get Heating Gradient", tags=["rfds:temperature_control", "rfds:none_risk"])
    def get_heating_gradient(self, alias: str | None = None) -> float:
        return self._handle(alias).core.get_heating_gradient_c_per_min()

    @keyword("Set Cooling Gradient", tags=["rfds:temperature_control", "rfds:medium_risk"])
    def set_cooling_gradient(self, value_c_per_min: float, alias: str | None = None) -> None:
        self._handle(alias).core.set_cooling_gradient_c_per_min(value_c_per_min)

    @keyword("Get Cooling Gradient", tags=["rfds:temperature_control", "rfds:none_risk"])
    def get_cooling_gradient(self, alias: str | None = None) -> float:
        return self._handle(alias).core.get_cooling_gradient_c_per_min()

    @keyword("Set Dryer", tags=["rfds:digital_io", "rfds:medium_risk"])
    def set_dryer(self, enabled: bool | str, alias: str | None = None) -> None:
        """Set the dryer output using the explicitly configured physical channel.

        Real hardware defaults to unsupported until ``dryer_output_channel`` is
        supplied through configuration or ``Connect`` options.
        """
        self._handle(alias).core.set_dryer(to_bool(enabled, "enabled"))

    @keyword("Get Dryer", tags=["rfds:digital_io", "rfds:none_risk"])
    def get_dryer(self, alias: str | None = None) -> bool:
        """Read the configured dryer output; fail if no mapping was qualified."""
        return self._handle(alias).core.get_dryer()

    @keyword("Set Compressed Air", tags=["rfds:digital_io", "rfds:medium_risk"])
    def set_compressed_air(self, enabled: bool | str, alias: str | None = None) -> None:
        """Set compressed air using the explicitly configured physical channel."""
        self._handle(alias).core.set_compressed_air(to_bool(enabled, "enabled"))

    @keyword("Get Compressed Air", tags=["rfds:digital_io", "rfds:none_risk"])
    def get_compressed_air(self, alias: str | None = None) -> bool:
        """Read compressed air; fail if no physical channel mapping was qualified."""
        return self._handle(alias).core.get_compressed_air()

    @keyword("Get Chamber Status", tags=["rfds:diagnostics", "rfds:none_risk"])
    def get_chamber_status(self, alias: str | None = None) -> str:
        return self._handle(alias).core.get_status()

    @keyword("Safe Shutdown", tags=["rfds:safe_shutdown", "rfds:high_risk"])
    def safe_shutdown(self, alias: str | None = None, timeout_s: float | str | None = None) -> dict[str, Any]:
        """Stop the chamber and disable only configured auxiliary outputs.

        Unqualified dryer and compressed-air mappings are recorded as ``SKIP``
        rather than transmitted to an unknown digital-output channel.
        """
        timeout = None if timeout_s is None else to_positive_seconds(timeout_s, "timeout_s")
        return sanitize(self._handle(alias).core.safe_shutdown(timeout_s=timeout))

    # ------------------------------------------------------------------
    # Assertions.
    # ------------------------------------------------------------------

    @keyword("Temperature Should Be", tags=["rfds:assertion", "rfds:none_risk"])
    def temperature_should_be(self, expected_c: float, tolerance_c: float = 0.1, alias: str | None = None) -> None:
        actual = self.measure_temperature(alias)
        expected = to_float(expected_c, "expected_c")
        tolerance = to_float(tolerance_c, "tolerance_c")
        if abs(actual - expected) > tolerance:
            raise AssertionError(f"Temperature {actual:.3f} °C is not {expected:.3f} °C ± {tolerance:.3f} °C.")

    @keyword("Temperature Should Be Within", tags=["rfds:assertion", "rfds:none_risk"])
    def temperature_should_be_within(self, minimum_c: float, maximum_c: float, alias: str | None = None) -> None:
        actual = self.measure_temperature(alias)
        minimum = to_float(minimum_c, "minimum_c")
        maximum = to_float(maximum_c, "maximum_c")
        if not minimum <= actual <= maximum:
            raise AssertionError(f"Temperature {actual:.3f} °C is outside [{minimum:.3f}, {maximum:.3f}] °C.")

    @keyword("Temperature Setpoint Should Be", tags=["rfds:assertion", "rfds:none_risk"])
    def temperature_setpoint_should_be(self, expected_c: float, tolerance_c: float = 0.05, alias: str | None = None) -> None:
        actual = self.get_temperature_setpoint(alias)
        expected = to_float(expected_c, "expected_c")
        tolerance = to_float(tolerance_c, "tolerance_c")
        if abs(actual - expected) > tolerance:
            raise AssertionError(f"Setpoint {actual:.3f} °C is not {expected:.3f} °C ± {tolerance:.3f} °C.")

    @keyword("Chamber Should Be Running", tags=["rfds:assertion", "rfds:none_risk"])
    def chamber_should_be_running(self, alias: str | None = None) -> None:
        if not self.get_chamber_running_state(alias):
            raise AssertionError("Climate chamber is not running.")

    @keyword("Chamber Should Be Stopped", tags=["rfds:assertion", "rfds:none_risk"])
    def chamber_should_be_stopped(self, alias: str | None = None) -> None:
        if self.get_chamber_running_state(alias):
            raise AssertionError("Climate chamber is running.")

    @keyword("Connection Should Be Available", tags=["rfds:assertion", "rfds:none_risk"])
    def connection_should_be_available(self, alias: str | None = None) -> None:
        if not self.check_communication(alias):
            raise AssertionError("Communication check did not succeed.")

    # ------------------------------------------------------------------
    # Diagnostics, capability projection, and RFDS-014 configuration API.
    # ------------------------------------------------------------------

    @keyword("Get Diagnostics", tags=["rfds:diagnostics", "rfds:none_risk"])
    def get_diagnostics(self) -> dict[str, Any]:
        return sanitize(build_diagnostics(self._registry))

    @keyword("Export Diagnostics", tags=["rfds:diagnostics", "rfds:low_risk"])
    def export_diagnostics(self, destination: str) -> dict[str, Any]:
        return write_diagnostics(self._registry, destination)

    @keyword("Get Capability Model", tags=["rfds:metadata", "rfds:none_risk"])
    def get_capability_model(self) -> list[dict[str, Any]]:
        return get_capability_model()

    @keyword("Get Driver Configuration Schema", tags=["rfds:configuration", "rfds:none_risk"])
    def get_driver_configuration_schema(self) -> dict[str, Any]:
        return self._configuration.get_schema()

    @keyword("Get Driver Default Configuration", tags=["rfds:configuration", "rfds:none_risk"])
    def get_driver_default_configuration(self, redact_sensitive: bool | str = True) -> dict[str, Any]:
        del redact_sensitive
        return self._configuration.get_default()

    @keyword("Get Driver Configuration", tags=["rfds:configuration", "rfds:none_risk"])
    def get_driver_configuration(
        self,
        scope: str = "EFFECTIVE",
        alias: str | None = None,
        redact_sensitive: bool | str = True,
        include_sources: bool | str = False,
    ) -> dict[str, Any]:
        del alias, redact_sensitive
        if str(scope).upper() != "EFFECTIVE":
            raise DriverStateError("only EFFECTIVE configuration scope is implemented", operation="Get Driver Configuration")
        return self._configuration.get_effective(include_sources=to_bool(include_sources, "include_sources"))

    @keyword("Validate Driver Configuration", tags=["rfds:configuration", "rfds:none_risk"])
    def validate_driver_configuration(
        self,
        configuration: Any,
        mode: str = "REPLACE",
        strict: bool | str = True,
        alias: str | None = None,
    ) -> dict[str, Any]:
        del alias
        if str(mode).upper() != "REPLACE":
            raise DriverStateError("only REPLACE configuration mode is implemented", operation="Validate Driver Configuration")
        return sanitize(self._configuration.validate(configuration, strict=to_bool(strict, "strict")))

    @keyword("Import Driver Configuration", tags=["rfds:configuration", "rfds:medium_risk"])
    def import_driver_configuration(
        self,
        source: Any,
        mode: str = "REPLACE",
        apply: bool | str = False,
        persist: bool | str = False,
        profile_name: str | None = None,
        strict: bool | str = True,
        reconnect: bool | str = False,
        allow_device_persistent_changes: bool | str = False,
        confirm_high_risk: bool | str = False,
        alias: str | None = None,
    ) -> dict[str, Any]:
        del reconnect, allow_device_persistent_changes, confirm_high_risk, alias
        if str(mode).upper() != "REPLACE":
            raise DriverStateError("only REPLACE configuration mode is implemented", operation="Import Driver Configuration")
        return sanitize(
            self._configuration.import_configuration(
                source,
                apply=to_bool(apply, "apply"),
                persist=to_bool(persist, "persist"),
                profile_name=profile_name,
                strict=to_bool(strict, "strict"),
            )
        )

    @keyword("Export Driver Configuration", tags=["rfds:configuration", "rfds:low_risk"])
    def export_driver_configuration(
        self,
        destination: str | None = None,
        scope: str = "EFFECTIVE",
        profile_name: str | None = None,
        overwrite: bool | str = False,
        alias: str | None = None,
    ) -> dict[str, Any]:
        del profile_name, alias
        if str(scope).upper() != "EFFECTIVE":
            raise DriverStateError("only EFFECTIVE configuration scope is implemented", operation="Export Driver Configuration")
        return sanitize(self._configuration.export_configuration(destination, overwrite=to_bool(overwrite, "overwrite")))

    @keyword("Save Driver Configuration", tags=["rfds:configuration", "rfds:low_risk"])
    def save_driver_configuration(
        self,
        profile_name: str,
        scope: str = "EFFECTIVE",
        overwrite: bool | str = False,
        set_active: bool | str = False,
        alias: str | None = None,
    ) -> dict[str, Any]:
        del alias
        if str(scope).upper() != "EFFECTIVE":
            raise DriverStateError("only EFFECTIVE configuration scope is implemented", operation="Save Driver Configuration")
        return self._configuration.save_profile(
            profile_name,
            overwrite=to_bool(overwrite, "overwrite"),
            set_active=to_bool(set_active, "set_active"),
        )

    @keyword("Load Driver Configuration", tags=["rfds:configuration", "rfds:low_risk"])
    def load_driver_configuration(
        self,
        profile_name: str,
        apply: bool | str = False,
        reconnect: bool | str = False,
        alias: str | None = None,
    ) -> dict[str, Any]:
        del reconnect, alias
        return sanitize(self._configuration.load_profile(profile_name, apply=to_bool(apply, "apply")))

    @keyword("List Driver Configuration Profiles", tags=["rfds:configuration", "rfds:none_risk"])
    def list_driver_configuration_profiles(self) -> list[dict[str, Any]]:
        return self._configuration.list_profiles()

    @keyword("Delete Driver Configuration Profile", tags=["rfds:configuration", "rfds:destructive"])
    def delete_driver_configuration_profile(self, profile_name: str, confirm: bool | str = False) -> dict[str, Any]:
        return self._configuration.delete_profile(profile_name, confirm=to_bool(confirm, "confirm"))

    @keyword("Reset Driver Configuration", tags=["rfds:configuration", "rfds:medium_risk"])
    def reset_driver_configuration(
        self,
        path: str | None = None,
        scope: str = "INSTANCE_OVERRIDE",
        apply: bool | str = False,
        persist: bool | str = False,
        confirm: bool | str = False,
        alias: str | None = None,
    ) -> dict[str, Any]:
        del path, scope, persist, alias
        if to_bool(apply, "apply") and not to_bool(confirm, "confirm"):
            raise DriverSafetyError("confirm=True is required when applying a configuration reset", operation="Reset Driver Configuration")
        return self._configuration.reset(apply=to_bool(apply, "apply"))

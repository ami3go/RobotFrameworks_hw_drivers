"""Robot Framework library for the NGI N83624 24-channel cell simulator.

The library wraps the typed :mod:`ngi_n83624` Python driver and adds Robot-specific
session management, input conversion, output arming, audit logging, assertions, and
safe teardown.
"""

from __future__ import annotations

import json
import math
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from robot.api import logger
from robot.api.deco import keyword, library

from ngi_n83624 import (
    CaptureRate,
    ChannelLimits,
    CurrentRange,
    DriverSafetyPolicy,
    HeartbeatConfig,
    InstrumentLimits,
    N83624CellSimulator,
    OutputMode,
    SequenceStep,
    SocStep,
)
from ngi_n83624.emulator import SimpleN83624Emulator
from ngi_n83624.exceptions import SafetyError, SessionStateError, ValidationError

RELEASE_VERSION = "26.01"
OUTPUT_CONFIRMATION = "ENABLE OUTPUT"
RAW_SCPI_CONFIRMATION = "ENABLE RAW SCPI"


@dataclass
class _Session:
    alias: str
    driver: N83624CellSimulator
    safe_shutdown: bool
    allow_raw_scpi: bool
    audit_log_path: Path | None
    armed_channels: set[int]
    emulator: SimpleN83624Emulator | None = None


@library(scope="GLOBAL", version=RELEASE_VERSION, auto_keywords=False)
class NGI_N83624:
    """Robot Framework keyword library for NGI N83624 instruments.

    The library supports multiple named sessions. Real connections start with all
    output channels *disarmed*. Before enabling a channel, configure finite voltage
    and current limits and call ``Arm Channel Output`` with the exact confirmation
    text ``ENABLE OUTPUT``.

    ``safe_shutdown`` defaults to true. Closing a session then attempts to disable
    every channel even if one channel command fails, closes the transport, and clears
    the output arming state.
    """

    ROBOT_LIBRARY_LISTENER = None

    def __init__(
        self,
        default_host: str = "192.168.0.123",
        default_port: int = 7000,
        default_timeout: float = 3.0,
        auto_close_on_suite_end: bool = True,
    ) -> None:
        self.default_host = str(default_host)
        self.default_port = self._as_int(default_port, "default_port")
        self.default_timeout = self._as_float(default_timeout, "default_timeout")
        self.auto_close_on_suite_end = self._as_bool(auto_close_on_suite_end)
        self._sessions: dict[str, _Session] = {}
        self._active_alias: str | None = None
        self.ROBOT_LIBRARY_LISTENER = self
        self.ROBOT_LISTENER_API_VERSION = 2

    # Robot listener -------------------------------------------------------------
    def _end_suite(self, name: str, attributes: Mapping[str, Any]) -> None:
        if self.auto_close_on_suite_end:
            try:
                self.close_all_n83624_connections()
            except Exception as exc:  # listener cleanup must not hide test failures
                logger.error(f"Automatic N83624 suite cleanup failed: {exc}")

    def _close(self) -> None:
        try:
            self.close_all_n83624_connections()
        except Exception as exc:
            logger.error(f"Automatic N83624 library cleanup failed: {exc}")

    # Connection management -----------------------------------------------------
    @keyword("Open N83624 TCP Connection")
    def open_n83624_tcp_connection(
        self,
        alias: str = "default",
        host: str | None = None,
        port: int | str | None = None,
        timeout: float | str | None = None,
        max_voltage_v: float | str | None = None,
        max_current_ma: float | str | None = None,
        max_resistance_mohm: float | str | None = None,
        max_power_mw: float | str | None = None,
        safe_shutdown: bool | str = True,
        verify_identity: bool | str = True,
        allow_raw_scpi: bool | str = False,
        audit_log_path: str | None = None,
    ) -> str:
        """Open a TCP session and make it active.

        The documented N83624 defaults are host ``192.168.0.123`` and port ``7000``.
        Hardware-specific voltage/current limits should be supplied before output use.
        """
        host = host or self.default_host
        port_value = self.default_port if port is None else self._as_int(port, "port")
        timeout_value = self.default_timeout if timeout is None else self._as_float(timeout, "timeout")
        limits = self._make_limits(max_voltage_v, max_current_ma, max_resistance_mohm, max_power_mw)
        policy = self._make_policy(safe_shutdown, verify_identity)
        driver = N83624CellSimulator.tcp(
            host=str(host),
            port=port_value,
            timeout=timeout_value,
            limits=limits,
            safety_policy=policy,
        )
        return self._register_and_connect(
            alias,
            driver,
            safe_shutdown=safe_shutdown,
            allow_raw_scpi=allow_raw_scpi,
            audit_log_path=audit_log_path,
        )

    @keyword("Open N83624 UDP Connection")
    def open_n83624_udp_connection(
        self,
        alias: str = "default",
        host: str | None = None,
        port: int | str = 7000,
        timeout: float | str | None = None,
        max_voltage_v: float | str | None = None,
        max_current_ma: float | str | None = None,
        safe_shutdown: bool | str = True,
        verify_identity: bool | str = True,
        allow_raw_scpi: bool | str = False,
        audit_log_path: str | None = None,
    ) -> str:
        """Open a UDP session. Prefer TCP for safety-critical control."""
        host = host or self.default_host
        timeout_value = self.default_timeout if timeout is None else self._as_float(timeout, "timeout")
        limits = self._make_limits(max_voltage_v, max_current_ma, None, None)
        policy = self._make_policy(safe_shutdown, verify_identity)
        driver = N83624CellSimulator.udp(
            host=str(host),
            port=self._as_int(port, "port"),
            timeout=timeout_value,
            limits=limits,
            safety_policy=policy,
        )
        return self._register_and_connect(
            alias,
            driver,
            safe_shutdown=safe_shutdown,
            allow_raw_scpi=allow_raw_scpi,
            audit_log_path=audit_log_path,
        )

    @keyword("Open N83624 Channel UDP Connection")
    def open_n83624_channel_udp_connection(
        self,
        alias: str,
        host: str,
        channel: int | str,
        timeout: float | str | None = None,
        max_voltage_v: float | str | None = None,
        max_current_ma: float | str | None = None,
        safe_shutdown: bool | str = True,
        verify_identity: bool | str = True,
        allow_raw_scpi: bool | str = False,
        audit_log_path: str | None = None,
    ) -> str:
        """Open channel-specific UDP port 7001..7024."""
        channel_value = self._channel(channel)
        timeout_value = self.default_timeout if timeout is None else self._as_float(timeout, "timeout")
        limits = self._make_limits(max_voltage_v, max_current_ma, None, None)
        policy = self._make_policy(safe_shutdown, verify_identity)
        driver = N83624CellSimulator.udp_channel(
            host=str(host),
            channel=channel_value,
            timeout=timeout_value,
            limits=limits,
            safety_policy=policy,
        )
        return self._register_and_connect(
            alias,
            driver,
            safe_shutdown=safe_shutdown,
            allow_raw_scpi=allow_raw_scpi,
            audit_log_path=audit_log_path,
        )

    @keyword("Open N83624 Serial Connection")
    def open_n83624_serial_connection(
        self,
        alias: str,
        serial_port: str,
        baudrate: int | str = 115200,
        timeout: float | str | None = None,
        max_voltage_v: float | str | None = None,
        max_current_ma: float | str | None = None,
        safe_shutdown: bool | str = True,
        verify_identity: bool | str = True,
        allow_raw_scpi: bool | str = False,
        audit_log_path: str | None = None,
    ) -> str:
        """Open an RS232 session."""
        timeout_value = self.default_timeout if timeout is None else self._as_float(timeout, "timeout")
        limits = self._make_limits(max_voltage_v, max_current_ma, None, None)
        policy = self._make_policy(safe_shutdown, verify_identity)
        driver = N83624CellSimulator.serial(
            port=str(serial_port),
            baudrate=self._as_int(baudrate, "baudrate"),
            timeout=timeout_value,
            limits=limits,
            safety_policy=policy,
        )
        return self._register_and_connect(
            alias,
            driver,
            safe_shutdown=safe_shutdown,
            allow_raw_scpi=allow_raw_scpi,
            audit_log_path=audit_log_path,
        )

    @keyword("Open N83624 Emulator")
    def open_n83624_emulator(
        self,
        alias: str = "emulator",
        max_voltage_v: float | str = 5.0,
        max_current_ma: float | str = 1000.0,
        safe_shutdown: bool | str = True,
        allow_raw_scpi: bool | str = True,
        audit_log_path: str | None = None,
    ) -> str:
        """Open the deterministic in-process emulator for tests and examples."""
        emulator = SimpleN83624Emulator()
        limits = self._make_limits(max_voltage_v, max_current_ma, 1_000_000.0, 10_000.0)
        policy = self._make_policy(safe_shutdown, True)
        driver = N83624CellSimulator(emulator, limits=limits, safety_policy=policy)
        return self._register_and_connect(
            alias,
            driver,
            safe_shutdown=safe_shutdown,
            allow_raw_scpi=allow_raw_scpi,
            audit_log_path=audit_log_path,
            emulator=emulator,
        )

    @keyword("Switch N83624 Connection")
    def switch_n83624_connection(self, alias: str) -> str:
        """Select the active named session."""
        normalized = self._normalize_alias(alias)
        if normalized not in self._sessions:
            raise SessionStateError(f"Unknown N83624 connection alias: {alias!r}")
        self._active_alias = normalized
        self._audit("switch_connection", alias=normalized)
        return normalized

    @keyword("Get Active N83624 Connection")
    def get_active_n83624_connection(self) -> str:
        """Return the active alias."""
        return self._session().alias

    @keyword("List N83624 Connections")
    def list_n83624_connections(self) -> list[str]:
        """Return all open aliases."""
        return sorted(self._sessions)

    @keyword("Close N83624 Connection")
    def close_n83624_connection(self, alias: str | None = None) -> None:
        """Safely close one session and remove it from the registry."""
        session = self._session(alias)
        error: BaseException | None = None
        try:
            if session.safe_shutdown and session.driver.transport.is_open():
                try:
                    session.driver.all_outputs_off()
                except BaseException as exc:
                    error = exc
                    logger.error(f"N83624 output-off cleanup for {session.alias!r} reported: {exc}")
            session.armed_channels.clear()
            try:
                session.driver.close()
            except BaseException as exc:
                error = error or exc
        finally:
            self._audit_for(session, "close_connection", error=str(error) if error else None)
            self._sessions.pop(session.alias, None)
            if self._active_alias == session.alias:
                self._active_alias = next(iter(self._sessions), None)
        if error is not None:
            raise error

    @keyword("Close All N83624 Connections")
    def close_all_n83624_connections(self) -> None:
        """Close all sessions, attempting every session even after failures."""
        errors: list[str] = []
        for alias in list(self._sessions):
            try:
                self.close_n83624_connection(alias)
            except Exception as exc:
                errors.append(f"{alias}: {type(exc).__name__}: {exc}")
        if errors:
            raise SafetyError("One or more N83624 sessions failed safe close: " + "; ".join(errors))

    @keyword("Identify N83624")
    def identify_n83624(self, alias: str | None = None) -> str:
        """Return ``*IDN?`` response."""
        session = self._session(alias)
        value = session.driver.identify()
        self._audit_for(session, "identify", response=value)
        return value

    # Safety configuration -------------------------------------------------------
    @keyword("Set Channel Safety Limits")
    def set_channel_safety_limits(
        self,
        channel: int | str,
        max_voltage_v: float | str,
        max_current_ma: float | str,
        max_resistance_mohm: float | str | None = None,
        max_power_mw: float | str | None = None,
        max_runtime_s: float | str | None = None,
        max_capacity_mah: float | str | None = None,
        alias: str | None = None,
    ) -> dict[str, Any]:
        """Set finite software limits for one channel.

        Existing default limits remain unchanged. The new per-channel limits replace
        any previous per-channel entry.
        """
        session = self._session(alias)
        channel_value = self._channel(channel)
        limits = ChannelLimits(
            max_voltage_v=self._as_float(max_voltage_v, "max_voltage_v"),
            max_current_ma=self._as_float(max_current_ma, "max_current_ma"),
            max_resistance_mohm=self._optional_float(max_resistance_mohm, "max_resistance_mohm"),
            max_power_mw=self._optional_float(max_power_mw, "max_power_mw"),
            max_runtime_s=self._optional_float(max_runtime_s, "max_runtime_s"),
            max_capacity_mah=self._optional_float(max_capacity_mah, "max_capacity_mah"),
        )
        channel_limits = dict(session.driver.limits.channel_limits)
        channel_limits[channel_value] = limits
        session.driver.limits = replace(session.driver.limits, channel_limits=channel_limits)
        session.armed_channels.discard(channel_value)
        result = self._to_robot(limits)
        self._audit_for(session, "set_channel_limits", channel=channel_value, limits=result)
        return result

    @keyword("Get Channel Safety Limits")
    def get_channel_safety_limits(self, channel: int | str, alias: str | None = None) -> dict[str, Any]:
        """Return effective channel limits as a dictionary."""
        session = self._session(alias)
        return self._to_robot(session.driver.limits.for_channel(self._channel(channel)))

    @keyword("Arm Channel Output")
    def arm_channel_output(
        self,
        channel: int | str,
        confirmation: str = OUTPUT_CONFIRMATION,
        alias: str | None = None,
    ) -> None:
        """Arm one channel for output enable.

        ``confirmation`` must equal ``ENABLE OUTPUT`` exactly and the channel must
        have finite maximum voltage and current limits.
        """
        session = self._session(alias)
        channel_value = self._channel(channel)
        if confirmation != OUTPUT_CONFIRMATION:
            raise SafetyError(f"Output arming requires exact confirmation text: {OUTPUT_CONFIRMATION}")
        limits = session.driver.limits.for_channel(channel_value)
        if not limits.has_output_enable_limits():
            raise SafetyError(
                f"Channel {channel_value} cannot be armed without finite max_voltage_v and max_current_ma"
            )
        session.armed_channels.add(channel_value)
        self._audit_for(session, "arm_output", channel=channel_value)

    @keyword("Disarm Channel Output")
    def disarm_channel_output(self, channel: int | str, alias: str | None = None) -> None:
        """Remove output enable permission for one channel."""
        session = self._session(alias)
        channel_value = self._channel(channel)
        session.armed_channels.discard(channel_value)
        self._audit_for(session, "disarm_output", channel=channel_value)

    @keyword("Disarm All Channel Outputs")
    def disarm_all_channel_outputs(self, alias: str | None = None) -> None:
        """Remove output enable permission from all channels."""
        session = self._session(alias)
        session.armed_channels.clear()
        self._audit_for(session, "disarm_all_outputs")

    @keyword("Channel Output Should Be Armed")
    def channel_output_should_be_armed(self, channel: int | str, alias: str | None = None) -> None:
        """Fail unless the channel is armed."""
        session = self._session(alias)
        channel_value = self._channel(channel)
        if channel_value not in session.armed_channels:
            raise AssertionError(f"N83624 channel {channel_value} is not armed")

    # Output and configuration ---------------------------------------------------
    @keyword("Set Channel Mode")
    def set_channel_mode(
        self,
        channel: int | str,
        mode: str | int,
        output_off_first: bool | str = True,
        verify: bool | str = True,
        alias: str | None = None,
    ) -> str:
        """Set SOURCE, CHARGE, SOC, or SEQUENCE mode."""
        session = self._session(alias)
        mode_value = self._enum(OutputMode, mode, "mode")
        session.driver.channel(self._channel(channel)).set_mode(
            mode_value,
            output_off_first=self._as_bool(output_off_first),
            verify=self._as_bool(verify),
        )
        self._audit_for(session, "set_mode", channel=self._channel(channel), mode=mode_value.name)
        return mode_value.name

    @keyword("Get Channel Mode")
    def get_channel_mode(self, channel: int | str, alias: str | None = None) -> str:
        """Return channel mode name."""
        return self._session(alias).driver.channel(self._channel(channel)).get_mode().name

    @keyword("Configure Source Mode")
    def configure_source_mode(
        self,
        channel: int | str,
        voltage_v: float | str,
        current_limit_ma: float | str,
        current_range: str | int = "AUTO",
        output: bool | str = False,
        verify: bool | str = True,
        alias: str | None = None,
    ) -> None:
        """Configure source mode and optionally enable the output."""
        session = self._session(alias)
        channel_value = self._channel(channel)
        output_value = self._as_bool(output)
        if output_value:
            self._require_armed(session, channel_value)
        range_value = self._enum(CurrentRange, current_range, "current_range")
        session.driver.channel(channel_value).configure_source(
            self._as_float(voltage_v, "voltage_v"),
            self._as_float(current_limit_ma, "current_limit_ma"),
            range_value,
            output=output_value,
            verify=self._as_bool(verify),
        )
        self._audit_for(
            session,
            "configure_source",
            channel=channel_value,
            voltage_v=float(voltage_v),
            current_limit_ma=float(current_limit_ma),
            current_range=range_value.name,
            output=output_value,
        )

    @keyword("Configure Charge Mode")
    def configure_charge_mode(
        self,
        channel: int | str,
        voltage_v: float | str,
        current_limit_ma: float | str,
        resistance_mohm: float | str,
        output: bool | str = False,
        verify: bool | str = True,
        alias: str | None = None,
    ) -> None:
        """Configure charge mode and optionally enable the output."""
        session = self._session(alias)
        channel_value = self._channel(channel)
        output_value = self._as_bool(output)
        if output_value:
            self._require_armed(session, channel_value)
        session.driver.channel(channel_value).configure_charge(
            self._as_float(voltage_v, "voltage_v"),
            self._as_float(current_limit_ma, "current_limit_ma"),
            self._as_float(resistance_mohm, "resistance_mohm"),
            output=output_value,
            verify=self._as_bool(verify),
        )
        self._audit_for(session, "configure_charge", channel=channel_value, output=output_value)

    @keyword("Configure SOC Profile")
    def configure_soc_profile(
        self,
        channel: int | str,
        steps: Any,
        file_number: int | str = 1,
        start_voltage_v: float | str | None = None,
        output: bool | str = False,
        verify: bool | str = True,
        alias: str | None = None,
    ) -> None:
        """Configure SOC profile from a Robot list or JSON list of dictionaries."""
        session = self._session(alias)
        channel_value = self._channel(channel)
        output_value = self._as_bool(output)
        if output_value:
            self._require_armed(session, channel_value)
        parsed_steps = [self._soc_step(item) for item in self._as_sequence(steps, "steps")]
        session.driver.channel(channel_value).configure_soc(
            parsed_steps,
            file_number=self._as_int(file_number, "file_number"),
            start_voltage_v=self._optional_float(start_voltage_v, "start_voltage_v"),
            output=output_value,
            verify=self._as_bool(verify),
        )
        self._audit_for(session, "configure_soc", channel=channel_value, steps=len(parsed_steps), output=output_value)

    @keyword("Configure Sequence Profile")
    def configure_sequence_profile(
        self,
        channel: int | str,
        file_number: int | str,
        steps: Any,
        file_cycle: int | str = 1,
        output: bool | str = False,
        verify: bool | str = True,
        alias: str | None = None,
    ) -> None:
        """Configure sequence profile from a Robot list or JSON list of dictionaries."""
        session = self._session(alias)
        channel_value = self._channel(channel)
        output_value = self._as_bool(output)
        if output_value:
            self._require_armed(session, channel_value)
        parsed_steps = [self._sequence_step(item) for item in self._as_sequence(steps, "steps")]
        session.driver.channel(channel_value).configure_sequence(
            self._as_int(file_number, "file_number"),
            parsed_steps,
            file_cycle=self._as_int(file_cycle, "file_cycle"),
            output=output_value,
            verify=self._as_bool(verify),
        )
        self._audit_for(
            session,
            "configure_sequence",
            channel=channel_value,
            steps=len(parsed_steps),
            output=output_value,
        )

    @keyword("Enable Channel Output")
    def enable_channel_output(self, channel: int | str, alias: str | None = None) -> None:
        """Enable one armed channel output."""
        session = self._session(alias)
        channel_value = self._channel(channel)
        self._require_armed(session, channel_value)
        session.driver.channel(channel_value).output_on()
        self._audit_for(session, "output_on", channel=channel_value)

    @keyword("Disable Channel Output")
    def disable_channel_output(self, channel: int | str, alias: str | None = None) -> None:
        """Disable one output. This operation never requires arming."""
        session = self._session(alias)
        channel_value = self._channel(channel)
        session.driver.channel(channel_value).output_off()
        self._audit_for(session, "output_off", channel=channel_value)

    @keyword("All N83624 Outputs Off")
    def all_n83624_outputs_off(self, alias: str | None = None, disarm: bool | str = True) -> None:
        """Attempt to disable all 24 outputs."""
        session = self._session(alias)
        session.driver.all_outputs_off()
        if self._as_bool(disarm):
            session.armed_channels.clear()
        self._audit_for(session, "all_outputs_off", disarm=self._as_bool(disarm))

    @keyword("Get Channel Output State")
    def get_channel_output_state(self, channel: int | str, alias: str | None = None) -> bool:
        """Return true when output is enabled."""
        return self._session(alias).driver.channel(self._channel(channel)).get_output()

    @keyword("Channel Output Should Be On")
    def channel_output_should_be_on(self, channel: int | str, alias: str | None = None) -> None:
        """Fail unless output is on."""
        if not self.get_channel_output_state(channel, alias):
            raise AssertionError(f"N83624 channel {self._channel(channel)} output is OFF")

    @keyword("Channel Output Should Be Off")
    def channel_output_should_be_off(self, channel: int | str, alias: str | None = None) -> None:
        """Fail unless output is off."""
        if self.get_channel_output_state(channel, alias):
            raise AssertionError(f"N83624 channel {self._channel(channel)} output is ON")

    # Measurements and assertions -----------------------------------------------
    @keyword("Measure Channel Voltage")
    def measure_channel_voltage(self, channel: int | str, alias: str | None = None) -> float:
        """Return channel voltage in volts."""
        return self._session(alias).driver.channel(self._channel(channel)).measure_voltage_v()

    @keyword("Measure Channel Current")
    def measure_channel_current(self, channel: int | str, alias: str | None = None) -> float:
        """Return channel current in milliamperes."""
        return self._session(alias).driver.channel(self._channel(channel)).measure_current_ma()

    @keyword("Measure Channel Power")
    def measure_channel_power(self, channel: int | str, alias: str | None = None) -> float:
        """Return channel power in watts."""
        return self._session(alias).driver.channel(self._channel(channel)).measure_power_w()

    @keyword("Measure Channel Resistance")
    def measure_channel_resistance(self, channel: int | str, alias: str | None = None) -> float:
        """Return channel resistance in milliohms."""
        return self._session(alias).driver.channel(self._channel(channel)).measure_resistance_mohm()

    @keyword("Measure Channel Capacity")
    def measure_channel_capacity(self, channel: int | str, alias: str | None = None) -> float:
        """Return channel capacity in mAh."""
        return self._session(alias).driver.channel(self._channel(channel)).measure_capacity_mah()

    @keyword("Measure Channel")
    def measure_channel(self, channel: int | str, alias: str | None = None) -> dict[str, Any]:
        """Return all supported channel measurements as a dictionary."""
        measurement = self._session(alias).driver.channel(self._channel(channel)).measure_all()
        return self._to_robot(measurement)

    @keyword("Measure Voltage Channels")
    def measure_voltage_channels(self, channels: Any, alias: str | None = None) -> dict[int, float]:
        """Measure multiple channels. ``channels`` may be a Robot list or CSV string."""
        values = [self._channel(item) for item in self._as_channel_sequence(channels)]
        return self._session(alias).driver.measure_voltage_channels(values)

    @keyword("Channel Voltage Should Be Within")
    def channel_voltage_should_be_within(
        self,
        channel: int | str,
        expected_v: float | str,
        tolerance_v: float | str,
        alias: str | None = None,
    ) -> float:
        """Measure voltage and fail when absolute error exceeds tolerance."""
        actual = self.measure_channel_voltage(channel, alias)
        self._assert_within(actual, expected_v, tolerance_v, "voltage", "V")
        return actual

    @keyword("Channel Current Should Be Within")
    def channel_current_should_be_within(
        self,
        channel: int | str,
        expected_ma: float | str,
        tolerance_ma: float | str,
        alias: str | None = None,
    ) -> float:
        """Measure current and fail when absolute error exceeds tolerance."""
        actual = self.measure_channel_current(channel, alias)
        self._assert_within(actual, expected_ma, tolerance_ma, "current", "mA")
        return actual

    @keyword("Wait Until Channel Voltage Is Within")
    def wait_until_channel_voltage_is_within(
        self,
        channel: int | str,
        expected_v: float | str,
        tolerance_v: float | str,
        timeout: float | str = 5.0,
        interval: float | str = 0.1,
        alias: str | None = None,
    ) -> float:
        """Poll voltage until it is within tolerance or timeout expires."""
        return self._wait_within(
            lambda: self.measure_channel_voltage(channel, alias),
            expected_v,
            tolerance_v,
            timeout,
            interval,
            f"channel {self._channel(channel)} voltage",
            "V",
        )

    @keyword("Wait Until Channel Current Is Within")
    def wait_until_channel_current_is_within(
        self,
        channel: int | str,
        expected_ma: float | str,
        tolerance_ma: float | str,
        timeout: float | str = 5.0,
        interval: float | str = 0.1,
        alias: str | None = None,
    ) -> float:
        """Poll current until it is within tolerance or timeout expires."""
        return self._wait_within(
            lambda: self.measure_channel_current(channel, alias),
            expected_ma,
            tolerance_ma,
            timeout,
            interval,
            f"channel {self._channel(channel)} current",
            "mA",
        )

    @keyword("Get Channel Status")
    def get_channel_status(self, channel: int | str, alias: str | None = None) -> dict[str, Any]:
        """Return decoded status bits."""
        return self._to_robot(self._session(alias).driver.channel(self._channel(channel)).get_status())

    @keyword("Get Channel Event")
    def get_channel_event(self, channel: int | str, alias: str | None = None) -> dict[str, Any]:
        """Return decoded event bits."""
        return self._to_robot(self._session(alias).driver.channel(self._channel(channel)).get_event())

    @keyword("Get Channel Configuration")
    def get_channel_configuration(self, channel: int | str, alias: str | None = None) -> dict[str, Any]:
        """Return a typed configuration snapshot as a Robot dictionary."""
        return self._to_robot(
            self._session(alias).driver.channel(self._channel(channel)).read_channel_configuration()
        )

    # Protection and acquisition -------------------------------------------------
    @keyword("Set Channel Protection Limits")
    def set_channel_protection_limits(
        self,
        channel: int | str,
        ocp_current_ma: float | str,
        ovp_voltage_v: float | str,
        opp_power_mw: float | str,
        alias: str | None = None,
    ) -> None:
        """Set OCP, OVP, and OPP thresholds."""
        session = self._session(alias)
        proxy = session.driver.channel(self._channel(channel))
        proxy.set_ocp_current_ma(self._as_float(ocp_current_ma, "ocp_current_ma"))
        proxy.set_ovp_voltage_v(self._as_float(ovp_voltage_v, "ovp_voltage_v"))
        proxy.set_opp_power_mw(self._as_float(opp_power_mw, "opp_power_mw"))
        self._audit_for(session, "set_protection", channel=self._channel(channel))

    @keyword("Set Channel Capture Rate")
    def set_channel_capture_rate(
        self,
        channel: int | str,
        rate: str | int,
        alias: str | None = None,
    ) -> str:
        """Set FAST_10MS, MEDIUM_120MS, or SLOW_480MS capture rate."""
        rate_value = self._enum(CaptureRate, rate, "capture rate")
        self._session(alias).driver.channel(self._channel(channel)).set_capture_rate(rate_value)
        return rate_value.name

    @keyword("Get Channel Capture Rate")
    def get_channel_capture_rate(self, channel: int | str, alias: str | None = None) -> str:
        """Return capture rate name."""
        return self._session(alias).driver.channel(self._channel(channel)).get_capture_rate().name

    # Heartbeat and recovery -----------------------------------------------------
    @keyword("Start N83624 Heartbeat")
    def start_n83624_heartbeat(
        self,
        interval_s: float | str = 10.0,
        fail_after: int | str = 3,
        query: str = "*IDN?",
        alias: str | None = None,
    ) -> None:
        """Start background communication supervision."""
        session = self._session(alias)
        session.driver.start_heartbeat(
            HeartbeatConfig(
                interval_s=self._as_float(interval_s, "interval_s"),
                fail_after=self._as_int(fail_after, "fail_after"),
                query=str(query),
            )
        )
        self._audit_for(session, "heartbeat_start", interval_s=float(interval_s), fail_after=int(fail_after))

    @keyword("Stop N83624 Heartbeat")
    def stop_n83624_heartbeat(self, alias: str | None = None) -> None:
        """Stop background heartbeat."""
        session = self._session(alias)
        session.driver.stop_heartbeat()
        self._audit_for(session, "heartbeat_stop")

    @keyword("Get N83624 Communication Health")
    def get_n83624_communication_health(self, alias: str | None = None) -> dict[str, Any]:
        """Return session state and latest communication observation."""
        session = self._session(alias)
        return {
            "alias": session.alias,
            "state": session.driver.state.value,
            "idn": session.driver.idn,
            "observation": self._to_robot(session.driver.get_communication_observation()),
        }

    @keyword("Recover N83624 Connection")
    def recover_n83624_connection(self, alias: str | None = None) -> None:
        """Attempt transport reconnect using the configured recovery policy."""
        session = self._session(alias)
        session.driver.recover()
        session.armed_channels.clear()
        self._audit_for(session, "recover")

    # Raw SCPI -------------------------------------------------------------------
    @keyword("Enable Raw SCPI")
    def enable_raw_scpi(
        self,
        confirmation: str,
        alias: str | None = None,
    ) -> None:
        """Enable raw SCPI for a session using exact confirmation text."""
        session = self._session(alias)
        if confirmation != RAW_SCPI_CONFIRMATION:
            raise SafetyError(f"Raw SCPI enable requires exact confirmation text: {RAW_SCPI_CONFIRMATION}")
        session.allow_raw_scpi = True
        self._audit_for(session, "raw_scpi_enabled")

    @keyword("Raw SCPI Query")
    def raw_scpi_query(self, command: str, alias: str | None = None) -> str:
        """Send a raw SCPI query when explicitly enabled."""
        session = self._session(alias)
        self._require_raw_scpi(session)
        response = session.driver.query(str(command))
        self._audit_for(session, "raw_query", command=command, response=response)
        return response

    @keyword("Raw SCPI Write")
    def raw_scpi_write(self, command: str, alias: str | None = None) -> None:
        """Send a raw SCPI write when explicitly enabled.

        Raw writes bypass typed validation and the output arming gate. Use only for
        diagnostics or commands not yet represented by the library.
        """
        session = self._session(alias)
        self._require_raw_scpi(session)
        session.driver.write(str(command))
        self._audit_for(session, "raw_write", command=command)

    # Emulator support -----------------------------------------------------------
    @keyword("Set Emulator Channel Measurement")
    def set_emulator_channel_measurement(
        self,
        channel: int | str,
        voltage_v: float | str | None = None,
        current_ma: float | str | None = None,
        power_w: float | str | None = None,
        capacity_mah: float | str | None = None,
        resistance_mohm: float | str | None = None,
        alias: str | None = None,
    ) -> None:
        """Set deterministic emulator readback values for offline Robot tests."""
        session = self._session(alias)
        if session.emulator is None:
            raise SessionStateError("Active N83624 session is not an emulator")
        channel_value = self._channel(channel)
        values = {
            "VOLTage": voltage_v,
            "CURRent": current_ma,
            "POWer": power_w,
            "MAH": capacity_mah,
            "Res": resistance_mohm,
        }
        for leaf, value in values.items():
            if value is not None and str(value).strip() != "":
                session.emulator.state[f"MEASure{channel_value}:{leaf}"] = self._as_float(value, leaf)
        self._audit_for(session, "set_emulator_measurement", channel=channel_value)

    @keyword("Get Emulator Command Log")
    def get_emulator_command_log(self, alias: str | None = None) -> list[str]:
        """Return all commands recorded by the active emulator."""
        session = self._session(alias)
        if session.emulator is None:
            raise SessionStateError("Active N83624 session is not an emulator")
        return list(session.emulator.all_commands)

    # Helpers --------------------------------------------------------------------
    def _register_and_connect(
        self,
        alias: str,
        driver: N83624CellSimulator,
        *,
        safe_shutdown: bool | str,
        allow_raw_scpi: bool | str,
        audit_log_path: str | None,
        emulator: SimpleN83624Emulator | None = None,
    ) -> str:
        normalized = self._normalize_alias(alias)
        if normalized in self._sessions:
            raise SessionStateError(f"N83624 connection alias already exists: {normalized!r}")
        session = _Session(
            alias=normalized,
            driver=driver,
            safe_shutdown=self._as_bool(safe_shutdown),
            allow_raw_scpi=self._as_bool(allow_raw_scpi),
            audit_log_path=Path(audit_log_path).expanduser().resolve() if audit_log_path else None,
            armed_channels=set(),
            emulator=emulator,
        )
        try:
            driver.connect()
        except Exception:
            try:
                driver.transport.close()
            finally:
                raise
        self._sessions[normalized] = session
        self._active_alias = normalized
        self._audit_for(session, "open_connection", idn=driver.idn, safe_shutdown=session.safe_shutdown)
        logger.info(f"Opened N83624 connection {normalized!r}: {driver.idn or 'identity check disabled'}")
        return normalized

    def _session(self, alias: str | None = None) -> _Session:
        normalized = self._active_alias if alias is None or str(alias).strip() == "" else self._normalize_alias(alias)
        if normalized is None:
            raise SessionStateError("No active N83624 connection")
        try:
            return self._sessions[normalized]
        except KeyError as exc:
            raise SessionStateError(f"Unknown N83624 connection alias: {normalized!r}") from exc

    @staticmethod
    def _normalize_alias(alias: str) -> str:
        normalized = str(alias).strip()
        if not normalized:
            raise ValidationError("Connection alias must not be empty")
        return normalized

    @staticmethod
    def _make_policy(safe_shutdown: bool | str, verify_identity: bool | str) -> DriverSafetyPolicy:
        return DriverSafetyPolicy(
            require_limits_before_output_on=True,
            output_off_on_close=False,  # wrapper performs best-effort all-channel cleanup once
            output_off_on_exception=True,
            fault_simulation_enabled=False,
            require_interlock_for_output_on=False,  # wrapper's explicit arming gate is enforced instead
            require_interlock_for_fault_simulation=True,
            require_status_check_after_setters=True,
            require_identity_check_on_connect=NGI_N83624._as_bool(verify_identity),
        )

    @staticmethod
    def _make_limits(
        max_voltage_v: float | str | None,
        max_current_ma: float | str | None,
        max_resistance_mohm: float | str | None,
        max_power_mw: float | str | None,
    ) -> InstrumentLimits:
        return InstrumentLimits(
            model_name="NGI N83624 - verify exact hardware ratings",
            default_channel_limits=ChannelLimits(
                max_voltage_v=NGI_N83624._optional_float(max_voltage_v, "max_voltage_v"),
                max_current_ma=NGI_N83624._optional_float(max_current_ma, "max_current_ma"),
                max_resistance_mohm=NGI_N83624._optional_float(
                    max_resistance_mohm, "max_resistance_mohm"
                ),
                max_power_mw=NGI_N83624._optional_float(max_power_mw, "max_power_mw"),
            ),
        )

    @staticmethod
    def _require_armed(session: _Session, channel: int) -> None:
        if channel not in session.armed_channels:
            raise SafetyError(
                f"N83624 channel {channel} is not armed. Call 'Arm Channel Output' with "
                f"confirmation '{OUTPUT_CONFIRMATION}' after configuring verified limits."
            )

    @staticmethod
    def _require_raw_scpi(session: _Session) -> None:
        if not session.allow_raw_scpi:
            raise SafetyError(
                f"Raw SCPI is disabled for alias {session.alias!r}. Use 'Enable Raw SCPI' with "
                f"confirmation '{RAW_SCPI_CONFIRMATION}'."
            )

    @staticmethod
    def _channel(value: int | str) -> int:
        result = NGI_N83624._as_int(value, "channel")
        if not 1 <= result <= 24:
            raise ValidationError(f"channel must be in range 1..24; got {result}")
        return result

    @staticmethod
    def _as_bool(value: bool | str | int) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and value in (0, 1):
            return bool(value)
        text = str(value).strip().lower()
        if text in {"true", "yes", "on", "1", "${true}"}:
            return True
        if text in {"false", "no", "off", "0", "${false}", "", "none"}:
            return False
        raise ValidationError(f"Expected boolean value; got {value!r}")

    @staticmethod
    def _as_int(value: int | str, name: str) -> int:
        if isinstance(value, bool):
            raise ValidationError(f"{name} must be an integer, not boolean")
        try:
            result = int(str(value).strip())
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{name} must be an integer; got {value!r}") from exc
        return result

    @staticmethod
    def _as_float(value: float | int | str, name: str) -> float:
        if isinstance(value, bool):
            raise ValidationError(f"{name} must be numeric, not boolean")
        try:
            result = float(str(value).strip())
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{name} must be numeric; got {value!r}") from exc
        if not math.isfinite(result):
            raise ValidationError(f"{name} must be finite; got {value!r}")
        return result

    @staticmethod
    def _optional_float(value: float | int | str | None, name: str) -> float | None:
        if value is None or str(value).strip().lower() in {"", "none", "${none}"}:
            return None
        return NGI_N83624._as_float(value, name)

    @staticmethod
    def _enum(enum_type: type[Enum], value: str | int | Enum, name: str) -> Any:
        if isinstance(value, enum_type):
            return value
        if isinstance(value, str):
            text = value.strip()
            if not text:
                raise ValidationError(f"{name} must not be empty")
            try:
                return enum_type[text.upper()]
            except KeyError:
                pass
            try:
                return enum_type(int(text))
            except (ValueError, TypeError):
                pass
        else:
            try:
                return enum_type(int(value))
            except (ValueError, TypeError):
                pass
        choices = ", ".join(f"{item.name}({item.value})" for item in enum_type)
        raise ValidationError(f"Invalid {name} {value!r}; allowed values: {choices}")

    @staticmethod
    def _as_sequence(value: Any, name: str) -> Sequence[Any]:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"{name} must be a Robot list or JSON list: {exc}") from exc
        if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray, str)):
            raise ValidationError(f"{name} must be a sequence; got {type(value).__name__}")
        if not value:
            raise ValidationError(f"{name} must not be empty")
        return value

    @staticmethod
    def _as_channel_sequence(value: Any) -> list[Any]:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValidationError(f"Invalid channel JSON list: {exc}") from exc
                return list(parsed)
            return [item.strip() for item in text.split(",") if item.strip()]
        if isinstance(value, Iterable):
            return list(value)
        raise ValidationError(f"channels must be a list or CSV string; got {type(value).__name__}")

    @staticmethod
    def _as_mapping(value: Any, name: str) -> Mapping[str, Any]:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"{name} must be a dictionary or JSON object: {exc}") from exc
        if not isinstance(value, Mapping):
            raise ValidationError(f"{name} must be a mapping; got {type(value).__name__}")
        return value

    @classmethod
    def _soc_step(cls, value: Any) -> SocStep:
        item = cls._as_mapping(value, "SOC step")
        return SocStep(
            capacity_mah=cls._as_float(item["capacity_mah"], "capacity_mah"),
            voltage_v=cls._as_float(item["voltage_v"], "voltage_v"),
            current_limit_ma=cls._as_float(item["current_limit_ma"], "current_limit_ma"),
            resistance_mohm=cls._as_float(item["resistance_mohm"], "resistance_mohm"),
        )

    @classmethod
    def _sequence_step(cls, value: Any) -> SequenceStep:
        item = cls._as_mapping(value, "sequence step")
        return SequenceStep(
            voltage_v=cls._as_float(item["voltage_v"], "voltage_v"),
            current_limit_ma=cls._as_float(item["current_limit_ma"], "current_limit_ma"),
            resistance_mohm=cls._as_float(item["resistance_mohm"], "resistance_mohm"),
            runtime_s=cls._as_float(item["runtime_s"], "runtime_s"),
            link_start=cls._as_int(item.get("link_start", -1), "link_start"),
            link_end=cls._as_int(item.get("link_end", -1), "link_end"),
            link_cycle=cls._as_int(item.get("link_cycle", 0), "link_cycle"),
        )

    @classmethod
    def _to_robot(cls, value: Any) -> Any:
        if isinstance(value, Enum):
            return value.name
        if is_dataclass(value):
            return cls._to_robot(asdict(value))
        if isinstance(value, Mapping):
            return {key: cls._to_robot(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [cls._to_robot(item) for item in value]
        return value

    @classmethod
    def _assert_within(
        cls,
        actual: float,
        expected: float | str,
        tolerance: float | str,
        quantity: str,
        unit: str,
    ) -> None:
        expected_value = cls._as_float(expected, f"expected_{quantity}")
        tolerance_value = cls._as_float(tolerance, f"{quantity}_tolerance")
        if tolerance_value < 0:
            raise ValidationError("tolerance must be non-negative")
        delta = abs(actual - expected_value)
        if delta > tolerance_value:
            raise AssertionError(
                f"N83624 {quantity} {actual:g} {unit} is outside {expected_value:g} ± "
                f"{tolerance_value:g} {unit}; absolute error={delta:g} {unit}"
            )

    @classmethod
    def _wait_within(
        cls,
        measurement: Any,
        expected: float | str,
        tolerance: float | str,
        timeout: float | str,
        interval: float | str,
        label: str,
        unit: str,
    ) -> float:
        expected_value = cls._as_float(expected, "expected")
        tolerance_value = cls._as_float(tolerance, "tolerance")
        timeout_value = cls._as_float(timeout, "timeout")
        interval_value = cls._as_float(interval, "interval")
        if tolerance_value < 0 or timeout_value < 0 or interval_value <= 0:
            raise ValidationError("tolerance and timeout must be non-negative; interval must be positive")
        deadline = time.monotonic() + timeout_value
        last = float("nan")
        while True:
            last = float(measurement())
            if abs(last - expected_value) <= tolerance_value:
                return last
            if time.monotonic() >= deadline:
                raise AssertionError(
                    f"Timed out waiting for {label}: last={last:g} {unit}, expected={expected_value:g} "
                    f"± {tolerance_value:g} {unit}, timeout={timeout_value:g} s"
                )
            time.sleep(interval_value)

    def _audit(self, action: str, **details: Any) -> None:
        if self._active_alias and self._active_alias in self._sessions:
            self._audit_for(self._sessions[self._active_alias], action, **details)

    @staticmethod
    def _audit_for(session: _Session, action: str, **details: Any) -> None:
        path = session.audit_log_path
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "release": RELEASE_VERSION,
            "alias": session.alias,
            "action": action,
            **details,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

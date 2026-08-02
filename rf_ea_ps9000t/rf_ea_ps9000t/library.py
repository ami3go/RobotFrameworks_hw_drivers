"""Robot Framework adapter for :mod:`ea_ps9000t`.

Keeps SCPI construction and validation entirely in the core driver
(task §5) — this module only converts arguments/results and manages named
sessions. ``Connect``/``Disconnect`` acquire/release remote control as part
of connecting because the core driver's ``connect_visa``/``connect_simulated``/
``close`` already do so internally (task §6 items 1-2) — this adapter does
not duplicate that logic, it only calls those methods.
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


from ea_ps9000t import EaPs9000T
from ea_ps9000t.exceptions import EaPs9000TConnectionError, EaPs9000TValidationError


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
    raise EaPs9000TValidationError(f"{name} must be a Boolean, got {value!r}")


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
class EaPs9000TLibrary:
    """Robot Framework keywords for the Elektro-Automatik EA-PS 9000 T DC power supply.

    The RFDS-002 canonical connection keywords (``Connect``, ``Disconnect``,
    ``Is Connected``, ``Get Connection State``, ``Check Communication``,
    ``Get Identity``) are the primary, documented connection API — see the
    task document, task §7. Unlike every other driver in this repository,
    ``Connect`` also acquires remote control (and raises if refused) and
    ``Disconnect`` releases it, since this instrument requires explicit
    remote-control acquisition before any value-changing command is
    honored (task §6). No hardware is touched on library import.
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = "26.1"

    def __init__(self) -> None:
        self._sessions: dict[str, EaPs9000T] = {}
        self._active_alias: str | None = None
        self.ROBOT_LIBRARY_LISTENER = self

    def _end_suite(self, name: str, attributes: dict[str, Any]) -> None:
        del name, attributes
        for alias in list(self._sessions):
            try:
                self._sessions[alias].close()
            except Exception as exc:  # noqa: BLE001 - cleanup must not hide an earlier suite failure
                _rf_logger.warn(f"EaPs9000T: cleanup for {alias!r} reported: {exc}")  # noqa: G010 - robot.api.logger has no .warning
        self._sessions.clear()
        self._active_alias = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_alias(self, alias: str | None) -> str | None:
        return str(alias) if alias not in (None, "") else self._active_alias

    def _session(self, alias: str | None = None) -> EaPs9000T:
        selected = self._resolve_alias(alias)
        if selected is None:
            raise EaPs9000TConnectionError(
                "no EA-PS 9000 T connection is active; call 'Connect' first"
            )
        try:
            return self._sessions[selected]
        except KeyError as exc:
            known = ", ".join(sorted(self._sessions)) or "none"
            raise EaPs9000TConnectionError(
                f"unknown EA-PS 9000 T alias {selected!r}; known aliases: {known}"
            ) from exc

    def _connection_state(self, alias: str, driver: EaPs9000T) -> dict[str, Any]:
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
        """Connect over VISA (USB/RS232/Ethernet), or the bundled simulator with
        ``simulated=True``. Acquires remote control as part of connecting and
        raises ``EaPs9000TConnectionError`` if the device refuses it (task §6 item 1).

        Idempotent when ``alias`` is already connected to the same ``resource``.
        """

        selected_alias = str(alias).strip() or "default"
        if selected_alias in self._sessions:
            existing = self._sessions[selected_alias]
            if resource and existing.connected and str(existing.resource) != str(resource):
                raise EaPs9000TConnectionError(
                    f"alias {selected_alias!r} is already connected to {existing.resource!r}; "
                    f"disconnect it before connecting it to {resource!r}."
                )
            self._active_alias = selected_alias
            return self._connection_state(selected_alias, existing)

        simulated = _as_bool(options.pop("simulated", False), "simulated")
        if simulated:
            driver = EaPs9000T.connect_simulated()
        else:
            if not resource:
                raise EaPs9000TValidationError("resource is required unless simulated=True")
            driver = EaPs9000T.connect_visa(str(resource), timeout_s=timeout_s or 5.0)
        self._sessions[selected_alias] = driver
        self._active_alias = selected_alias
        _rf_logger.info(f"EaPs9000T: connected alias={selected_alias!r} resource={driver.resource!r}")
        return self._connection_state(selected_alias, driver)

    @keyword("Disconnect")
    def disconnect(self, alias: str | None = None) -> None:
        """Releases remote control before closing the transport (task §6 item 2).
        Idempotent: succeeds even if already disconnected."""

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

    @keyword("Get Remote Control Owner")
    def get_remote_control_owner(self, alias: str | None = None) -> str:
        """Wraps SYSTem:LOCK:OWNer? — REMOTE, NONE, or LOCAL (task §7)."""

        return self._session(alias).get_remote_control_owner().value

    @keyword("Switch Power Supply")
    def switch_power_supply(self, alias: str) -> str:
        self._session(alias)
        self._active_alias = str(alias)
        return self._active_alias

    @keyword("Get Active Power Supply")
    def get_active_power_supply(self) -> str | None:
        return self._active_alias

    @keyword("List Power Supply Connections")
    def list_power_supply_connections(self) -> list[str]:
        return sorted(self._sessions)

    # ------------------------------------------------------------------
    # Set values (task §8)
    # ------------------------------------------------------------------
    @keyword("Set Voltage")
    def set_voltage(self, value: float, alias: str | None = None) -> None:
        self._session(alias).set_voltage(float(value))

    @keyword("Get Voltage")
    def get_voltage(self, alias: str | None = None) -> float:
        return self._session(alias).get_voltage()

    @keyword("Set Current")
    def set_current(self, value: float, alias: str | None = None) -> None:
        self._session(alias).set_current(float(value))

    @keyword("Get Current")
    def get_current(self, alias: str | None = None) -> float:
        return self._session(alias).get_current()

    @keyword("Set Power")
    def set_power(self, value: float, alias: str | None = None) -> None:
        self._session(alias).set_power(float(value))

    @keyword("Get Power")
    def get_power(self, alias: str | None = None) -> float:
        return self._session(alias).get_power()

    # ------------------------------------------------------------------
    # Protection thresholds (task §8)
    # ------------------------------------------------------------------
    @keyword("Set Overvoltage Protection")
    def set_overvoltage_protection(self, value: float, alias: str | None = None) -> None:
        self._session(alias).set_overvoltage_protection(float(value))

    @keyword("Get Overvoltage Protection")
    def get_overvoltage_protection(self, alias: str | None = None) -> float:
        return self._session(alias).get_overvoltage_protection()

    @keyword("Set Overcurrent Protection")
    def set_overcurrent_protection(self, value: float, alias: str | None = None) -> None:
        self._session(alias).set_overcurrent_protection(float(value))

    @keyword("Get Overcurrent Protection")
    def get_overcurrent_protection(self, alias: str | None = None) -> float:
        return self._session(alias).get_overcurrent_protection()

    @keyword("Set Overpower Protection")
    def set_overpower_protection(self, value: float, alias: str | None = None) -> None:
        self._session(alias).set_overpower_protection(float(value))

    @keyword("Get Overpower Protection")
    def get_overpower_protection(self, alias: str | None = None) -> float:
        return self._session(alias).get_overpower_protection()

    @keyword("Get Protection Thresholds")
    def get_protection_thresholds(self, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_protection_thresholds())

    # ------------------------------------------------------------------
    # Output control (task §8)
    # ------------------------------------------------------------------
    @keyword("Enable Output")
    def enable_output(self, alias: str | None = None) -> None:
        self._session(alias).enable_output()

    @keyword("Disable Output")
    def disable_output(self, alias: str | None = None) -> None:
        self._session(alias).disable_output()

    @keyword("Is Output Enabled")
    def is_output_enabled(self, alias: str | None = None) -> bool:
        return self._session(alias).is_output_enabled()

    # ------------------------------------------------------------------
    # Measuring (task §8)
    # ------------------------------------------------------------------
    @keyword("Get Measured Voltage")
    def get_measured_voltage(self, alias: str | None = None) -> float:
        return self._session(alias).get_measured_voltage()

    @keyword("Get Measured Current")
    def get_measured_current(self, alias: str | None = None) -> float:
        return self._session(alias).get_measured_current()

    @keyword("Get Measured Power")
    def get_measured_power(self, alias: str | None = None) -> float:
        return self._session(alias).get_measured_power()

    @keyword("Get Measured Values")
    def get_measured_values(self, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_measured_values())

    # ------------------------------------------------------------------
    # General queries (task §8)
    # ------------------------------------------------------------------
    @keyword("Get Nominal Ratings")
    def get_nominal_ratings(self, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_nominal_ratings())

    @keyword("Get Device Class")
    def get_device_class(self, alias: str | None = None) -> str:
        return self._session(alias).get_device_class()

    @keyword("Get Alarm Counters")
    def get_alarm_counters(self, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_alarm_counters())

    # ------------------------------------------------------------------
    # Adjustment limits (task §9)
    # ------------------------------------------------------------------
    @keyword("Set Voltage Limit Low")
    def set_voltage_limit_low(self, value: float, alias: str | None = None) -> None:
        self._session(alias).set_voltage_limit_low(float(value))

    @keyword("Set Voltage Limit High")
    def set_voltage_limit_high(self, value: float, alias: str | None = None) -> None:
        self._session(alias).set_voltage_limit_high(float(value))

    @keyword("Get Voltage Limits")
    def get_voltage_limits(self, alias: str | None = None) -> list[float]:
        return list(self._session(alias).get_voltage_limits())

    @keyword("Set Current Limit Low")
    def set_current_limit_low(self, value: float, alias: str | None = None) -> None:
        self._session(alias).set_current_limit_low(float(value))

    @keyword("Set Current Limit High")
    def set_current_limit_high(self, value: float, alias: str | None = None) -> None:
        self._session(alias).set_current_limit_high(float(value))

    @keyword("Get Current Limits")
    def get_current_limits(self, alias: str | None = None) -> list[float]:
        return list(self._session(alias).get_current_limits())

    @keyword("Set Power Limit High")
    def set_power_limit_high(self, value: float, alias: str | None = None) -> None:
        """No corresponding "low" limit exists on this instrument family (task §9)."""

        self._session(alias).set_power_limit_high(float(value))

    @keyword("Get Power Limit High")
    def get_power_limit_high(self, alias: str | None = None) -> float:
        return self._session(alias).get_power_limit_high()

    @keyword("Get Adjustment Limits")
    def get_adjustment_limits(self, alias: str | None = None) -> dict[str, Any]:
        return _robot_value(self._session(alias).get_adjustment_limits())

    # ------------------------------------------------------------------
    # Device configuration (task §9, PST-applicable subset only)
    # ------------------------------------------------------------------
    @keyword("Set Power Stage After Remote")
    def set_power_stage_after_remote(self, mode: str, alias: str | None = None) -> None:
        self._session(alias).set_power_stage_after_remote(mode)

    @keyword("Get Power Stage After Remote")
    def get_power_stage_after_remote(self, alias: str | None = None) -> str:
        return self._session(alias).get_power_stage_after_remote().value

    @keyword("Set Output Restore Mode")
    def set_output_restore_mode(self, mode: str, alias: str | None = None) -> None:
        self._session(alias).set_output_restore_mode(mode)

    @keyword("Get Output Restore Mode")
    def get_output_restore_mode(self, alias: str | None = None) -> str:
        return self._session(alias).get_output_restore_mode().value

    @keyword("Set User Text")
    def set_user_text(self, text: str, alias: str | None = None) -> None:
        self._session(alias).set_user_text(text)

    @keyword("Get User Text")
    def get_user_text(self, alias: str | None = None) -> str:
        return self._session(alias).get_user_text()

    @keyword("Set Communication Timeout")
    def set_communication_timeout(self, milliseconds: int, alias: str | None = None) -> None:
        """Serial interfaces only (USB, RS232) — not meaningful over Ethernet (task §9)."""

        self._session(alias).set_communication_timeout(int(milliseconds))

    @keyword("Get Communication Timeout")
    def get_communication_timeout(self, alias: str | None = None) -> int:
        return self._session(alias).get_communication_timeout()

    @keyword("Set Power Fail Alarm Action")
    def set_power_fail_alarm_action(self, action: str, alias: str | None = None) -> None:
        self._session(alias).set_power_fail_alarm_action(action)

    @keyword("Get Power Fail Alarm Action")
    def get_power_fail_alarm_action(self, alias: str | None = None) -> str:
        return self._session(alias).get_power_fail_alarm_action().value

    @keyword("Set Overtemperature Alarm Action")
    def set_overtemperature_alarm_action(self, action: str, alias: str | None = None) -> None:
        self._session(alias).set_overtemperature_alarm_action(action)

    @keyword("Get Overtemperature Alarm Action")
    def get_overtemperature_alarm_action(self, alias: str | None = None) -> str:
        return self._session(alias).get_overtemperature_alarm_action().value

    # ------------------------------------------------------------------
    # LAN configuration (Gate 3 extension)
    # ------------------------------------------------------------------
    @keyword("Set LAN DHCP Enabled")
    def set_lan_dhcp_enabled(self, enabled: bool, alias: str | None = None) -> None:
        self._session(alias).set_lan_dhcp_enabled(_as_bool(enabled, "enabled"))

    @keyword("Get LAN DHCP Enabled")
    def get_lan_dhcp_enabled(self, alias: str | None = None) -> bool:
        return self._session(alias).get_lan_dhcp_enabled()

    @keyword("Set LAN IP Address")
    def set_lan_ip_address(self, address: str, alias: str | None = None) -> None:
        self._session(alias).set_lan_ip_address(address)

    @keyword("Get LAN IP Address")
    def get_lan_ip_address(self, alias: str | None = None) -> str:
        return self._session(alias).get_lan_ip_address()

    @keyword("Set LAN Subnet Mask")
    def set_lan_subnet_mask(self, mask: str, alias: str | None = None) -> None:
        self._session(alias).set_lan_subnet_mask(mask)

    @keyword("Get LAN Subnet Mask")
    def get_lan_subnet_mask(self, alias: str | None = None) -> str:
        return self._session(alias).get_lan_subnet_mask()

    @keyword("Set LAN Gateway")
    def set_lan_gateway(self, gateway: str, alias: str | None = None) -> None:
        self._session(alias).set_lan_gateway(gateway)

    @keyword("Get LAN Gateway")
    def get_lan_gateway(self, alias: str | None = None) -> str:
        return self._session(alias).get_lan_gateway()

    @keyword("Set LAN Hostname")
    def set_lan_hostname(self, hostname: str, alias: str | None = None) -> None:
        self._session(alias).set_lan_hostname(hostname)

    @keyword("Get LAN Hostname")
    def get_lan_hostname(self, alias: str | None = None) -> str:
        return self._session(alias).get_lan_hostname()

    @keyword("Set LAN Domain")
    def set_lan_domain(self, domain: str, alias: str | None = None) -> None:
        self._session(alias).set_lan_domain(domain)

    @keyword("Get LAN Domain")
    def get_lan_domain(self, alias: str | None = None) -> str:
        return self._session(alias).get_lan_domain()

    @keyword("Set LAN DNS1")
    def set_lan_dns1(self, address: str, alias: str | None = None) -> None:
        self._session(alias).set_lan_dns1(address)

    @keyword("Get LAN DNS1")
    def get_lan_dns1(self, alias: str | None = None) -> str:
        return self._session(alias).get_lan_dns1()

    @keyword("Set LAN DNS2")
    def set_lan_dns2(self, address: str, alias: str | None = None) -> None:
        """Anybus modules only (task §9); see ``ea_ps9000t.driver.EaPs9000T.set_lan_dns2``."""

        self._session(alias).set_lan_dns2(address)

    @keyword("Get LAN DNS2")
    def get_lan_dns2(self, alias: str | None = None) -> str:
        return self._session(alias).get_lan_dns2()

    @keyword("Set LAN Control Port")
    def set_lan_control_port(self, port: int, alias: str | None = None) -> None:
        """Rejects port 502, reserved for ModBus TCP (task §9)."""

        self._session(alias).set_lan_control_port(int(port))

    @keyword("Get LAN Control Port")
    def get_lan_control_port(self, alias: str | None = None) -> int:
        return self._session(alias).get_lan_control_port()

    @keyword("Set LAN Keepalive Enabled")
    def set_lan_keepalive_enabled(self, enabled: bool, alias: str | None = None) -> None:
        self._session(alias).set_lan_keepalive_enabled(_as_bool(enabled, "enabled"))

    @keyword("Get LAN Keepalive Enabled")
    def get_lan_keepalive_enabled(self, alias: str | None = None) -> bool:
        return self._session(alias).get_lan_keepalive_enabled()

    @keyword("Set LAN Timeout")
    def set_lan_timeout(self, seconds: int, alias: str | None = None) -> None:
        self._session(alias).set_lan_timeout(int(seconds))

    @keyword("Get LAN Timeout")
    def get_lan_timeout(self, alias: str | None = None) -> int:
        return self._session(alias).get_lan_timeout()

    @keyword("Get LAN MAC Address")
    def get_lan_mac_address(self, alias: str | None = None) -> str:
        return self._session(alias).get_lan_mac_address()

    # ------------------------------------------------------------------
    # Analog interface configuration (Gate 3 extension)
    # ------------------------------------------------------------------
    @keyword("Set Analog Reference Range")
    def set_analog_reference_range(self, range_v: int, alias: str | None = None) -> None:
        self._session(alias).set_analog_reference_range(int(range_v))

    @keyword("Get Analog Reference Range")
    def get_analog_reference_range(self, alias: str | None = None) -> int:
        return self._session(alias).get_analog_reference_range()

    @keyword("Set Analog REMSB Level")
    def set_analog_remsb_level(self, level: str, alias: str | None = None) -> None:
        self._session(alias).set_analog_remsb_level(level)

    @keyword("Get Analog REMSB Level")
    def get_analog_remsb_level(self, alias: str | None = None) -> str:
        return self._session(alias).get_analog_remsb_level().value

    @keyword("Set Analog REMSB Action")
    def set_analog_remsb_action(self, action: str, alias: str | None = None) -> None:
        self._session(alias).set_analog_remsb_action(action)

    @keyword("Get Analog REMSB Action")
    def get_analog_remsb_action(self, alias: str | None = None) -> str:
        return self._session(alias).get_analog_remsb_action().value

    # ------------------------------------------------------------------
    # Raw SCPI escape hatch (task §10)
    # ------------------------------------------------------------------
    @keyword("Enable Raw SCPI")
    def enable_raw_scpi(self, confirmation: str, alias: str | None = None) -> None:
        self._session(alias).enable_raw_scpi(confirmation)

    @keyword("Raw SCPI Query")
    def raw_scpi_query(self, command: str, alias: str | None = None) -> str:
        """Bypasses typed validation. Also the sanctioned path to ModBus-disable and
        to LAN/analog-interface commands not exposed as typed keywords (Gate 3 added
        typed keywords for the ordinary LAN and analog-interface configuration
        commands themselves; ModBus-disable and the Anybus/IF-AB/10000-series-only
        LAN commands remain raw-SCPI-only, task §9)."""

        return self._session(alias).raw_query(command)

    @keyword("Raw SCPI Write")
    def raw_scpi_write(self, command: str, alias: str | None = None) -> None:
        """Bypasses typed validation."""

        self._session(alias).raw_write(command)

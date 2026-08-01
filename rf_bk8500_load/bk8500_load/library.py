"""``BK8500Library`` -- Robot Framework keywords for B&K 8500 series DC loads.

Import in a suite::

    Library    BK8500Library    port=/dev/ttyUSB0    model=8500

or, for development without hardware::

    Library    BK8500Library    simulated=${TRUE}    model=8500

Every keyword operates on the *current* connection. Several loads can be open
at once; use ``Switch Load Connection`` with the alias given to
``Open Load Connection``.
"""

from __future__ import annotations

from typing import Any

from .driver import BK8500Driver
from .enums import ListRepeat, LoadFunction, LoadMode, TransientOperation, TriggerSource, parse_enum
from .exceptions import BK8500ConnectionError, BK8500VerificationError
from .transport import SUPPORTED_BAUD_RATES, SimulatedTransport
from .version import VERSION

try:  # Robot Framework is optional at import time so pytest can run standalone
    from robot.api import logger as _rf_logger
    from robot.api.deco import keyword, library
except ImportError:  # pragma: no cover

    def keyword(name=None, tags=(), types=None):  # type: ignore[misc]
        """Minimal Robot decorator compatible with source-only test runs.

        Robot Framework is a runtime dependency of the installed package, but
        the pure-Python unit and contract tests are intentionally runnable in a
        source checkout before dependencies are installed.  Preserve the same
        metadata that the real decorator exposes so conformance checks do not
        silently see an empty keyword surface.
        """

        def decorate(func):
            func.robot_name = name or func.__name__.replace("_", " ").title()
            func.robot_tags = tags
            func.robot_types = types
            return func

        return decorate

    def library(cls=None, **kwargs):  # type: ignore[misc]
        return cls if cls is not None else (lambda inner: inner)

    class _FallbackLogger:
        @staticmethod
        def info(message, *args, **kwargs):
            print(message)

        warn = debug = info

    _rf_logger = _FallbackLogger()


@library(scope="GLOBAL", version=VERSION, auto_keywords=False)
class BK8500Library:
    """Robot Framework library for the B&K Precision 8500 series DC loads."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_VERSION = VERSION

    def __init__(
        self,
        port: str | None = None,
        baudrate: int | str = 9600,
        model: str | None = None,
        address: int = 0,
        timeout: float = 1.0,
        simulated: bool = False,
        auto_connect: bool = True,
        source_voltage: float = 12.0,
        source_resistance: float = 0.05,
        auto_detect_baudrate: bool = False,
        baudrate_candidates: str = "4800,9600,19200,38400",
        probe_timeout: float = 0.75,
        confirm_baudrate_identity: bool = True,
    ) -> None:
        self._connections: dict[str, BK8500Driver] = {}
        self._current: str | None = None
        self._defaults = {
            "baudrate": baudrate,
            "model": model,
            "address": address,
            "timeout": timeout,
            "simulated": simulated,
            "source_voltage": source_voltage,
            "source_resistance": source_resistance,
            "auto_detect_baudrate": auto_detect_baudrate,
            "baudrate_candidates": baudrate_candidates,
            "probe_timeout": probe_timeout,
            "confirm_baudrate_identity": confirm_baudrate_identity,
        }
        if auto_connect and (port or simulated):
            self.open_load_connection(
                port=port,
                baudrate=baudrate,
                model=model,
                address=address,
                timeout=timeout,
                simulated=simulated,
                source_voltage=source_voltage,
                source_resistance=source_resistance,
                auto_detect_baudrate=auto_detect_baudrate,
                baudrate_candidates=baudrate_candidates,
                probe_timeout=probe_timeout,
                confirm_baudrate_identity=confirm_baudrate_identity,
            )

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    @property
    def driver(self) -> BK8500Driver:
        """The driver behind the current connection."""
        if self._current is None:
            raise BK8500ConnectionError(
                "No DC load connection is open. Call 'Open Load Connection' first."
            )
        return self._connections[self._current]

    @staticmethod
    def _compare(actual: float, expected: float, tolerance: float, quantity: str, unit: str) -> float:
        deviation = abs(actual - expected)
        message = (
            f"{quantity}: measured {actual:.6g} {unit}, expected {expected:.6g} "
            f"+/- {tolerance:.6g} {unit} (deviation {deviation:.6g} {unit})"
        )
        if deviation > tolerance:
            raise BK8500VerificationError(message)
        _rf_logger.info(message)
        return actual

    @staticmethod
    def _parse_baudrate_candidates(value: Any) -> tuple[int, ...]:
        """Parse Robot/Python candidate input into a tuple of integers."""
        if value is None:
            return SUPPORTED_BAUD_RATES
        if isinstance(value, str):
            parts = [item.strip() for item in value.replace(";", ",").split(",")]
            values = [item for item in parts if item]
        elif isinstance(value, (list, tuple, set)):
            values = list(value)
        else:
            values = [value]
        try:
            return tuple(int(item) for item in values)
        except (TypeError, ValueError):
            raise BK8500ConnectionError(
                f"Invalid baudrate_candidates={value!r}; use comma-separated values "
                f"from {SUPPORTED_BAUD_RATES}"
            ) from None

    # ------------------------------------------------------------------
    # connection management
    # ------------------------------------------------------------------
    @keyword("Open Load Connection")
    def open_load_connection(
        self,
        port: str | None = None,
        baudrate: int | str | None = None,
        model: str | None = None,
        alias: str = "default",
        address: int | None = None,
        timeout: float | None = None,
        simulated: bool | None = None,
        identify: bool = True,
        assert_dtr: bool = True,
        assert_rts: bool = True,
        source_voltage: float | None = None,
        source_resistance: float | None = None,
        auto_detect_baudrate: bool | None = None,
        baudrate_candidates: Any = None,
        probe_timeout: float | None = None,
        confirm_baudrate_identity: bool | None = None,
    ) -> str:
        """Open a connection to a DC load and make it current.

        ``port`` is a serial device such as ``/dev/ttyUSB0`` or ``COM4``. With
        ``simulated=${TRUE}`` an in-process instrument model is used instead
        and ``port`` is ignored.

        ``assert_dtr`` and ``assert_rts`` default to true because the 8500
        series requires both signal lines asserted; leave them alone unless a
        non-standard adapter needs otherwise.

        Set ``baudrate=AUTO`` or ``auto_detect_baudrate=${TRUE}`` to probe the
        supported rates using only the read-only product-information query. The
        requested numeric baud is always tried first, followed by
        ``baudrate_candidates``. A rate is accepted only after a valid identity
        is received twice by default.

        Returns the alias, so it can be stored in a variable.
        """
        if alias in self._connections:
            raise BK8500ConnectionError(
                f"A load connection with alias '{alias}' is already open. "
                "Close it or choose a different alias."
            )

        defaults = self._defaults
        baudrate = defaults["baudrate"] if baudrate is None else baudrate
        model = defaults["model"] if model is None else model
        address = defaults["address"] if address is None else address
        timeout = defaults["timeout"] if timeout is None else timeout
        simulated = defaults["simulated"] if simulated is None else simulated
        auto_detect_baudrate = (
            defaults["auto_detect_baudrate"]
            if auto_detect_baudrate is None
            else bool(auto_detect_baudrate)
        )
        baudrate_candidates = (
            defaults["baudrate_candidates"]
            if baudrate_candidates is None
            else baudrate_candidates
        )
        probe_timeout = (
            defaults["probe_timeout"] if probe_timeout is None else probe_timeout
        )
        confirm_baudrate_identity = (
            defaults["confirm_baudrate_identity"]
            if confirm_baudrate_identity is None
            else bool(confirm_baudrate_identity)
        )

        auto_requested = isinstance(baudrate, str) and baudrate.strip().upper() == "AUTO"
        if auto_requested:
            configured_default = defaults["baudrate"]
            preferred_baudrate = (
                9600
                if isinstance(configured_default, str)
                and configured_default.strip().upper() == "AUTO"
                else int(configured_default)
            )
            auto_detect_baudrate = True
        else:
            try:
                preferred_baudrate = int(baudrate)
            except (TypeError, ValueError):
                raise BK8500ConnectionError(
                    f"Invalid baudrate={baudrate!r}; use a supported numeric rate or AUTO"
                ) from None

        if simulated:
            transport = SimulatedTransport(
                model=str(model or "8500"),
                source_voltage_v=(
                    defaults["source_voltage"] if source_voltage is None else source_voltage
                ),
                source_resistance_ohm=(
                    defaults["source_resistance"] if source_resistance is None else source_resistance
                ),
                address=int(address),
            )
            driver = BK8500Driver(transport, model=model, address=int(address))
        else:
            if not port:
                raise BK8500ConnectionError(
                    "A serial port is required unless simulated=${TRUE} is used"
                )
            if auto_detect_baudrate:
                candidates = self._parse_baudrate_candidates(baudrate_candidates)
                driver, info, attempts = BK8500Driver.connect_serial_with_baud_detection(
                    port=port,
                    preferred_baudrate=preferred_baudrate,
                    baudrate_candidates=candidates,
                    model=model,
                    address=int(address),
                    timeout_s=float(timeout),
                    probe_timeout_s=float(probe_timeout),
                    assert_dtr=assert_dtr,
                    assert_rts=assert_rts,
                    confirm_identity=confirm_baudrate_identity,
                )
                _rf_logger.info(
                    f"Automatically detected {driver.detected_baudrate} baud on {port}"
                )
                _rf_logger.info(f"Baud probe attempts: {attempts}")
            else:
                driver = BK8500Driver.on_serial_port(
                    port=port,
                    baudrate=preferred_baudrate,
                    model=model,
                    address=int(address),
                    timeout_s=float(timeout),
                    assert_dtr=assert_dtr,
                    assert_rts=assert_rts,
                )
                info = driver.connect(identify=identify)
        if simulated:
            info = driver.connect(identify=identify)
        self._connections[alias] = driver
        self._current = alias
        _rf_logger.info(
            f"Opened DC load connection '{alias}' -> {driver.description}"
            + (f" ({info.serial_number}, firmware {info.firmware_version})" if info else "")
        )
        return alias

    @keyword("Switch Load Connection")
    def switch_load_connection(self, alias: str) -> str:
        """Make a previously opened connection current. Returns the previous alias."""
        if alias not in self._connections:
            known = ", ".join(sorted(self._connections)) or "none"
            raise BK8500ConnectionError(f"Unknown load alias '{alias}'. Open aliases: {known}")
        previous = self._current or ""
        self._current = alias
        return previous

    @keyword("Close Load Connection")
    def close_load_connection(self, alias: str | None = None, safe: bool = True) -> None:
        """Return the load to a safe state and close its port."""
        target = alias or self._current
        if target is None or target not in self._connections:
            return
        self._connections.pop(target).disconnect(safe=safe)
        if self._current == target:
            # Do not silently adopt another load as "current": a keyword meant
            # for the closed connection would then act on a different instrument.
            self._current = None
            if self._connections:
                _rf_logger.info(
                    f"Closed the current connection '{target}'. Still open: "
                    f"{', '.join(sorted(self._connections))}. "
                    "Use 'Switch Load Connection' before the next keyword."
                )

    @keyword("Close All Load Connections")
    def close_all_load_connections(self, safe: bool = True) -> None:
        """Suite teardown keyword: safe-state and close every open load."""
        for alias in list(self._connections):
            self.close_load_connection(alias, safe=safe)

    # ------------------------------------------------------------------
    # RFDS-002 mandatory universal keywords
    #
    # Thin, idempotent wrappers over the device-specific keywords above, kept
    # for generic/cross-driver tooling that expects the RFDS canonical names.
    # The device-specific keywords remain the primary, documented API.
    # ------------------------------------------------------------------
    def _connection_state(self, alias: str, driver: BK8500Driver) -> dict[str, Any]:
        """Build the RFDS-002 Section 12.1 normalized connection-state dictionary."""
        identity_str: str | None = None
        try:
            info = driver.get_product_info().as_dict()
            parts = [str(info[key]) for key in ("model", "serial_number", "firmware_version") if info.get(key)]
            identity_str = ", ".join(parts) if parts else None
        except Exception:
            identity_str = None
        return {
            "alias": alias,
            "resource": getattr(driver.transport, "port", None) or driver.description,
            "connected": True,
            "communication_ok": identity_str is not None,
            "transport": driver.description,
            "identity": identity_str,
            "timeout_s": getattr(driver.transport, "timeout", None),
            "state": "connected",
        }

    @keyword("Connect")
    def connect(
        self,
        resource: str | None = None,
        alias: str = "default",
        timeout_s: float | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        """RFDS-002 generic connect. ``resource`` is the serial port (see ``Open Load Connection``).

        Idempotent when ``alias`` is already connected to the same ``resource``.
        """
        selected_alias = str(alias).strip() or "default"
        if selected_alias in self._connections:
            driver = self._connections[selected_alias]
            existing_resource = getattr(driver.transport, "port", None) or driver.description
            if resource and str(existing_resource) != str(resource):
                raise BK8500ConnectionError(
                    f"Alias '{selected_alias}' is already connected to {existing_resource!r}; "
                    f"close it before connecting it to {resource!r}."
                )
            return self._connection_state(selected_alias, driver)
        connect_kwargs: dict[str, Any] = dict(options)
        if timeout_s is not None:
            connect_kwargs.setdefault("timeout", timeout_s)
        self.open_load_connection(port=resource, alias=selected_alias, **connect_kwargs)
        return self._connection_state(selected_alias, self._connections[selected_alias])

    @keyword("Disconnect")
    def disconnect(self, alias: str | None = None) -> None:
        """RFDS-002 generic disconnect. Idempotent: succeeds even if already disconnected."""
        self.close_load_connection(alias)

    @keyword("Is Connected")
    def is_connected(self, alias: str | None = None) -> bool:
        """Return whether ``alias`` (or the current connection) is open."""
        target = alias if alias not in (None, "") else self._current
        return target is not None and target in self._connections

    @keyword("Get Connection State")
    def get_connection_state(self, alias: str | None = None, refresh: bool = False) -> dict[str, Any]:
        """Return the RFDS-002 Section 12.1 normalized connection-state dictionary."""
        target = alias if alias not in (None, "") else self._current
        if target is None or target not in self._connections:
            return {
                "alias": target or "default",
                "resource": None,
                "connected": False,
                "communication_ok": False,
                "transport": None,
                "identity": None,
                "timeout_s": None,
                "state": "disconnected",
            }
        return self._connection_state(target, self._connections[target])

    @keyword("Check Communication")
    def check_communication(self, alias: str | None = None) -> bool:
        """Perform a bounded, non-destructive communication check. Raises on failure."""
        target = alias if alias not in (None, "") else self._current
        if target is None or target not in self._connections:
            raise BK8500ConnectionError(
                f"No DC load connection is open for alias {target!r}. Call 'Connect' first."
            )
        self._connections[target].get_product_info()
        return True

    @keyword("Get Identity")
    def get_identity(self, alias: str | None = None, refresh: bool = True) -> str:
        """Return a stable human-readable identity string."""
        del refresh
        target = alias if alias not in (None, "") else self._current
        if target is None or target not in self._connections:
            raise BK8500ConnectionError(
                f"No DC load connection is open for alias {target!r}. Call 'Connect' first."
            )
        info = self._connections[target].get_product_info().as_dict()
        parts = [str(info[key]) for key in ("model", "serial_number", "firmware_version") if info.get(key)]
        return ", ".join(parts) if parts else "BK8500"

    @keyword("Get Load Product Information")
    def get_load_product_information(self) -> dict:
        """Return ``{model, serial_number, firmware_version}`` from the instrument."""
        return self.driver.get_product_info().as_dict()

    @keyword("Get Load Rated Limits")
    def get_load_rated_limits(self) -> dict:
        """Return the rated envelope the driver validates against."""
        limits = self.driver.limits
        return {
            "model": limits.model,
            "max_voltage_v": limits.max_voltage_v,
            "max_current_a": limits.max_current_a,
            "max_power_w": limits.max_power_w,
        }

    # ------------------------------------------------------------------
    # control state
    # ------------------------------------------------------------------
    @keyword("Claim Remote Control")
    def claim_remote_control(self) -> None:
        """Put the load under remote control. Required before any setting."""
        self.driver.set_remote_control(True)

    @keyword("Release Remote Control")
    def release_remote_control(self) -> None:
        """Return the load to front panel operation."""
        self.driver.set_remote_control(False)

    @keyword("Set Local Key Enabled")
    def set_local_key_enabled(self, enabled: bool = True) -> None:
        """Enable or disable the front panel LOCAL key while in remote control."""
        self.driver.set_local_key_enabled(enabled)

    @keyword("Load Input On")
    def load_input_on(self) -> None:
        """Close the load input and start sinking current.

        Requires remote control. Configure mode, setpoint and protection
        limits before calling this.
        """
        self.driver.set_input_state(True)

    @keyword("Load Input Off")
    def load_input_off(self) -> None:
        """Open the load input. Safe to call at any time."""
        self.driver.set_input_state(False)

    @keyword("Reset Load To Safe State")
    def reset_load_to_safe_state(self) -> None:
        """Input off, FIXED function, front panel handed back to the operator."""
        self.driver.reset_to_safe_state()

    @keyword("Set Remote Sense")
    def set_remote_sense(self, enabled: bool) -> None:
        """Enable or disable 4-wire remote voltage sensing."""
        self.driver.set_remote_sense(enabled)

    @keyword("Get Remote Sense")
    def get_remote_sense(self) -> bool:
        """Return whether remote sensing is enabled."""
        return self.driver.get_remote_sense()

    # ------------------------------------------------------------------
    # protection
    # ------------------------------------------------------------------
    @keyword("Configure Load Protection")
    def configure_load_protection(
        self,
        max_voltage: float | None = None,
        max_current: float | None = None,
        max_power: float | None = None,
    ) -> None:
        """Write the instrument's own over-voltage, over-current and over-power limits."""
        self.driver.configure_protection(max_voltage, max_current, max_power)

    @keyword("Get Load Protection Limits")
    def get_load_protection_limits(self) -> dict:
        """Read back the configured protection limits."""
        return {
            "max_voltage_v": self.driver.get_max_voltage(),
            "max_current_a": self.driver.get_max_current(),
            "max_power_w": self.driver.get_max_power(),
        }

    # ------------------------------------------------------------------
    # mode and setpoint
    # ------------------------------------------------------------------
    @keyword("Set Load Mode")
    def set_load_mode(self, mode: str) -> str:
        """Select the regulation mode: ``CC``, ``CV``, ``CW`` or ``CR``."""
        return self.driver.set_mode(mode).name

    @keyword("Get Load Mode")
    def get_load_mode(self) -> str:
        """Return the active regulation mode as a string."""
        return self.driver.get_mode().name

    @keyword("Set Load Setpoint")
    def set_load_setpoint(self, mode: str, value: float) -> None:
        """Write the regulation level of ``mode`` in SI units (A, V, W or ohm)."""
        self.driver.set_setpoint(mode, value)

    @keyword("Get Load Setpoint")
    def get_load_setpoint(self, mode: str) -> float:
        """Read the regulation level of ``mode`` in SI units."""
        return self.driver.get_setpoint(mode)

    @keyword("Apply Constant Current")
    def apply_constant_current(self, current: float, enable_input: bool = False) -> None:
        """CC mode at ``current`` amperes, optionally closing the input."""
        self.driver.apply_load(LoadMode.CC, current, enable_input)

    @keyword("Apply Constant Voltage")
    def apply_constant_voltage(self, voltage: float, enable_input: bool = False) -> None:
        """CV mode at ``voltage`` volts, optionally closing the input."""
        self.driver.apply_load(LoadMode.CV, voltage, enable_input)

    @keyword("Apply Constant Power")
    def apply_constant_power(self, power: float, enable_input: bool = False) -> None:
        """CW mode at ``power`` watts, optionally closing the input."""
        self.driver.apply_load(LoadMode.CW, power, enable_input)

    @keyword("Apply Constant Resistance")
    def apply_constant_resistance(self, resistance: float, enable_input: bool = False) -> None:
        """CR mode at ``resistance`` ohms, optionally closing the input."""
        self.driver.apply_load(LoadMode.CR, resistance, enable_input)

    @keyword("Set Load Function")
    def set_load_function(self, function: str) -> str:
        """Select ``FIXED``, ``TRANSIENT``, ``LIST`` or ``BATTERY``.

        ``SHORT`` is refused here because it commands the model's maximum sink
        current; use ``Set Load Function Unchecked`` if the bench contract
        explicitly permits it.
        """
        return self.driver.set_function(function).name

    @keyword("Set Load Function Unchecked")
    def set_load_function_unchecked(self, function: str) -> str:
        """Select any function, including ``SHORT``. Bypasses the SHORT safety rule."""
        return self.driver.set_function_unchecked(function).name

    @keyword("Get Load Function")
    def get_load_function(self) -> str:
        """Return the active function as a string."""
        return self.driver.get_function().name

    # ------------------------------------------------------------------
    # transient and triggering
    # ------------------------------------------------------------------
    @keyword("Configure Load Transient")
    def configure_load_transient(
        self,
        mode: str,
        level_a: float,
        dwell_a: float,
        level_b: float,
        dwell_b: float,
        operation: str = "CONTINUOUS",
    ) -> None:
        """Program A/B transient toggling for ``mode``. Dwell times in seconds."""
        self.driver.set_transient(mode, level_a, dwell_a, level_b, dwell_b, operation)

    @keyword("Get Load Transient")
    def get_load_transient(self, mode: str) -> dict:
        """Read back the transient parameters of ``mode``."""
        return self.driver.get_transient(mode).as_dict()

    @keyword("Set Load Trigger Source")
    def set_load_trigger_source(self, source: str) -> str:
        """Select ``IMMEDIATE``, ``EXTERNAL`` or ``BUS`` triggering."""
        return self.driver.set_trigger_source(source).name

    @keyword("Get Load Trigger Source")
    def get_load_trigger_source(self) -> str:
        """Return the configured trigger source."""
        return self.driver.get_trigger_source().name

    @keyword("Trigger Load")
    def trigger_load(self) -> None:
        """Issue a software (bus) trigger. Requires trigger source ``BUS``."""
        self.driver.trigger()

    # ------------------------------------------------------------------
    # list operation
    # ------------------------------------------------------------------
    @keyword("Configure Load List")
    def configure_load_list(
        self,
        mode: str,
        steps: list,
        repeat: str = "ONCE",
        name: str | None = None,
    ) -> None:
        """Program a list sequence with the input forced OFF.

        ``steps`` is a list of ``(level, dwell_seconds)`` pairs, for example::

            @{steps}=    Evaluate    [(1.0, 0.5), (2.0, 0.5)]
            Configure Load List    CC    ${steps}    repeat=REPEAT
        """
        normalised = [(float(level), float(dwell)) for level, dwell in steps]
        self.driver.configure_list(mode, normalised, repeat, name)

    @keyword("Get Load List Step")
    def get_load_list_step(self, mode: str, index: int) -> dict:
        """Read back one list step as ``{index, level, dwell_s}``."""
        return self.driver.get_list_step(mode, int(index)).as_dict()

    @keyword("Get Load List Step Count")
    def get_load_list_step_count(self) -> int:
        """Return the programmed number of list steps."""
        return self.driver.get_list_step_count()

    @keyword("Save Load List File")
    def save_load_list_file(self, location: int) -> None:
        """Store the current list into a slot allowed by the active partition."""
        self.driver.save_list_file(int(location))

    @keyword("Recall Load List File")
    def recall_load_list_file(self, location: int) -> None:
        """Load a list from a slot allowed by the active partition."""
        self.driver.recall_list_file(int(location))

    # ------------------------------------------------------------------
    # battery test, timer, storage
    # ------------------------------------------------------------------
    @keyword("Set Battery Cutoff Voltage")
    def set_battery_cutoff_voltage(self, voltage: float) -> None:
        """Set the terminal voltage at which a battery test stops."""
        self.driver.set_battery_cutoff_voltage(voltage)

    @keyword("Get Battery Cutoff Voltage")
    def get_battery_cutoff_voltage(self) -> float:
        """Read the battery test cut-off voltage in volts."""
        return self.driver.get_battery_cutoff_voltage()

    @keyword("Set Load On Timer")
    def set_load_on_timer(self, seconds: float, enabled: bool = True) -> None:
        """Set the LOAD ON timer in whole seconds and enable or disable it."""
        self.driver.set_load_on_timer(seconds)
        self.driver.set_load_on_timer_enabled(enabled)

    @keyword("Get Load On Timer")
    def get_load_on_timer(self) -> dict:
        """Return ``{seconds, enabled}`` for the LOAD ON timer."""
        return {
            "seconds": self.driver.get_load_on_timer(),
            "enabled": self.driver.get_load_on_timer_enabled(),
        }

    @keyword("Save Load Settings")
    def save_load_settings(self, register: int) -> None:
        """Store the present settings into instrument register 1..25."""
        self.driver.save_settings(int(register))

    @keyword("Recall Load Settings")
    def recall_load_settings(self, register: int) -> None:
        """Restore settings from instrument register 1..25."""
        self.driver.recall_settings(int(register))

    # ------------------------------------------------------------------
    # measurement
    # ------------------------------------------------------------------
    @keyword("Measure Load Input")
    def measure_load_input(self) -> dict:
        """Return one reading: voltage, current, power, input state and flags."""
        reading = self.driver.measure().as_dict()
        _rf_logger.info(
            f"V = {reading['voltage_v']:.4f} V, I = {reading['current_a']:.4f} A, "
            f"P = {reading['power_w']:.4f} W, input {'ON' if reading['input_on'] else 'OFF'}"
        )
        return reading

    @keyword("Get Load Voltage")
    def get_load_voltage(self) -> float:
        """Measured terminal voltage in volts."""
        return self.driver.measure().voltage_v

    @keyword("Get Load Current")
    def get_load_current(self) -> float:
        """Measured sink current in amperes."""
        return self.driver.measure().current_a

    @keyword("Get Load Power")
    def get_load_power(self) -> float:
        """Measured input power in watts."""
        return self.driver.measure().power_w

    @keyword("Wait Until Load Reading Is Stable")
    def wait_until_load_reading_is_stable(
        self,
        quantity: str = "current",
        tolerance: float = 0.01,
        window: float = 1.0,
        timeout: float = 10.0,
        interval: float = 0.1,
    ) -> dict:
        """Poll until ``quantity`` stays within ``tolerance`` for ``window`` seconds.

        Fails if the reading has not settled within ``timeout`` seconds.
        """
        return self.driver.wait_until_stable(
            quantity=quantity,
            tolerance=tolerance,
            window_s=window,
            timeout_s=timeout,
            interval_s=interval,
        ).as_dict()

    # ------------------------------------------------------------------
    # verification
    # ------------------------------------------------------------------
    @keyword("Load Voltage Should Be Within")
    def load_voltage_should_be_within(self, expected: float, tolerance: float) -> float:
        """Fail unless the measured voltage is ``expected`` +/- ``tolerance`` volts."""
        return self._compare(self.driver.measure().voltage_v, expected, tolerance, "Voltage", "V")

    @keyword("Load Current Should Be Within")
    def load_current_should_be_within(self, expected: float, tolerance: float) -> float:
        """Fail unless the measured current is ``expected`` +/- ``tolerance`` amperes."""
        return self._compare(self.driver.measure().current_a, expected, tolerance, "Current", "A")

    @keyword("Load Power Should Be Within")
    def load_power_should_be_within(self, expected: float, tolerance: float) -> float:
        """Fail unless the measured power is ``expected`` +/- ``tolerance`` watts."""
        return self._compare(self.driver.measure().power_w, expected, tolerance, "Power", "W")

    @keyword("Load Should Report No Protection Faults")
    def load_should_report_no_protection_faults(self) -> dict:
        """Fail if reverse polarity, OV, OC, OP or OT is asserted."""
        return self.driver.assert_no_protection_faults().as_dict()

    @keyword("Load Input State Should Be")
    def load_input_state_should_be(self, expected: str) -> None:
        """Fail unless the input state matches ``ON`` or ``OFF``."""
        wanted = str(expected).strip().upper() in ("ON", "TRUE", "1", "YES")
        actual = self.driver.measure().input_on
        if actual is not wanted:
            raise BK8500VerificationError(
                f"Load input is {'ON' if actual else 'OFF'}, expected "
                f"{'ON' if wanted else 'OFF'}"
            )

    @keyword("Load Mode Should Be")
    def load_mode_should_be(self, expected: str) -> None:
        """Fail unless the active regulation mode equals ``expected``."""
        wanted = parse_enum(LoadMode, expected, "Mode")
        actual = self.driver.get_mode()
        if actual is not wanted:
            raise BK8500VerificationError(f"Load mode is {actual.name}, expected {wanted.name}")

    # ------------------------------------------------------------------
    # diagnostics
    # ------------------------------------------------------------------
    @keyword("Get Load Connection Info")
    def get_load_connection_info(self) -> dict[str, Any]:
        """Return alias, transport description and rated limits of the current load."""
        transport = self.driver.transport
        return {
            "alias": self._current,
            "transport": transport.description,
            "address": self.driver.address,
            "signal_lines": getattr(transport, "signal_lines", {"dtr": None, "rts": None}),
            "response_style": self.driver.response_style,
            "baudrate": getattr(transport, "baudrate", None),
            "baudrate_auto_detected": bool(self.driver.baudrate_probe_attempts),
            "baudrate_probe_attempts": list(self.driver.baudrate_probe_attempts),
            "limits": self.get_load_rated_limits(),
            "open_aliases": sorted(self._connections),
        }

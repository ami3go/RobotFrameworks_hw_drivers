"""Robot Framework keyword adapter for the climate-chamber Python driver.

The adapter is intentionally thin: protocol and hardware behavior stay in
:mod:`votsch_climate_chamber.driver`; this module translates Robot arguments,
manages suite lifecycle, adds readable keywords, and reports useful failures.
"""

from __future__ import annotations

import math
from typing import Any

from robot.api import logger
from robot.api.deco import keyword, library
from robot.utils import is_truthy, timestr_to_secs  # type: ignore[import-untyped]

from .driver import (
    ClimateChamber,
    ClimateChamberError,
    ClimateChamberSafetyError,
)
from .robot_logging import create_robot_logger
from .version import PEP440_VERSION, RELEASE_VERSION


@library(scope="SUITE", auto_keywords=False, version=PEP440_VERSION)
class VotschClimateChamberLibrary:
    """Control a Vötsch/SimServ-compatible climate chamber over TCP.

    Importing this library never opens a network connection.  A suite must call
    ``Connect Climate Chamber`` explicitly, normally from ``Suite Setup``.

    The default library scope is ``SUITE``: tests in one suite share one chamber
    session, while separate suites receive separate adapter instances.
    """

    ROBOT_LIBRARY_DOC_FORMAT = "ROBOT"

    def __init__(
        self,
        default_timeout: str | float = "1 second",
        default_response_timeout: str | float | None = None,
        verify_writes: bool | str = True,
        stop_on_close: bool | str = False,
        progress_log_interval: str | float = "30 seconds",
    ) -> None:
        """Configure adapter defaults without contacting chamber hardware."""
        self._default_timeout = self._seconds(default_timeout, "default_timeout", positive=True)
        self._default_response_timeout = (
            None
            if default_response_timeout is None
            else self._seconds(default_response_timeout, "default_response_timeout", positive=True)
        )
        self._verify_writes = self._boolean(verify_writes, "verify_writes")
        self._stop_on_close = self._boolean(stop_on_close, "stop_on_close")
        self._progress_log_interval = self._seconds(
            progress_log_interval, "progress_log_interval", positive=True
        )
        self._driver: ClimateChamber | None = None
        # The attribute is intentionally replaceable in unit tests. Production
        # code leaves it pointing at the real driver class.
        self._driver_factory: type[ClimateChamber] = ClimateChamber
        self._last_progress_log = -math.inf

    # ------------------------------------------------------------------
    # Internal helpers. auto_keywords=False keeps these out of Robot API.
    # ------------------------------------------------------------------

    @staticmethod
    def _seconds(value: str | float | int, name: str, *, positive: bool = False) -> float:
        """Convert numeric seconds or Robot time text into finite seconds."""
        try:
            seconds = float(value) if isinstance(value, (int, float)) else float(timestr_to_secs(str(value)))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"<{name}> must be a valid Robot time value, received {value!r}.") from exc
        if not math.isfinite(seconds):
            raise ValueError(f"<{name}> must be finite, received {value!r}.")
        if positive and seconds <= 0:
            raise ValueError(f"<{name}> must be greater than 0, received {value!r}.")
        if not positive and seconds < 0:
            raise ValueError(f"<{name}> must be greater than or equal to 0, received {value!r}.")
        return seconds

    @staticmethod
    def _boolean(value: bool | str | int, name: str) -> bool:
        """Convert Robot boolean syntax while rejecting unclear values."""
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and value in (0, 1):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().upper()
            accepted = {"TRUE", "YES", "ON", "1", "FALSE", "NO", "OFF", "0", "NONE", ""}
            if normalized in accepted:
                return bool(is_truthy(value))
        raise ValueError(f"<{name}> must be a Robot boolean value, received {value!r}.")

    @staticmethod
    def _float(value: Any, name: str) -> float:
        if isinstance(value, bool):
            raise TypeError(f"<{name}> must be numeric, received bool.")
        try:
            result = float(value)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"<{name}> must be numeric, received {value!r}.") from exc
        if not math.isfinite(result):
            raise ValueError(f"<{name}> must be finite, received {value!r}.")
        return result

    @staticmethod
    def _integer(value: Any, name: str, *, minimum: int | None = None) -> int:
        try:
            result = int(value)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"<{name}> must be an integer, received {value!r}.") from exc
        if minimum is not None and result < minimum:
            raise ValueError(f"<{name}> must be >= {minimum}, received {result!r}.")
        return result

    def _require_driver(self) -> ClimateChamber:
        if self._driver is None:
            raise ClimateChamberError(
                "Climate chamber is not connected. Run 'Connect Climate Chamber' first."
            )
        return self._driver

    def _progress_callback(self, state: dict[str, Any]) -> None:
        """Rate-limit temperature progress messages in potentially long runs."""
        elapsed = float(state.get("elapsed_seconds", 0.0))
        stable = int(state.get("stable_count", 0))
        required = int(state.get("stable_samples", 1))
        should_log = (
            elapsed - self._last_progress_log >= self._progress_log_interval
            or stable == required
            or (stable > 0 and stable == 1)
        )
        if should_log:
            logger.info(
                f"Temperature {float(state['temperature']):.2f} °C; "
                f"target {float(state['target']):.2f} °C ± {float(state['tolerance']):.2f} °C; "
                f"stable samples {stable}/{required}; elapsed {elapsed:.1f} s."
            )
            self._last_progress_log = elapsed

    def _dwell_progress_callback(self, state: dict[str, Any]) -> None:
        elapsed = float(state.get("elapsed_seconds", 0.0))
        remaining = float(state.get("remaining_seconds", 0.0))
        if elapsed - self._last_progress_log >= self._progress_log_interval or remaining <= 0:
            logger.info(
                f"Dwell temperature {float(state['temperature']):.2f} °C; "
                f"{remaining:.1f} s remaining."
            )
            self._last_progress_log = elapsed

    @staticmethod
    def _sanitize(value: Any) -> Any:
        """Convert driver data into Robot-log-friendly scalar containers."""
        if isinstance(value, bytes):
            return value.decode("latin-1", errors="backslashreplace")
        if isinstance(value, dict):
            return {str(k): VotschClimateChamberLibrary._sanitize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [VotschClimateChamberLibrary._sanitize(v) for v in value]
        return value

    # ------------------------------------------------------------------
    # Public Robot Framework keywords.
    # ------------------------------------------------------------------

    @keyword("Get Climate Chamber Library Version")
    def get_library_version(self) -> str:
        """Return the human-facing library release label, for example ``v26.02``."""
        return RELEASE_VERSION

    @keyword("Connect Climate Chamber")
    def connect_climate_chamber(
        self,
        ip: str,
        temperature_min: float,
        temperature_max: float,
        port: int = 2049,
        timeout: str | float | None = None,
        response_timeout: str | float | None = None,
        retries: int = 2,
        retry_delay: str | float = "500 milliseconds",
        verify_writes: bool | str | None = None,
        tcp_keepalive: bool | str = True,
        replace_existing: bool | str = False,
    ) -> str:
        """Connect to a chamber and return its identification string.

        ``temperature_min`` and ``temperature_max`` are local software safety
        limits.  Any later setpoint outside this range is rejected before a
        command is sent.
        """
        replace = self._boolean(replace_existing, "replace_existing")
        if self._driver is not None:
            if not replace:
                raise ClimateChamberError(
                    "A climate chamber session already exists. Disconnect it first or set replace_existing=True."
                )
            self.disconnect_climate_chamber(stop=False)

        effective_timeout = self._default_timeout if timeout is None else self._seconds(timeout, "timeout", positive=True)
        if response_timeout is None:
            effective_response_timeout = self._default_response_timeout or effective_timeout
        else:
            effective_response_timeout = self._seconds(response_timeout, "response_timeout", positive=True)
        effective_verify = self._verify_writes if verify_writes is None else self._boolean(verify_writes, "verify_writes")

        driver = self._driver_factory(
            ip=str(ip),
            temperature_min=self._float(temperature_min, "temperature_min"),
            temperature_max=self._float(temperature_max, "temperature_max"),
            timeout=effective_timeout,
            port=self._integer(port, "port", minimum=1),
            retries=self._integer(retries, "retries", minimum=0),
            retry_delay=self._seconds(retry_delay, "retry_delay"),
            response_timeout=effective_response_timeout,
            verify_writes=effective_verify,
            tcp_keepalive=self._boolean(tcp_keepalive, "tcp_keepalive"),
            connect_on_init=False,
            logger=create_robot_logger(),
        )
        try:
            driver.connect()
            driver.verify_connection()
            identification = driver.idn
        except Exception:
            driver.disconnect()
            raise
        self._driver = driver
        logger.info(f"Connected to {identification} at {ip}:{port}.")
        return identification

    @keyword("Disconnect Climate Chamber")
    def disconnect_climate_chamber(self, stop: bool | str | None = None, strict: bool | str = False) -> None:
        """Optionally stop and then disconnect. The keyword is idempotent by default."""
        if self._driver is None:
            if self._boolean(strict, "strict"):
                raise ClimateChamberError("Climate chamber is already disconnected.")
            return
        effective_stop = self._stop_on_close if stop is None else self._boolean(stop, "stop")
        driver = self._driver
        try:
            if effective_stop:
                driver.stop()
        finally:
            driver.disconnect()
            self._driver = None
        logger.info("Climate chamber disconnected.")

    @keyword("Stop And Disconnect Climate Chamber")
    def stop_and_disconnect_climate_chamber(self) -> None:
        """Safety teardown that always attempts both stop and disconnect."""
        if self._driver is None:
            return
        driver = self._driver
        stop_error: BaseException | None = None
        disconnect_error: BaseException | None = None
        try:
            driver.stop()
        except BaseException as exc:  # preserve teardown even after non-standard driver failures
            stop_error = exc
            logger.warn(f"Failed to stop climate chamber during teardown: {exc}")
        try:
            driver.disconnect()
        except BaseException as exc:
            disconnect_error = exc
        finally:
            self._driver = None

        if stop_error or disconnect_error:
            details = []
            if stop_error:
                details.append(f"stop failed: {stop_error}")
            if disconnect_error:
                details.append(f"disconnect failed: {disconnect_error}")
            raise ClimateChamberError("Stop and disconnect did not complete cleanly; " + "; ".join(details))
        logger.info("Climate chamber stopped and disconnected.")

    @keyword("Reconnect Climate Chamber")
    def reconnect_climate_chamber(self) -> bool:
        """Reconnect the existing session and verify chamber communication."""
        driver = self._require_driver()
        driver.reconnect()
        result = driver.verify_connection()
        logger.info("Climate chamber reconnected and communication verified.")
        return result

    @keyword("Climate Chamber Should Be Connected")
    def climate_chamber_should_be_connected(self) -> None:
        """Fail unless a real status query succeeds."""
        self._require_driver().verify_connection()

    @keyword("Get Climate Chamber Connection Statistics")
    def get_connection_statistics(self) -> dict[str, Any]:
        """Return communication counters and the last response as a dictionary."""
        return self._sanitize(self._require_driver().communication_stats)

    @keyword("Get Climate Chamber Identification")
    def get_identification(self) -> str:
        """Return model, serial number, and manufacturing year."""
        return self._require_driver().idn

    @keyword("Get Climate Chamber Serial Number")
    def get_serial_number(self) -> str:
        return str(self._require_driver().serial_number)

    @keyword("Get Climate Chamber Model")
    def get_model(self) -> str:
        return str(self._require_driver().test_system_type)

    @keyword("Get Climate Chamber Manufacturing Year")
    def get_manufacturing_year(self) -> str:
        return str(self._require_driver().year_manufactured)

    @keyword("Get Climate Chamber Status")
    def get_status(self) -> str:
        return str(self._require_driver().chamber_status)

    @keyword("Get Climate Chamber Health")
    def get_health(self) -> dict[str, Any]:
        """Return identification, state, temperatures, status, and communication counters."""
        return self._sanitize(self._require_driver().health_check())

    @keyword("Set Climate Chamber Temperature")
    def set_temperature(self, celsius: float) -> float:
        """Set and verify a temperature setpoint in degrees Celsius."""
        driver = self._require_driver()
        target = self._float(celsius, "celsius")
        driver.temperature_set_point = target
        logger.info(f"Climate chamber setpoint changed to {target:.2f} °C.")
        return driver.temperature_set_point

    @keyword("Get Climate Chamber Setpoint")
    def get_setpoint(self) -> float:
        return float(self._require_driver().temperature_set_point)

    @keyword("Get Climate Chamber Temperature")
    def get_temperature(self) -> float:
        return float(self._require_driver().temperature_measured)

    @keyword("Set Climate Chamber Temperature Limits")
    def set_temperature_limits(self, minimum: float, maximum: float) -> dict[str, float]:
        """Change local software safety limits without changing chamber setpoint."""
        driver = self._require_driver()
        new_min = self._float(minimum, "minimum")
        new_max = self._float(maximum, "maximum")
        if new_min >= new_max:
            raise ClimateChamberSafetyError(
                f"Invalid temperature limits: minimum {new_min} °C must be below maximum {new_max} °C."
            )
        # Choose assignment order so each intermediate state is valid.
        if new_min >= driver.temperature_max:
            driver.temperature_max = new_max
            driver.temperature_min = new_min
        elif new_max <= driver.temperature_min:
            driver.temperature_min = new_min
            driver.temperature_max = new_max
        else:
            driver.temperature_min = new_min
            driver.temperature_max = new_max
        logger.info(f"Local temperature limits changed to {new_min:.2f}…{new_max:.2f} °C.")
        return {"minimum": driver.temperature_min, "maximum": driver.temperature_max}

    @keyword("Get Climate Chamber Temperature Limits")
    def get_temperature_limits(self) -> dict[str, float]:
        driver = self._require_driver()
        return {"minimum": float(driver.temperature_min), "maximum": float(driver.temperature_max)}

    @keyword("Start Climate Chamber")
    def start_climate_chamber(self) -> None:
        self._require_driver().start()
        logger.info("Climate chamber started.")

    @keyword("Stop Climate Chamber")
    def stop_climate_chamber(self) -> None:
        self._require_driver().stop()
        logger.info("Climate chamber stopped.")

    @keyword("Set Temperature And Wait")
    def set_temperature_and_wait(
        self,
        target: float,
        dwell: str | float = "0 seconds",
        tolerance: float = 0.8,
        poll_interval: str | float = "10 seconds",
        timeout: str | float = "4 hours",
        stable_samples: int = 1,
        start_chamber: bool | str = True,
    ) -> float:
        """Set, optionally start, stabilize, dwell, and return final temperature."""
        driver = self._require_driver()
        target_value = self._float(target, "target")
        tolerance_value = self._float(tolerance, "tolerance")
        poll_seconds = self._seconds(poll_interval, "poll_interval", positive=True)
        timeout_seconds = self._seconds(timeout, "timeout", positive=True)
        dwell_seconds = self._seconds(dwell, "dwell")
        samples = self._integer(stable_samples, "stable_samples", minimum=1)
        driver.temperature_set_point = target_value
        if self._boolean(start_chamber, "start_chamber"):
            driver.start()
        self._last_progress_log = -math.inf
        final = driver.wait_until_temperature(
            target_value,
            tolerance=tolerance_value,
            wait_period=poll_seconds,
            timeout=timeout_seconds,
            stable_samples=samples,
            progress_callback=self._progress_callback,
        )
        if dwell_seconds > 0:
            self._last_progress_log = -math.inf
            final = driver.dwell(
                dwell_seconds,
                poll_interval=min(max(poll_seconds, 0.1), 60.0),
                progress_callback=self._dwell_progress_callback,
            )
        logger.info(f"Temperature sequence complete at {final:.2f} °C.")
        return float(final)

    @keyword("Wait Until Climate Chamber Is Stable")
    def wait_until_stable(
        self,
        target: float | None = None,
        tolerance: float = 0.8,
        poll_interval: str | float = "10 seconds",
        timeout: str | float = "4 hours",
        stable_samples: int = 1,
        start_chamber: bool | str = False,
    ) -> float:
        """Wait for consecutive in-tolerance samples without changing setpoint."""
        driver = self._require_driver()
        if self._boolean(start_chamber, "start_chamber"):
            driver.start()
        target_value = None if target is None else self._float(target, "target")
        self._last_progress_log = -math.inf
        return float(
            driver.wait_until_temperature(
                target_value,
                tolerance=self._float(tolerance, "tolerance"),
                wait_period=self._seconds(poll_interval, "poll_interval", positive=True),
                timeout=self._seconds(timeout, "timeout", positive=True),
                stable_samples=self._integer(stable_samples, "stable_samples", minimum=1),
                progress_callback=self._progress_callback,
            )
        )

    @keyword("Wait For Climate Chamber Dwell")
    def wait_for_dwell(
        self,
        duration: str | float,
        poll_interval: str | float = "1 minute",
    ) -> float:
        """Dwell for a finite period while logging the current temperature."""
        self._last_progress_log = -math.inf
        return float(
            self._require_driver().dwell(
                self._seconds(duration, "duration"),
                poll_interval=self._seconds(poll_interval, "poll_interval", positive=True),
                progress_callback=self._dwell_progress_callback,
            )
        )

    @keyword("Set Climate Chamber Heating Gradient")
    def set_heating_gradient(self, celsius_per_minute: float) -> float:
        driver = self._require_driver()
        driver.gradient_up = self._float(celsius_per_minute, "celsius_per_minute")
        return float(driver.gradient_up)

    @keyword("Get Climate Chamber Heating Gradient")
    def get_heating_gradient(self) -> float:
        return float(self._require_driver().gradient_up)

    @keyword("Set Climate Chamber Cooling Gradient")
    def set_cooling_gradient(self, celsius_per_minute: float) -> float:
        driver = self._require_driver()
        driver.gradient_down = self._float(celsius_per_minute, "celsius_per_minute")
        return float(driver.gradient_down)

    @keyword("Get Climate Chamber Cooling Gradient")
    def get_cooling_gradient(self) -> float:
        return float(self._require_driver().gradient_down)

    @keyword("Set Climate Chamber Dryer")
    def set_dryer(self, enabled: bool | str) -> bool:
        driver = self._require_driver()
        driver.dryer = self._boolean(enabled, "enabled")
        return bool(driver.dryer)

    @keyword("Get Climate Chamber Dryer")
    def get_dryer(self) -> bool:
        return bool(self._require_driver().dryer)

    @keyword("Set Climate Chamber Compressed Air")
    def set_compressed_air(self, enabled: bool | str) -> bool:
        driver = self._require_driver()
        driver.compressed_air = self._boolean(enabled, "enabled")
        return bool(driver.compressed_air)

    @keyword("Get Climate Chamber Compressed Air")
    def get_compressed_air(self) -> bool:
        return bool(self._require_driver().compressed_air)

    @keyword("Climate Chamber Temperature Should Be")
    def temperature_should_be(self, expected: float, tolerance: float = 0.1) -> None:
        """Assert measured temperature equals expected within ±tolerance °C."""
        actual = self.get_temperature()
        expected_value = self._float(expected, "expected")
        tolerance_value = self._float(tolerance, "tolerance")
        if tolerance_value < 0:
            raise ValueError("<tolerance> must be >= 0.")
        if abs(actual - expected_value) > tolerance_value:
            raise AssertionError(
                f"Climate chamber temperature mismatch: expected {expected_value:.2f} °C ± "
                f"{tolerance_value:.2f} °C, actual {actual:.2f} °C."
            )

    @keyword("Climate Chamber Temperature Should Be Within")
    def temperature_should_be_within(self, minimum: float, maximum: float) -> None:
        """Assert measured temperature lies inside an inclusive range."""
        low = self._float(minimum, "minimum")
        high = self._float(maximum, "maximum")
        if low > high:
            raise ValueError(f"<minimum> {low} must not exceed <maximum> {high}.")
        actual = self.get_temperature()
        if not low <= actual <= high:
            raise AssertionError(
                f"Climate chamber temperature {actual:.2f} °C is outside {low:.2f}…{high:.2f} °C."
            )

    @keyword("Climate Chamber Setpoint Should Be")
    def setpoint_should_be(self, expected: float, tolerance: float = 0.05) -> None:
        actual = self.get_setpoint()
        expected_value = self._float(expected, "expected")
        tolerance_value = self._float(tolerance, "tolerance")
        if tolerance_value < 0:
            raise ValueError("<tolerance> must be >= 0.")
        if abs(actual - expected_value) > tolerance_value:
            raise AssertionError(
                f"Climate chamber setpoint mismatch: expected {expected_value:.2f} °C ± "
                f"{tolerance_value:.2f} °C, actual {actual:.2f} °C."
            )

    @keyword("Climate Chamber Should Be Running")
    def chamber_should_be_running(self) -> None:
        if not self._require_driver().is_running:
            raise AssertionError("Climate chamber should be running, but it is stopped.")

    @keyword("Climate Chamber Should Be Stopped")
    def chamber_should_be_stopped(self) -> None:
        if self._require_driver().is_running:
            raise AssertionError("Climate chamber should be stopped, but it is running.")

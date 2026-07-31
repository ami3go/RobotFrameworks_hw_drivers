"""Robot Framework keyword library for two PhidgetInterfaceKit 0/0/4 boards.

Logical channels 1..4 map to device A outputs 0..3. Logical channels 5..8
map to device B outputs 0..3. Device serial numbers are required so USB
enumeration order can never change the logical wiring.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

try:
    from robot.api import logger
    from robot.api.deco import keyword, library
except ImportError:  # Allows lightweight unit testing without Robot Framework.
    class _Logger:
        def info(self, message: str) -> None:
            pass

        def warn(self, message: str) -> None:
            pass

    logger = _Logger()

    def keyword(name: Optional[str] = None):
        def decorate(function):
            return function
        return decorate

    def library(**_kwargs):
        return lambda cls: cls


def _to_bool(value: Any, name: str = "value") -> bool:
    """Convert common Robot scalar values to bool without Python's 'False' trap."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on", "closed", "energized"}:
            return True
        if normalized in {"false", "0", "no", "off", "open", "de-energized", "deenergized"}:
            return False
    raise ValueError(f"{name} must be a boolean or one of ON/OFF, OPEN/CLOSED, 1/0")


@library(scope="SUITE", version="26.2", auto_keywords=False)
class PhidgetRelayLibrary:
    """Control eight relays implemented by two four-output Phidget boards.

    Import with ``Library    rf_phidget_relay.PhidgetRelayLibrary``. Call
    ``Connect Relays`` before accessing channels and ``Disconnect Relays`` in
    suite teardown. By default, connecting and disconnecting de-energize all
    relays. ``active_high=False`` supports external relay hardware whose input
    logic is inverted.
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = "26.2"
    CHANNEL_COUNT = 8

    def __init__(
        self,
        active_high: Any = True,
        output_factory: Optional[Callable[[], Any]] = None,
        sleep_function: Callable[[float], None] = time.sleep,
    ) -> None:
        self._active_high = _to_bool(active_high, "active_high")
        self._output_factory = output_factory
        self._sleep = sleep_function
        self._outputs: Dict[int, Any] = {}
        self._serials: Optional[Tuple[int, int]] = None

    def _factory(self) -> Any:
        if self._output_factory is not None:
            return self._output_factory()
        try:
            from Phidget22.Devices.DigitalOutput import DigitalOutput
        except ImportError as exc:
            raise RuntimeError(
                "Phidget22 is not installed. Run: python -m pip install Phidget22"
            ) from exc
        return DigitalOutput()

    @staticmethod
    def _channel(value: Any) -> int:
        try:
            channel = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Relay channel must be an integer from 1 to 8, got {value!r}") from exc
        if channel < 1 or channel > 8:
            raise ValueError(f"Relay channel must be from 1 to 8, got {channel}")
        return channel

    def _require_connected(self) -> None:
        if len(self._outputs) != self.CHANNEL_COUNT:
            raise RuntimeError("Relay bank is not connected. Call 'Connect Relays' first.")

    @staticmethod
    def _physical_address(logical_channel: int, serial_a: int, serial_b: int) -> Tuple[int, int]:
        if logical_channel <= 4:
            return serial_a, logical_channel - 1
        return serial_b, logical_channel - 5

    def _write(self, channel: int, closed: bool) -> None:
        physical_state = closed if self._active_high else not closed
        self._outputs[channel].setState(physical_state)
        logger.info(f"Relay CH{channel} set to {'CLOSED' if closed else 'OPEN'}")

    @keyword("Connect Relays")
    def connect_relays(
        self,
        device_a_serial: Any,
        device_b_serial: Any,
        timeout_ms: Any = 5000,
        open_all_on_connect: Any = True,
    ) -> None:
        """Attach all outputs using two unique Phidget serial numbers.

        Device A becomes logical CH1..CH4; device B becomes CH5..CH8.
        If any output fails to attach, already-opened handles are closed and
        this keyword fails. ``timeout_ms`` applies to each output attachment.
        """
        if self._outputs:
            raise RuntimeError("Relay bank is already connected; disconnect it first")
        serial_a, serial_b = int(device_a_serial), int(device_b_serial)
        timeout = int(timeout_ms)
        if serial_a <= 0 or serial_b <= 0:
            raise ValueError("Both Phidget serial numbers must be positive integers")
        if serial_a == serial_b:
            raise ValueError("Device A and device B must have different serial numbers")
        if timeout <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        make_safe = _to_bool(open_all_on_connect, "open_all_on_connect")

        opened: Dict[int, Any] = {}
        try:
            for logical in range(1, self.CHANNEL_COUNT + 1):
                serial, physical = self._physical_address(logical, serial_a, serial_b)
                output = self._factory()
                # Track immediately so every vendor-API failure path closes it.
                opened[logical] = output
                output.setDeviceSerialNumber(serial)
                output.setChannel(physical)
                output.openWaitForAttachment(timeout)
                if make_safe:
                    # Establish the safe state as soon as each output attaches,
                    # rather than waiting for all eight channels to attach.
                    output.setState(False if self._active_high else True)
            self._outputs = opened
            self._serials = (serial_a, serial_b)
            logger.info(f"Connected relay devices {serial_a} and {serial_b}")
        except Exception:
            for output in opened.values():
                try:
                    output.close()
                except Exception:
                    pass
            self._outputs = {}
            self._serials = None
            raise

    @keyword("Disconnect Relays")
    def disconnect_relays(self, open_all_before_disconnect: Any = True) -> None:
        """Optionally open every relay, then close all Phidget handles."""
        errors: List[str] = []
        if self._outputs and _to_bool(open_all_before_disconnect, "open_all_before_disconnect"):
            try:
                self.open_all_relays()
            except Exception as exc:
                errors.append(f"could not open every relay: {exc}")
        for channel, output in list(self._outputs.items()):
            try:
                output.close()
            except Exception as exc:
                errors.append(f"CH{channel} close failed: {exc}")
        self._outputs = {}
        self._serials = None
        if errors:
            raise RuntimeError("; ".join(errors))

    @keyword("Set Relay State")
    def set_relay_state(self, channel: Any, closed: Any) -> None:
        """Set one logical relay OPEN/OFF or CLOSED/ON."""
        self._require_connected()
        logical = self._channel(channel)
        self._write(logical, _to_bool(closed, "closed"))

    @keyword("Open Relay")
    def open_relay(self, channel: Any) -> None:
        """De-energize/open one logical relay."""
        self.set_relay_state(channel, False)

    @keyword("Close Relay")
    def close_relay(self, channel: Any) -> None:
        """Energize/close one logical relay."""
        self.set_relay_state(channel, True)

    @keyword("Get Relay State")
    def get_relay_state(self, channel: Any) -> str:
        """Return ``OPEN`` or ``CLOSED`` from the Phidget output state."""
        self._require_connected()
        logical = self._channel(channel)
        physical = bool(self._outputs[logical].getState())
        closed = physical if self._active_high else not physical
        return "CLOSED" if closed else "OPEN"

    @keyword("Relay Should Be Open")
    def relay_should_be_open(self, channel: Any) -> None:
        """Fail unless the selected output reports OPEN."""
        actual = self.get_relay_state(channel)
        if actual != "OPEN":
            raise AssertionError(f"Relay CH{self._channel(channel)} expected OPEN, got {actual}")

    @keyword("Relay Should Be Closed")
    def relay_should_be_closed(self, channel: Any) -> None:
        """Fail unless the selected output reports CLOSED."""
        actual = self.get_relay_state(channel)
        if actual != "CLOSED":
            raise AssertionError(f"Relay CH{self._channel(channel)} expected CLOSED, got {actual}")

    @keyword("Open All Relays")
    def open_all_relays(self) -> None:
        """Open all eight relays; attempts every channel before reporting failures."""
        self._set_all(False)

    @keyword("Close All Relays")
    def close_all_relays(self) -> None:
        """Close all eight relays; use only when the connected circuit permits it."""
        self._set_all(True)

    def _set_all(self, closed: bool) -> None:
        self._require_connected()
        errors: List[str] = []
        for logical in range(1, self.CHANNEL_COUNT + 1):
            try:
                self._write(logical, closed)
            except Exception as exc:
                errors.append(f"CH{logical}: {exc}")
        if errors:
            raise RuntimeError("Failed to set all relays: " + "; ".join(errors))

    @keyword("Set Relay Pattern")
    def set_relay_pattern(self, pattern: Any) -> None:
        """Apply eight states from an 8-character binary string, e.g. ``10000001``.

        Leftmost digit controls CH1. All values are validated before any output
        changes. Outputs are then written CH1 through CH8.
        """
        self._require_connected()
        value = str(pattern).strip()
        if len(value) != 8 or any(char not in "01" for char in value):
            raise ValueError("Relay pattern must contain exactly eight binary digits")
        for logical, char in enumerate(value, start=1):
            self._write(logical, char == "1")

    @keyword("Set Multiple Relays")
    def set_multiple_relays(self, states: Mapping[Any, Any]) -> None:
        """Apply a Robot dictionary such as ``&{states}    1=ON    8=OFF``.

        The complete dictionary is validated before the first hardware write.
        """
        self._require_connected()
        if not isinstance(states, Mapping):
            raise TypeError("states must be a Robot/Python dictionary")
        validated = [(self._channel(ch), _to_bool(state, f"state for CH{ch}")) for ch, state in states.items()]
        if len({channel for channel, _ in validated}) != len(validated):
            raise ValueError("states contains duplicate logical channels")
        for channel, closed in validated:
            self._write(channel, closed)

    @keyword("Get All Relay States")
    def get_all_relay_states(self) -> Dict[int, str]:
        """Return a dictionary mapping logical channel numbers to OPEN/CLOSED."""
        self._require_connected()
        return {channel: self.get_relay_state(channel) for channel in range(1, 9)}

    @keyword("Pulse Relay")
    def pulse_relay(self, channel: Any, duration_seconds: Any = 0.5) -> None:
        """Close a relay for a duration and always attempt to open it afterward."""
        logical = self._channel(channel)
        duration = float(duration_seconds)
        if duration < 0:
            raise ValueError("duration_seconds must not be negative")
        self.close_relay(logical)
        try:
            self._sleep(duration)
        finally:
            self.open_relay(logical)

    @keyword("Get Relay Mapping")
    def get_relay_mapping(self) -> Dict[int, str]:
        """Return human-readable logical-to-physical mapping for the active connection."""
        self._require_connected()
        assert self._serials is not None
        serial_a, serial_b = self._serials
        return {
            logical: f"serial={serial}, output={physical}"
            for logical in range(1, 9)
            for serial, physical in [self._physical_address(logical, serial_a, serial_b)]
        }

    @keyword("Get Connection Status")
    def get_connection_status(self) -> str:
        """Return ``CONNECTED`` only when all eight handles are active."""
        return "CONNECTED" if len(self._outputs) == self.CHANNEL_COUNT else "DISCONNECTED"

    @keyword("Get Driver Information")
    def get_driver_information(self) -> Dict[str, Any]:
        """Return stable driver identity and runtime state for test evidence."""
        return {
            "name": "rf_phidget_relay",
            "version": self.ROBOT_LIBRARY_VERSION,
            "logical_channels": self.CHANNEL_COUNT,
            "connection_status": self.get_connection_status(),
            "device_serials": list(self._serials) if self._serials else [],
            "active_high": self._active_high,
        }

    @keyword("Emergency Open All Relays")
    def emergency_open_all_relays(self) -> None:
        """Attempt the safe state on every channel and aggregate failures."""
        self.open_all_relays()

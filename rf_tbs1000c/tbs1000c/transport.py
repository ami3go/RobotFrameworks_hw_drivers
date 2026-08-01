"""Transport layer: USBTMC (via pyvisa) and the in-process simulator.

Per RFDS-004, protocol/driver code never touches pyvisa/usb directly outside
this module. Both backends expose the same three operations so ``driver.py``
never needs to know which one it's talking to.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .exceptions import Tbs1000cConnectionError, Tbs1000cTimeoutError

if TYPE_CHECKING:
    from .simulator import SimTbs1000cInstrument


class Transport(Protocol):
    """Byte-oriented boundary every backend implements identically."""

    resource: str

    def open(self) -> None: ...

    def close(self) -> None: ...

    def is_open(self) -> bool: ...

    def write(self, command: str) -> None: ...

    def query(self, command: str) -> str: ...

    def query_binary(self, command: str) -> bytes: ...

    @property
    def timeout_s(self) -> float: ...

    @timeout_s.setter
    def timeout_s(self, value: float) -> None: ...


class PyvisaUsbtmcTransport:
    """USBTMC transport over `pyvisa`.

    Import is deferred to :meth:`open` so this module (and the whole package)
    stays importable without ``pyvisa`` installed when only the simulator is
    used — no device I/O happens at import time either way.
    """

    def __init__(self, resource: str, timeout_s: float = 5.0) -> None:
        if not resource or not str(resource).strip():
            raise Tbs1000cConnectionError("a VISA resource string is required for USBTMC")
        self.resource = str(resource).strip()
        self._timeout_s = float(timeout_s)
        self._instrument = None

    def open(self) -> None:
        try:
            import pyvisa
        except ImportError as exc:  # pragma: no cover - exercised only without the extra installed
            raise Tbs1000cConnectionError(
                "pyvisa is not installed; install rf_tbs1000c[usbtmc] for real hardware"
            ) from exc
        try:
            manager = pyvisa.ResourceManager()
            self._instrument = manager.open_resource(self.resource)
            self._instrument.timeout = self._timeout_s * 1000.0
        except Exception as exc:  # pyvisa raises its own exception types
            raise Tbs1000cConnectionError(
                f"could not open USBTMC resource {self.resource!r}: {exc}"
            ) from exc

    def close(self) -> None:
        if self._instrument is not None:
            self._instrument.close()
            self._instrument = None

    def is_open(self) -> bool:
        return self._instrument is not None

    def _require_open(self):
        if self._instrument is None:
            raise Tbs1000cConnectionError("transport is not open")
        return self._instrument

    def write(self, command: str) -> None:
        instrument = self._require_open()
        try:
            instrument.write(command)
        except Exception as exc:
            raise Tbs1000cTimeoutError(f"write failed for {command!r}: {exc}") from exc

    def query(self, command: str) -> str:
        instrument = self._require_open()
        try:
            return str(instrument.query(command)).strip()
        except Exception as exc:
            raise Tbs1000cTimeoutError(f"query failed for {command!r}: {exc}") from exc

    def query_binary(self, command: str) -> bytes:
        instrument = self._require_open()
        try:
            instrument.write(command)
            return bytes(instrument.read_raw())
        except Exception as exc:
            raise Tbs1000cTimeoutError(f"binary query failed for {command!r}: {exc}") from exc

    @property
    def timeout_s(self) -> float:
        return self._timeout_s

    @timeout_s.setter
    def timeout_s(self, value: float) -> None:
        self._timeout_s = float(value)
        if self._instrument is not None:
            self._instrument.timeout = self._timeout_s * 1000.0


class SimulatedTransport:
    """Wraps a :class:`~tbs1000c.simulator.SimTbs1000cInstrument`.

    Every command — write or query, text or binary — goes through the
    simulator's single ``dispatch`` entry point, so the real SCPI strings
    built by ``driver.py`` are exercised exactly as they would be against
    hardware; nothing here special-cases individual commands.
    """

    def __init__(self, simulator: SimTbs1000cInstrument | None = None) -> None:
        if simulator is None:
            from .simulator import SimTbs1000cInstrument

            simulator = SimTbs1000cInstrument()
        self._simulator = simulator
        self.resource = "SIM::default"
        self._open = False
        self._timeout_s = 5.0

    def open(self) -> None:
        self._open = True

    def close(self) -> None:
        self._open = False

    def is_open(self) -> bool:
        return self._open

    def _require_open(self) -> None:
        if not self._open:
            raise Tbs1000cConnectionError("transport is not open")

    def write(self, command: str) -> None:
        self._require_open()
        self._simulator.dispatch(command)

    def query(self, command: str) -> str:
        self._require_open()
        return self._simulator.dispatch(command).decode("ascii", errors="replace").strip()

    def query_binary(self, command: str) -> bytes:
        self._require_open()
        return self._simulator.dispatch(command)

    @property
    def timeout_s(self) -> float:
        return self._timeout_s

    @timeout_s.setter
    def timeout_s(self, value: float) -> None:
        self._timeout_s = float(value)

    @property
    def simulator(self) -> SimTbs1000cInstrument:
        """Direct access for tests that need to inspect/drive simulator state."""
        return self._simulator

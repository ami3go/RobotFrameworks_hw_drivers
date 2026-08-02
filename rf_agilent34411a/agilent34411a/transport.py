"""Transport layer: VISA (via pyvisa) and the in-process simulator.

Per RFDS-004, protocol/driver code never touches pyvisa directly outside
this module. Like ``rf_agilent33220a``, GPIB/USB/LAN are all standard on
this instrument and all reachable through one VISA resource string, so
there is only one hardware backend here, not one per interface (task §5).
Every command this driver issues is plain text — reading transfer stays
ASCII-only for Gate 2 (task §2, ``FORMat[:DATA]``), so no binary transport
path is needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .exceptions import Agilent34411AConnectionError, Agilent34411ATimeoutError

if TYPE_CHECKING:
    from .simulator import SimAgilent34411AInstrument


class Transport(Protocol):
    """Text-oriented boundary every backend implements identically."""

    resource: str

    def open(self) -> None: ...

    def close(self) -> None: ...

    def is_open(self) -> bool: ...

    def write(self, command: str) -> None: ...

    def query(self, command: str) -> str: ...

    @property
    def timeout_s(self) -> float: ...

    @timeout_s.setter
    def timeout_s(self, value: float) -> None: ...


class PyvisaTransport:
    """VISA transport over `pyvisa` — GPIB, USB, or LAN, chosen by ``resource``'s prefix.

    Import is deferred to :meth:`open` so this module (and the whole
    package) stays importable without ``pyvisa`` installed when only the
    simulator is used — no device I/O happens at import time either way.
    """

    def __init__(self, resource: str, timeout_s: float = 5.0) -> None:
        if not resource or not str(resource).strip():
            raise Agilent34411AConnectionError("a VISA resource string is required")
        self.resource = str(resource).strip()
        self._timeout_s = float(timeout_s)
        self._instrument = None

    def open(self) -> None:
        try:
            import pyvisa
        except ImportError as exc:  # pragma: no cover - exercised only without the extra installed
            raise Agilent34411AConnectionError(
                "pyvisa is not installed; install rf_agilent34411a[visa] for real hardware"
            ) from exc
        try:
            manager = pyvisa.ResourceManager()
            self._instrument = manager.open_resource(self.resource)
            self._instrument.timeout = self._timeout_s * 1000.0
        except Exception as exc:  # pyvisa raises its own exception types
            raise Agilent34411AConnectionError(
                f"could not open VISA resource {self.resource!r}: {exc}"
            ) from exc

    def close(self) -> None:
        if self._instrument is not None:
            self._instrument.close()
            self._instrument = None

    def is_open(self) -> bool:
        return self._instrument is not None

    def _require_open(self):
        if self._instrument is None:
            raise Agilent34411AConnectionError("transport is not open")
        return self._instrument

    def write(self, command: str) -> None:
        instrument = self._require_open()
        try:
            instrument.write(command)
        except Exception as exc:
            raise Agilent34411ATimeoutError(f"write failed for {command!r}: {exc}") from exc

    def query(self, command: str) -> str:
        instrument = self._require_open()
        try:
            return str(instrument.query(command)).strip()
        except Exception as exc:
            raise Agilent34411ATimeoutError(f"query failed for {command!r}: {exc}") from exc

    @property
    def timeout_s(self) -> float:
        return self._timeout_s

    @timeout_s.setter
    def timeout_s(self, value: float) -> None:
        self._timeout_s = float(value)
        if self._instrument is not None:
            self._instrument.timeout = self._timeout_s * 1000.0


class SimulatedTransport:
    """Wraps a :class:`~agilent34411a.simulator.SimAgilent34411AInstrument`.

    Every command — write or query — goes through the simulator's single
    ``dispatch`` entry point, so the real SCPI strings built by
    ``driver.py`` are exercised exactly as they would be against hardware.
    """

    def __init__(self, simulator: SimAgilent34411AInstrument | None = None) -> None:
        if simulator is None:
            from .simulator import SimAgilent34411AInstrument

            simulator = SimAgilent34411AInstrument()
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
            raise Agilent34411AConnectionError("transport is not open")

    def write(self, command: str) -> None:
        self._require_open()
        self._simulator.dispatch(command)

    def query(self, command: str) -> str:
        self._require_open()
        return self._simulator.dispatch(command).decode("ascii", errors="replace").strip()

    @property
    def timeout_s(self) -> float:
        return self._timeout_s

    @timeout_s.setter
    def timeout_s(self, value: float) -> None:
        self._timeout_s = float(value)

    @property
    def simulator(self) -> SimAgilent34411AInstrument:
        """Direct access for tests that need to inspect/drive simulator state."""
        return self._simulator

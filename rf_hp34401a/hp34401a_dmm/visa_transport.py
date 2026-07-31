"""VISA GPIB transport using pyvisa (spec section 21.3, incorporating R9/R10).

``pyvisa`` is imported lazily inside ``_do_open`` so the package imports and the
CLI ``--help`` work without pyvisa installed and without hardware.
"""

from __future__ import annotations

import logging
import re

from .config import VisaGpibConfig
from .enums import (
    MAX_GPIB_ADDRESS,
    MIN_GPIB_ADDRESS,
    TALK_ONLY_GPIB_ADDRESS,
    TransportType,
)
from .errors import InstrumentConnectionError, InstrumentTimeoutError, TransportError
from .transports import BaseTransport

_log = logging.getLogger("hp34401a_dmm.transport")

_GPIB_ADDR_RE = re.compile(r"GPIB\d*::(\d+)", re.IGNORECASE)


def validate_gpib_resource(resource: str) -> None:
    """R10: reject talk-only (31) and out-of-range GPIB primary addresses."""
    m = _GPIB_ADDR_RE.search(resource)
    if not m:
        return  # non-GPIB resource string; nothing to validate here
    addr = int(m.group(1))
    if addr == TALK_ONLY_GPIB_ADDRESS:
        raise InstrumentConnectionError(
            f"GPIB address {addr} selects talk-only mode and cannot be queried. "
            f"Use a primary address in {MIN_GPIB_ADDRESS}-{MAX_GPIB_ADDRESS}."
        )
    if not (MIN_GPIB_ADDRESS <= addr <= MAX_GPIB_ADDRESS):
        raise InstrumentConnectionError(
            f"GPIB primary address {addr} is out of range "
            f"({MIN_GPIB_ADDRESS}-{MAX_GPIB_ADDRESS})."
        )


class VisaGpibTransport(BaseTransport):
    _transport_type = TransportType.VISA_GPIB

    def __init__(self, config: VisaGpibConfig, *, raw_traffic_log: bool = False) -> None:
        super().__init__(
            read_termination=config.read_termination,
            write_termination=config.write_termination,
            raw_traffic_log=raw_traffic_log,
        )
        validate_gpib_resource(config.resource)  # R10, fail before opening
        self.config = config
        self._rm = None
        self._inst = None

    @property
    def name(self) -> str:
        return f"visa:{self.config.resource}"

    def _do_open(self) -> None:
        try:
            import pyvisa  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise InstrumentConnectionError(
                "pyvisa is required for GPIB transport; install with "
                "'pip install pyvisa>=1.14'. GPIB additionally needs a vendor/native "
                "VISA backend (NI-VISA or Keysight IO Libraries); pyvisa-py alone "
                "does not drive GPIB (R9)."
            ) from exc

        try:
            if self.config.visa_library is not None:
                self._rm = pyvisa.ResourceManager(self.config.visa_library)
            else:
                self._rm = pyvisa.ResourceManager()
        except Exception as exc:
            raise InstrumentConnectionError(
                "Could not initialise a VISA backend. For GPIB you need NI-VISA or "
                "Keysight IO Libraries installed (R9). Underlying error: "
                f"{exc}"
            ) from exc

        try:
            self._inst = self._rm.open_resource(self.config.resource)
            self._inst.timeout = int(self.config.timeout_s * 1000)
            self._inst.read_termination = self.config.read_termination
            self._inst.write_termination = self.config.write_termination
        except Exception as exc:
            try:
                if self._inst is not None:
                    self._inst.close()
                if self._rm is not None:
                    self._rm.close()
            finally:
                self._inst = None
                self._rm = None
            raise InstrumentConnectionError(
                f"Could not open VISA resource {self.config.resource!r}: {exc}"
            ) from exc

    def _do_close(self) -> None:
        try:
            if self._inst is not None:
                self._inst.close()
        finally:
            self._inst = None
            if self._rm is not None:
                try:
                    self._rm.close()
                finally:
                    self._rm = None

    def _send(self, data: str) -> None:
        if self._inst is None:
            raise TransportError("VISA resource is not open")
        try:
            # data already includes the write terminator; strip it because pyvisa
            # appends its own configured write_termination.
            self._inst.write(data.rstrip("\r\n"))
        except Exception as exc:
            raise self._map_visa_error(exc, "write")

    def _recv(self) -> str:
        if self._inst is None:
            raise TransportError("VISA resource is not open")
        try:
            return self._inst.read()
        except Exception as exc:
            raise self._map_visa_error(exc, "read")

    def _clear(self) -> None:
        if self._inst is not None:
            try:
                self._inst.clear()
            except Exception as exc:  # pragma: no cover - hardware dependent
                raise TransportError(f"VISA clear failed on {self.name}: {exc}") from exc

    def _set_timeout(self, timeout_s: float) -> None:
        if self._inst is not None:
            self._inst.timeout = int(timeout_s * 1000)

    @staticmethod
    def _map_visa_error(exc: Exception, op: str) -> Exception:
        name = type(exc).__name__
        text = str(exc)
        if "timeout" in name.lower() or "VI_ERROR_TMO" in text:
            return InstrumentTimeoutError(f"VISA {op} timed out: {text}")
        return TransportError(f"VISA {op} failed: {text}")

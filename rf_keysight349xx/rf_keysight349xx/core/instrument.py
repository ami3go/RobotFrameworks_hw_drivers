"""Device semantics independent of Robot Framework presentation."""
from __future__ import annotations

from ..protocol.commands import CLEAR_STATUS, IDN, SYSTEM_CARD_TYPE, SYSTEM_ERROR, SYSTEM_VERSION
from ..protocol.parsers import parse_device_error, parse_identity, parse_module_identity
from ..protocol.scpi import ScpiProtocol


class Keysight349xxCore:
    def __init__(self, transport) -> None:
        self.scpi = ScpiProtocol(transport)

    def read_identity(self, *, timeout_s: float, operation_id: str = "identity"):
        return parse_identity(self.scpi.query(IDN, timeout_s=timeout_s, operation_id=operation_id))

    def get_module(self, slot: int, *, timeout_s: float, operation_id: str = "module"):
        raw = self.scpi.query(SYSTEM_CARD_TYPE.format(slot=slot), timeout_s=timeout_s, operation_id=operation_id)
        return parse_module_identity(slot, raw)

    def get_modules(self, *, timeout_s: float):
        return {slot: self.get_module(slot, timeout_s=timeout_s, operation_id=f"module.{slot}") for slot in (100, 200, 300)}

    def get_scpi_version(self, *, timeout_s: float) -> str:
        return self.scpi.query(SYSTEM_VERSION, timeout_s=timeout_s, operation_id="system.scpi_version")

    def get_device_error(self, *, timeout_s: float):
        return parse_device_error(self.scpi.query(SYSTEM_ERROR, timeout_s=timeout_s, operation_id="system.error"))

    def clear_device_errors(self, *, timeout_s: float) -> None:
        self.scpi.write(CLEAR_STATUS, timeout_s=timeout_s, operation_id="system.clear_errors")

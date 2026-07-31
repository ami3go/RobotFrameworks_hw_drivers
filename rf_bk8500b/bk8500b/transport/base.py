"""Transport abstraction used by protocol engines and test doubles."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol as TypingProtocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class PortInfo:
    device: str
    description: str | None = None
    hardware_id: str | None = None
    manufacturer: str | None = None
    serial_number: str | None = None


@runtime_checkable
class Transport(TypingProtocol):
    @property
    def is_open(self) -> bool: ...

    def open(self) -> None: ...
    def close(self) -> None: ...
    def write(self, data: bytes, *, timeout_s: float | None = None) -> int: ...
    def read(self, size: int, *, timeout_s: float | None = None) -> bytes: ...
    def read_until(
        self,
        terminator: bytes,
        *,
        maximum_bytes: int,
        timeout_s: float | None = None,
    ) -> bytes: ...
    def reset_input_buffer(self) -> None: ...
    def reset_output_buffer(self) -> None: ...

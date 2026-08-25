"""Phase 3 acquisition/memory safety semantics layered over scan configuration."""
from __future__ import annotations

from ..exceptions import DriverStateError
from ..transports.base import ReplayPolicy
from .acquisition import AcquisitionEngine as _ScanTriggerEngine, parse_numeric_list


class AcquisitionEngine(_ScanTriggerEngine):
    """Add validated acquisition and destructive reading-memory operations."""

    def initiate(self, *, timeout_s: float) -> None:
        if not self.get_scan_list(timeout_s=timeout_s):
            raise DriverStateError("cannot initiate a scan with an empty scan list", operation="scan.initiate")
        self.scpi.write("INIT", timeout_s=timeout_s, operation_id="scan.initiate")

    def read_scan(self, *, timeout_s: float) -> list[float]:
        if not self.get_scan_list(timeout_s=timeout_s):
            raise DriverStateError("cannot read a scan with an empty scan list", operation="scan.read")
        if self.get_trigger_source(timeout_s=timeout_s) == "BUS":
            raise DriverStateError(
                "READ? is invalid with BUS trigger source; use INITiate and an external bus trigger",
                operation="scan.read",
            )
        raw = self.scpi.query(
            "READ?",
            timeout_s=timeout_s,
            operation_id="scan.read",
            replay_policy=ReplayPolicy.NEVER,
        )
        return parse_numeric_list(raw)

    def remove(self, count: object, *, timeout_s: float) -> list[float]:
        value = self._positive_count(count, max_value=50000)
        available = self.reading_count(timeout_s=timeout_s)
        if value > available:
            raise DriverStateError(
                f"cannot remove {value} readings because only {available} are stored",
                operation="memory.remove",
            )
        raw = self.scpi.query(
            f"DATA:REM? {value}",
            timeout_s=timeout_s,
            operation_id="memory.remove",
            replay_policy=ReplayPolicy.NEVER,
        )
        return parse_numeric_list(raw)

    def clear_memory(self, *, timeout_s: float) -> int:
        """Drain memory using R? and return the number of discarded readings."""
        count = self.reading_count(timeout_s=timeout_s)
        if count:
            self.buffered(count, timeout_s=timeout_s)
        return count

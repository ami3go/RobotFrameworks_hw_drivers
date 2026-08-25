"""Phase 3 acquisition and reading-memory simulator behavior."""
from __future__ import annotations

import re

from .simulator import SimulatorTransport as _ScanTriggerSimulator


class SimulatorTransport(_ScanTriggerSimulator):
    """Add INIT/ABOR/READ/FETCH/R?/DATA memory semantics to the simulator."""

    def __init__(self, model: str = "34972A", modules: dict[int, str] | None = None, *, strict: bool = True) -> None:
        super().__init__(model=model, modules=modules, strict=strict)
        self._memory: list[float] = []
        self._scan_active = False

    def _clear_acquisition_data(self) -> None:
        self._memory.clear()

    def _channel_value(self, channel: int) -> float:
        function = self._configured.get(channel, "VOLT:DC")
        return self._measurement_value(f"MEAS:{function}?", channel)

    def _generate_sweeps(self) -> list[float]:
        count = 1 if self._trigger_count == "INF" else int(self._trigger_count)
        readings = [self._channel_value(channel) for _ in range(count) for channel in self._scan_list]
        self._memory.extend(readings)
        if len(self._memory) > 50000:
            self._memory = self._memory[-50000:]
        return readings

    @staticmethod
    def _format_readings(readings: list[float]) -> str:
        return ",".join(f"{value:+.9E}" for value in readings)

    def _execute_scan_trigger(self, normalized: str):
        result = super()._execute_scan_trigger(normalized)
        upper = normalized.upper()
        if result is not NotImplemented and (upper.startswith("CONF:") or upper.startswith("TRIG:SOUR ") or upper.startswith("TRIG:COUN ") or upper.startswith("TRIG:TIM ")):
            self._clear_acquisition_data()
        return result

    def _execute_acquisition(self, normalized: str):
        upper = normalized.upper()
        if upper == "INIT":
            if not self._scan_list:
                self._errors.append((-221, "Settings conflict")); return None
            self._clear_acquisition_data(); self._scan_active = True
            if self._trigger_source in {"IMM", "TIM"}:
                self._generate_sweeps()
                if self._trigger_count != "INF": self._scan_active = False
            return None
        if upper == "ABOR":
            self._scan_active = False; return None
        if upper == "READ?":
            if not self._scan_list or self._trigger_source == "BUS":
                self._errors.append((-221, "Settings conflict")); return b"\n"
            self._clear_acquisition_data(); self._scan_active = True
            readings = self._generate_sweeps(); self._scan_active = self._trigger_count == "INF"
            response = (self._format_readings(readings) + "\n").encode("ascii")
            if self.model == "34970A": self._memory.clear()
            return response
        if upper in {"FETC?", "FETCH?"}:
            return (self._format_readings(self._memory) + "\n").encode("ascii")
        match = re.fullmatch(r"R\?(?:\s+(\d+))?", upper)
        if match:
            requested = len(self._memory) if match.group(1) is None else int(match.group(1))
            count = min(requested, len(self._memory), 50000)
            readings = self._memory[:count]; del self._memory[:count]
            return self._block(self._format_readings(readings))
        match = re.fullmatch(r"DATA:(?:REM|REMOVE)\?\s+(\d+)", upper)
        if match:
            count = int(match.group(1))
            if count > len(self._memory):
                self._errors.append((-222, "Data out of range")); return b"\n"
            readings = self._memory[:count]; del self._memory[:count]
            return self._block(self._format_readings(readings))
        if upper in {"DATA:POIN?", "DATA:POINTS?"}:
            return f"+{len(self._memory)}\n".encode("ascii")
        return NotImplemented

    def _execute(self, command: str) -> bytes | None:
        normalized = command.strip()
        result = self._execute_acquisition(normalized)
        if result is not NotImplemented:
            return result
        return super()._execute(command)

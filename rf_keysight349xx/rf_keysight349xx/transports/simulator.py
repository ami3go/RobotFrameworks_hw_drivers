"""Phase 3 stateful simulator extensions for scan and trigger configuration."""
from __future__ import annotations

import re

from .simulator_base import SimulatorTransport as _Phase2SimulatorTransport


class SimulatorTransport(_Phase2SimulatorTransport):
    """Extend the Phase 2 protocol-boundary simulator with scan/trigger state."""

    def __init__(self, model: str = "34972A", modules: dict[int, str] | None = None, *, strict: bool = True) -> None:
        super().__init__(model=model, modules=modules, strict=strict)
        self._configured: dict[int, str] = {}
        self._scan_list: list[int] = []
        self._trigger_source = "IMM"
        self._trigger_count: int | str = 1
        self._trigger_timer_s = 0.0

    @staticmethod
    def _block(payload: str) -> bytes:
        count = str(len(payload))
        return f"#{len(count)}{count}{payload}\n".encode("ascii")

    def _execute_scan_trigger(self, normalized: str):
        upper = normalized.upper()
        conf = re.match(
            r"CONF:(VOLT:DC|VOLT:AC|CURR:DC|CURR:AC|RES|FRES|FREQ|PER)(?:\s+.*?)?,?\(@(\d{3})\)\s*$",
            upper,
        )
        if conf:
            channel = int(conf.group(2))
            self._configured[channel] = conf.group(1)
            self._scan_list = [channel]
            self._trigger_source = "IMM"
            self._trigger_count = 1
            self._trigger_timer_s = 1.0
            return None
        match = re.fullmatch(r"ROUT:SCAN\s+\(@([^)]*)\)", upper)
        if match:
            payload = match.group(1).strip()
            self._scan_list = [] if not payload else sorted({int(x.strip()) for x in payload.split(",") if x.strip()})
            return None
        if upper == "ROUT:SCAN?":
            payload = "(@" + ",".join(str(x) for x in self._scan_list) + ")"
            return self._block(payload)
        if upper.startswith("TRIG:SOUR "):
            self._trigger_source = upper.split(None, 1)[1]
            return None
        if upper == "TRIG:SOUR?":
            return (self._trigger_source + "\n").encode("ascii")
        if upper.startswith("TRIG:COUN "):
            token = upper.split(None, 1)[1]
            self._trigger_count = "INF" if token.startswith("INF") else int(token)
            return None
        if upper == "TRIG:COUN?":
            if self._trigger_count == "INF":
                return b"+9.90000200E+37\n"
            return f"{int(self._trigger_count):+.8E}\n".encode("ascii")
        if upper.startswith("TRIG:TIM "):
            self._trigger_timer_s = float(upper.split(None, 1)[1])
            return None
        if upper == "TRIG:TIM?":
            return f"{self._trigger_timer_s:+.8E}\n".encode("ascii")
        return NotImplemented

    def _execute(self, command: str) -> bytes | None:
        normalized = command.strip()
        result = self._execute_scan_trigger(normalized)
        if result is not NotImplemented:
            return result
        return super()._execute(command)

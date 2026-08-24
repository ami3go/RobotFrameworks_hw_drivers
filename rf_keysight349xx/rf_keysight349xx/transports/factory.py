"""Transport factory with deterministic resource selection."""
from __future__ import annotations

from typing import Any

from ..exceptions import DriverNotSupportedError, DriverValidationError
from .simulator import SimulatorTransport
from .visa import VisaTransport


class TransportFactory:
    def create(self, resource: str, *, timeout_s: float, options: dict[str, Any] | None = None):
        options = dict(options or {})
        allowed = {"visa_backend", "simulator_modules", "strict_simulator"}
        unknown = sorted(set(options) - allowed)
        if unknown:
            raise DriverValidationError(f"unknown connection option(s): {', '.join(unknown)}")
        upper = resource.upper()
        if upper.startswith("SIM::"):
            model = upper.split("::", 1)[1].strip() or "34972A"
            modules = options.get("simulator_modules")
            if isinstance(modules, str):
                # form: 100=34901A,200=0,300=34907A
                parsed = {}
                for item in modules.split(","):
                    slot_text, model_text = item.split("=", 1)
                    parsed[int(slot_text.strip())] = model_text.strip().upper()
                modules = parsed
            return SimulatorTransport(
                model=model,
                modules=modules,
                strict=bool(options.get("strict_simulator", True)),
            )
        if "::" in resource:
            return VisaTransport(resource, backend=options.get("visa_backend"), default_timeout_s=timeout_s)
        raise DriverNotSupportedError(
            "resource is not a supported simulator or VISA identifier; use SIM::34970A, SIM::34972A, or a VISA resource",
            code="RFDS-DEV-004",
        )

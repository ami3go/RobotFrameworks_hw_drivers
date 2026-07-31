#!/usr/bin/env python3
"""Run a bounded canonical-API simulator smoke workflow."""
from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary
from rf_votsch_climate_chamber.version import RELEASE_VERSION


def main() -> int:
    started = time.monotonic()
    library = VotschClimateChamberLibrary(default_resource="SIM::release-smoke")
    results: dict[str, object] = {}
    try:
        results["connect"] = library.connect()
        results["identity"] = library.get_identity(refresh=True)
        results["temperature_initial_c"] = library.measure_temperature()
        library.set_temperature(30)
        library.start_chamber()
        results["temperature_final_c"] = library.wait_for_temperature_stability(
            30, stable_samples=1, poll_interval_s=0.001, settle_timeout_s=2
        )
        results["safe_shutdown"] = library.safe_shutdown()
        results["status"] = "PASS"
    finally:
        try:
            library.disconnect_all()
        except Exception as exc:  # pragma: no cover - evidence path only.
            results["cleanup_error"] = str(exc)

    results["environment"] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "duration_s": time.monotonic() - started,
    }
    output = ROOT / "review" / "evidence" / f"v{RELEASE_VERSION}" / "python_simulator_smoke.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    print(output)
    print(results["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

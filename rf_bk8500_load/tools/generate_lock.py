#!/usr/bin/env python3
"""Generate ``ai/ai_contract.lock`` from the contract and the live library.

The lock file pins three things:

* the SHA-256 of ``ai_contract.yaml``, so an edit without a re-generation is
  detectable;
* the SHA-256 of the library's keyword surface (names plus argument names), so
  a signature change without a contract update is detectable;
* the driver version the contract was generated for.

Run after any change to the contract or to the keyword surface::

    python3 tools/generate_lock.py
"""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bk8500_load.library import BK8500Library  # noqa: E402
from bk8500_load.version import VERSION  # noqa: E402

AI_DIR = ROOT / "ai"
CONTRACT = AI_DIR / "ai_contract.yaml"
LOCK = AI_DIR / "ai_contract.lock"


def keyword_surface() -> list[str]:
    """Return ``keyword name(arg, arg=default)`` for every exposed keyword."""
    surface = []
    for attribute in vars(BK8500Library).values():
        name = getattr(attribute, "robot_name", None)
        if not name:
            continue
        signature = inspect.signature(attribute)
        arguments = [
            parameter.name for parameter in signature.parameters.values() if parameter.name != "self"
        ]
        surface.append(f"{name}({', '.join(arguments)})")
    return sorted(surface)


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    contract_bytes = CONTRACT.read_bytes()
    surface = keyword_surface()
    if not surface:
        # Never write a lock for an empty keyword surface. The library fallback
        # decorator preserves metadata in source-only environments, so reaching
        # this branch indicates a real decorator or discovery regression.
        raise SystemExit(
            "No keywords found. Install robotframework before regenerating the lock."
        )
    lock = {
        "lock_format": 1,
        "rfds": "RFDS-017",
        "specification_version": "3.0",
        "driver_version": VERSION,
        "contract_file": "ai_contract.yaml",
        "contract_sha256": sha256_of(contract_bytes),
        "contract_bytes": len(contract_bytes),
        "keyword_count": len(surface),
        "keyword_surface_sha256": sha256_of("\n".join(surface).encode("utf-8")),
        "keywords": surface,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    LOCK.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {LOCK.relative_to(ROOT)}: {len(surface)} keywords, contract {lock['contract_sha256'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

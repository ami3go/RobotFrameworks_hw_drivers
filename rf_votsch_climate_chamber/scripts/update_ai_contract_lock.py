#!/usr/bin/env python3
"""Regenerate ai_contract.lock after an intentional contract/API update."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_ai_contract import (
    CONTRACT_PATH,
    LOCK_PATH,
    keyword_manifest,
    manifest_hash,
    release_version,
)


def main() -> int:
    manifest = keyword_manifest()
    lock: dict[str, Any] = {
        "schema": "RFDS-017-LOCK-1.0",
        "driver_release": release_version(),
        "contract_file": "ai/ai_contract.yaml",
        "contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "keyword_source": "votsch_climate_chamber/robot_library.py",
        "keyword_count": len(manifest),
        "keyword_manifest_sha256": manifest_hash(manifest),
        "generated_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "generator": "scripts/update_ai_contract_lock.py",
    }
    LOCK_PATH.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {LOCK_PATH.relative_to(Path.cwd()) if LOCK_PATH.is_relative_to(Path.cwd()) else LOCK_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

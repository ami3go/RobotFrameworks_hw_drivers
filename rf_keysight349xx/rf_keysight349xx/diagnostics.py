"""Non-invasive diagnostic helpers."""
from __future__ import annotations

import platform
import sys


def environment_summary() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "implementation": platform.python_implementation(),
    }

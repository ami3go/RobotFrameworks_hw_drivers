"""Robot Framework driver for B&K Precision 8500 series DC electronic loads.

Public API::

    from bk8500_load import BK8500Library      # Robot Framework keywords
    from bk8500_load import BK8500Driver       # plain Python driver
"""

import os
import sysconfig
from pathlib import Path

from .driver import BK8500Driver
from .enums import (
    InputValues,
    ListRepeat,
    ListStep,
    LoadFunction,
    LoadMode,
    ModelLimits,
    ProductInfo,
    TransientOperation,
    TransientSettings,
    TriggerSource,
)
from .exceptions import (
    BK8500CommandError,
    BK8500ConfigurationError,
    BK8500ConnectionError,
    BK8500Error,
    BK8500ProtectionError,
    BK8500ProtocolError,
    BK8500SafetyError,
    BK8500StateError,
    BK8500TimeoutError,
    BK8500ValidationError,
    BK8500VerificationError,
)
from .library import BK8500Library
from .transport import SerialTransport, SimulatedTransport, Transport
from .version import LIFECYCLE_VERSION, PACKAGE_RELEASE, VERSION

#: Directory holding the RFDS-017 contract and its lock file. In the source
#: package it is the top-level ``ai/`` directory. When installed from the wheel,
#: setuptools places the same files under ``share/rf_bk8500_load/ai``.
def _resolve_ai_contract_dir() -> Path:
    override = os.getenv("RF_BK8500_AI_DIR")
    candidates = []
    if override:
        candidates.append(Path(override).expanduser())
    candidates.extend(
        [
            Path(__file__).resolve().parent.parent / "ai",
            # ``pip install --target`` places data files beside the package,
            # not under the interpreter's sysconfig data prefix.
            Path(__file__).resolve().parent.parent / "share" / "rf_bk8500_load" / "ai",
            Path(sysconfig.get_path("data")) / "share" / "rf_bk8500_load" / "ai",
        ]
    )
    for candidate in candidates:
        if (candidate / "ai_contract.yaml").is_file():
            return candidate
    # Return the source-layout location to make missing-file errors explicit.
    return candidates[0] if candidates else Path(__file__).resolve().parent.parent / "ai"


AI_CONTRACT_DIR = _resolve_ai_contract_dir()


def contract_path() -> Path:
    """Absolute path to the RFDS-017 ``ai_contract.yaml`` file."""
    return AI_CONTRACT_DIR / "ai_contract.yaml"


def lock_path() -> Path:
    """Absolute path to the RFDS-017 ``ai_contract.lock`` file."""
    return AI_CONTRACT_DIR / "ai_contract.lock"


__version__ = VERSION
__all__ = [
    "BK8500Library",
    "BK8500Driver",
    "Transport",
    "SerialTransport",
    "SimulatedTransport",
    "LoadMode",
    "LoadFunction",
    "TriggerSource",
    "TransientOperation",
    "ListRepeat",
    "InputValues",
    "ProductInfo",
    "TransientSettings",
    "ListStep",
    "ModelLimits",
    "BK8500Error",
    "BK8500ConfigurationError",
    "BK8500ConnectionError",
    "BK8500TimeoutError",
    "BK8500ProtocolError",
    "BK8500CommandError",
    "BK8500ValidationError",
    "BK8500StateError",
    "BK8500SafetyError",
    "BK8500ProtectionError",
    "BK8500VerificationError",
    "VERSION",
    "LIFECYCLE_VERSION",
    "PACKAGE_RELEASE",
    "AI_CONTRACT_DIR",
    "contract_path",
    "lock_path",
]

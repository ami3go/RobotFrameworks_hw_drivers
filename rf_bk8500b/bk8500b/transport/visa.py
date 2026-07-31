"""Optional VISA serial transport placeholder.

The stable public API does not depend on PyVISA. This adapter intentionally raises
an actionable error until the optional extra is installed and selected explicitly.
"""
from __future__ import annotations

from ..exceptions import ConfigurationError


class VisaSerialTransport:
    def __init__(self, *args, **kwargs) -> None:
        raise ConfigurationError(
            "VisaSerialTransport is optional and not enabled in this release candidate"
        )

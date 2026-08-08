"""Robot Framework suite lifecycle cleanup.

The listener owns best-effort emergency cleanup when a suite ends. Explicit
``Disconnect`` and ``Safe Shutdown`` keywords remain authoritative because
they can report cleanup failures to the caller.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from .sessions import SessionRegistry

_LOG = logging.getLogger(__name__)


class SuiteLifecycleListener:
    """Best-effort suite-end cleanup listener for one session registry."""

    ROBOT_LISTENER_API_VERSION = 3

    def __init__(
        self,
        registry: SessionRegistry,
        safe_shutdown_policy: Callable[[], bool] | None = None,
        evidence_finalizer: Callable[[], None] | None = None,
    ) -> None:
        self._registry = registry
        self._safe_shutdown_policy = safe_shutdown_policy or (lambda: True)
        self._evidence_finalizer = evidence_finalizer

    def end_suite(self, data: Any, result: Any) -> None:
        """Close all sessions without hiding the original suite result."""
        del data, result
        try:
            self._registry.disconnect_all(
                safe_shutdown=bool(self._safe_shutdown_policy()), timeout_s=20.0
            )
        except Exception:  # pragma: no cover - emergency cleanup must not mask suite result.
            _LOG.exception("Suite-end climate-chamber cleanup failed")
        if self._evidence_finalizer is not None:
            try:
                self._evidence_finalizer()
            except (
                Exception
            ):  # pragma: no cover - evidence finalization must not mask suite result.
                _LOG.exception("Suite-end evidence finalization failed")

"""Robot Framework integration with an import-safe development fallback.

Normal installations use Robot Framework's real decorators and logger.  The
fallback exists only so metadata, plugin discovery, package validation, and
pure-Python tests remain importable before the optional test runtime is
installed.  It does not attempt to execute a Robot suite.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

try:  # pragma: no cover - exercised in a real Robot Framework environment.
    from robot.api import logger as logger
    from robot.api.deco import keyword as keyword
    from robot.api.deco import library as library
    ROBOT_AVAILABLE = True
except ImportError:  # development fallback
    ROBOT_AVAILABLE = False
    _log = logging.getLogger("rf_votsch_climate_chamber")

    class _Logger:
        def info(self, message: str, **_: Any) -> None:
            _log.info(message)

        def debug(self, message: str, **_: Any) -> None:
            _log.debug(message)

        def warn(self, message: str, **_: Any) -> None:
            _log.warning(message)

        def error(self, message: str, **_: Any) -> None:
            _log.error(message)

    logger = _Logger()

    def keyword(name: str | None = None, tags: list[str] | tuple[str, ...] | None = None):  # type: ignore[misc]
        def decorator(function: F) -> F:
            setattr(function, "robot_name", name or function.__name__.replace("_", " ").title())
            setattr(function, "robot_tags", tuple(tags or ()))
            return function

        return decorator

    def library(*, scope: str = "TEST", auto_keywords: bool = True, version: str | None = None):  # type: ignore[misc]
        def decorator(cls):
            cls.ROBOT_LIBRARY_SCOPE = scope
            cls.ROBOT_AUTO_KEYWORDS = auto_keywords
            cls.ROBOT_LIBRARY_VERSION = version
            return cls

        return decorator

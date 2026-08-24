"""Robot Framework imports with an import-safe development fallback.

Robot Framework is a declared runtime dependency.  The tiny fallback exists only
so static inspection and unit tests can run in stripped build environments; it
never performs I/O and does not replace Robot Framework in installed releases.
"""
from __future__ import annotations

try:  # pragma: no cover - exercised in installed environments
    from robot.api.deco import keyword, library
except ImportError:  # pragma: no cover - build-environment fallback
    def keyword(name=None, tags=None):
        def decorate(func):
            func.robot_name = name or func.__name__.replace("_", " ").title()
            func.robot_tags = tuple(tags or ())
            return func
        return decorate

    def library(*, scope="SUITE", version=None, auto_keywords=False):
        def decorate(cls):
            cls.ROBOT_LIBRARY_SCOPE = scope
            cls.ROBOT_LIBRARY_VERSION = version
            cls.ROBOT_AUTO_KEYWORDS = auto_keywords
            return cls
        return decorate

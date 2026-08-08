"""Robot Framework library for B&K Precision 8500B Series electronic loads.

This package re-exports :class:`BK8500BLibrary` so that Robot Framework can
resolve the canonical ``Library    rf_bk8500b.BK8500BLibrary`` import, matching
the ``rf_<device>.<Device>Library`` convention used by the other drivers in
this repository. The legacy ``Library    BK8500BLibrary`` import keeps
working unchanged.
"""

from BK8500BLibrary.library import BK8500BLibrary, BK8500BRobotError

__version__ = "26.05"

__all__ = ["BK8500BLibrary", "BK8500BRobotError"]

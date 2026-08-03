"""Robot Framework library for B&K Precision 8500 series DC electronic loads.

This package re-exports :class:`BK8500Library` so that Robot Framework can
resolve the canonical ``Library    rf_bk8500_load.BK8500Library`` import,
matching the ``rf_<device>.<Device>Library`` convention used by the other
drivers in this repository. The legacy top-level ``Library    BK8500Library``
import keeps working unchanged.
"""

from bk8500_load.library import BK8500Library
from bk8500_load.version import VERSION

__version__ = VERSION

__all__ = ["BK8500Library"]

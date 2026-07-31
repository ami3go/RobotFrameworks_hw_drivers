"""Robot Framework compatibility entry point.

This module intentionally defines ``BK8500Library`` locally instead of merely
re-exporting the implementation class.  Robot Framework can therefore resolve
``Library    BK8500Library`` consistently across supported Robot Framework
versions and discover the inherited keyword methods.
"""

from bk8500_load.library import BK8500Library as _BK8500Library


class BK8500Library(_BK8500Library):
    """Public Robot Framework library class for the short import name."""


__all__ = ["BK8500Library"]

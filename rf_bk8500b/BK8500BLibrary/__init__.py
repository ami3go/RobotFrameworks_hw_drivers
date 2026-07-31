"""Robot Framework library for B&K Precision 8500B Series electronic loads."""
from .library import BK8500BLibrary, BK8500BRobotError

__version__ = "26.04"

__all__ = ["BK8500BLibrary", "BK8500BRobotError"]

"""RFDS Vötsch climate-chamber Robot Framework driver."""

from .library import VotschClimateChamberLibrary
from .version import API_VERSION, PEP440_VERSION, RELEASE_LABEL, RELEASE_VERSION

__all__ = [
    "VotschClimateChamberLibrary",
    "API_VERSION",
    "PEP440_VERSION",
    "RELEASE_LABEL",
    "RELEASE_VERSION",
]
__version__ = PEP440_VERSION

"""Robot Framework library package for SLCAN (serial-line CAN) interface adapters.

Thin Robot Framework wrapper (``library.py``) over the framework-agnostic
``slcan`` core driver package: SLCAN command construction/parsing and the
background CAN-frame reader thread live entirely in ``slcan``, never
duplicated here. Every public keyword is recorded as RFDS-008 structured
evidence via ``slcan.evidence`` — see ``docs/logging_and_evidence.md``.
"""

from .library import SlcanLibrary

__version__ = "26.2"

__all__ = ["SlcanLibrary", "__version__"]

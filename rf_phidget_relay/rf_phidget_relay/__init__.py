"""Robot Framework driver for an eight-channel, two-board Phidget relay bank.

Wraps two PhidgetInterfaceKit 0/0/4 boards' ``DigitalOutput`` channels as one
logical 8-channel switch bank (``PhidgetRelayLibrary``, in ``library.py``).
Typically used to route a DMM or other shared instrument to one of several
points under test. ``evidence.py`` provides the RFDS-008 structured logging/
diagnostics layer described in ``docs/logging_and_evidence.md``.
"""

from .library import PhidgetRelayLibrary

__all__ = ["PhidgetRelayLibrary"]
__version__ = "26.3"

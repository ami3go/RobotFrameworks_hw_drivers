"""Phase 3 acquisition and reading-memory Robot Framework keywords."""
from __future__ import annotations

from datetime import datetime, timezone

from ._robot_compat import keyword, library
from .core import AcquisitionEngine
from .library_scan import Keysight349xxLibrary as _ScanTriggerLibrary
from .version import __version__


@library(scope="SUITE", version=__version__, auto_keywords=False)
class Keysight349xxLibrary(_ScanTriggerLibrary):
    """Extend scan/trigger configuration with acquisition and reading-memory operations."""

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = __version__
    ROBOT_AUTO_KEYWORDS = False

    @keyword("Initiate Scan", tags=["rfds:scan", "rfds:acquisition", "rfds:medium_risk"])
    def initiate_scan(self, alias=None) -> None:
        session = self._session(alias)
        AcquisitionEngine(session.transport).initiate(timeout_s=session.timeout_s)
        session.scan_start_time_utc = datetime.now(timezone.utc).isoformat()

    @keyword("Abort Scan", tags=["rfds:scan", "rfds:acquisition", "rfds:medium_risk"])
    def abort_scan(self, alias=None) -> None:
        self._execute_operation("abort_scan", lambda session, timeout: AcquisitionEngine(session.transport).abort(timeout_s=timeout), alias=alias)

    @keyword("Read Scan", tags=["rfds:scan", "rfds:acquisition", "rfds:medium_risk"])
    def read_scan(self, alias=None) -> list[float]:
        session = self._session(alias)
        session.scan_start_time_utc = datetime.now(timezone.utc).isoformat()
        return AcquisitionEngine(session.transport).read_scan(timeout_s=session.timeout_s)

    @keyword("Fetch Readings", tags=["rfds:scan", "rfds:acquisition", "rfds:query", "rfds:low_risk"])
    def fetch_readings(self, alias=None) -> list[float]:
        return self._execute_operation("fetch_readings", lambda session, timeout: AcquisitionEngine(session.transport).fetch(timeout_s=timeout), alias=alias)

    @keyword("Read Buffered Readings", tags=["rfds:memory", "rfds:acquisition", "rfds:medium_risk"])
    def read_buffered_readings(self, max_count=None, alias=None) -> list[float]:
        return self._execute_operation("read_buffered_readings", lambda session, timeout: AcquisitionEngine(session.transport).buffered(max_count, timeout_s=timeout), alias=alias)

    @keyword("Remove Readings", tags=["rfds:memory", "rfds:acquisition", "rfds:medium_risk"])
    def remove_readings(self, count, alias=None) -> list[float]:
        return self._execute_operation("remove_readings", lambda session, timeout: AcquisitionEngine(session.transport).remove(count, timeout_s=timeout), alias=alias)

    @keyword("Get Reading Count", tags=["rfds:memory", "rfds:query", "rfds:low_risk"])
    def get_reading_count(self, alias=None) -> int:
        return self._execute_operation("get_reading_count", lambda session, timeout: AcquisitionEngine(session.transport).reading_count(timeout_s=timeout), alias=alias)

    @keyword("Clear Reading Memory", tags=["rfds:memory", "rfds:acquisition", "rfds:medium_risk"])
    def clear_reading_memory(self, alias=None) -> int:
        """Drain and discard stored readings; return the number removed."""
        return self._execute_operation("clear_reading_memory", lambda session, timeout: AcquisitionEngine(session.transport).clear_memory(timeout_s=timeout), alias=alias)

    @keyword("Get Scan Start Time", tags=["rfds:scan", "rfds:query", "rfds:low_risk"])
    def get_scan_start_time(self, alias=None) -> str | None:
        """Return host UTC timestamp captured when this driver initiated/read the current scan."""
        return self._session(alias).scan_start_time_utc

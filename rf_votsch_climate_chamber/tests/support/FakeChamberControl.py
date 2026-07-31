"""Robot helper that owns the fake TCP chamber used in acceptance suites."""

from tests.support.fake_chamber import FakeChamberServer


class FakeChamberControl:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self) -> None:
        self._server = None

    def start_fake_chamber(self) -> int:
        self._server = FakeChamberServer().start()
        return self._server.port

    def stop_fake_chamber(self) -> None:
        if self._server is not None:
            self._server.stop()
            self._server = None

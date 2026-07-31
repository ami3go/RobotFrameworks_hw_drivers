"""Robot acceptance-test library using the deterministic fake SCPI transport."""
from dataclasses import replace

from bk8500b import BK8500B
from BK8500BLibrary import BK8500BLibrary
from tests.fakes import FakeSCPITransport


class FakeBK8500BLibrary(BK8500BLibrary):
    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self) -> None:
        super().__init__()

        def factory(config):
            return BK8500B(
                replace(config, minimum_command_interval_s=0),
                transport=FakeSCPITransport(),
            )

        self._device_factory = factory

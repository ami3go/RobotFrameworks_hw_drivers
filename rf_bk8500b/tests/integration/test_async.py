import asyncio

from bk8500b import AsyncBK8500B, DriverConfig
from tests.fakes import FakeSCPITransport


def test_async_facade_uses_sync_core() -> None:
    async def run() -> None:
        transport = FakeSCPITransport()
        device = AsyncBK8500B(
            DriverConfig(port="FAKE", minimum_command_interval_s=0),
            transport=transport,
        )
        await device.connect()
        measurement = await device.measure_voltage()
        assert measurement.value == 12.0
        await device.close()

    asyncio.run(run())

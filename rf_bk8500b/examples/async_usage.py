import asyncio

from bk8500b import AsyncBK8500B, DriverConfig

async def main() -> None:
    async with AsyncBK8500B(DriverConfig(port="COM5")) as load:
        voltage, current = await asyncio.gather(
            load.measure_voltage(),
            load.measure_current(),
        )
        # Calls are accepted concurrently but serialized through one worker.
        print(voltage.value, current.value)

asyncio.run(main())

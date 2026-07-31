import asyncio
import inspect
import time

import pytest

import bk8500b.async_device as async_module
from bk8500b import (
    DriverConfig,
    DynamicMode,
    LEDConfig,
    ListConfig,
    OCPTestConfig,
    OperatingMode,
    SafeEnableConfig,
    SafetyToken,
    TimingTestConfig,
    TransientConfig,
    TriggerSource,
)
from bk8500b.enums import SessionState, TriggerEdge
from bk8500b.measurements import ListStep
from bk8500b.protocol.legacy_codec import build_frame


class UniversalSync:
    def __init__(self, *args, **kwargs):
        self.connected = True
        self.session_state = SessionState.CONNECTED_READY
        self.calls = []

    def __getattr__(self, name):
        def method(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return name
        return method


def argument_for(method_name: str, parameter: str):
    if parameter == "enabled": return False
    if parameter == "value": return 1.0
    if parameter == "slot": return 0
    if parameter == "mode": return OperatingMode.CURRENT
    if parameter == "amperes": return 1.0
    if parameter == "volts": return 1.0
    if parameter == "watts": return 1.0
    if parameter == "ohms": return 10.0
    if parameter == "token":
        purpose = "clear_protection" if method_name == "clear_protection" else "enable_short"
        return SafetyToken.issue(purpose)
    if parameter == "command": return "*STB?"
    if parameter == "frame": return build_frame(0, 1)
    if parameter == "config":
        return {
            "configure_and_enable": SafeEnableConfig(OperatingMode.CURRENT, 0.1),
            "configure_transient": TransientConfig(1, 0.1, 0.1, 0.1, 1, DynamicMode.CONTINUOUS),
            "configure_led": LEDConfig(1, 0.1, 0.2),
            "configure_ocp_test": OCPTestConfig(0.1, 0.2, 2, 0.01, 1),
            "configure_timing_test": TimingTestConfig(True, OperatingMode.CURRENT, 0.1, TriggerSource.VOLTAGE, TriggerEdge.RISE, 1, TriggerSource.VOLTAGE, TriggerEdge.FALL, 2),
            "configure_list": ListConfig((ListStep(0.1, 0.1),)),
        }[method_name]
    raise AssertionError((method_name, parameter))


def test_every_async_public_wrapper_dispatches(monkeypatch) -> None:
    monkeypatch.setattr(async_module, "BK8500B", UniversalSync)

    async def run() -> None:
        device = async_module.AsyncBK8500B(DriverConfig(port="FAKE"))
        assert device.connected
        assert device.session_state is SessionState.CONNECTED_READY
        await device.connect()
        skip = {"close", "connect"}
        for name, method in inspect.getmembers(device, predicate=inspect.iscoroutinefunction):
            if name.startswith("_") or name in skip:
                continue
            signature = inspect.signature(method)
            args = []
            kwargs = {}
            for parameter in signature.parameters.values():
                if parameter.default is not inspect.Parameter.empty:
                    continue
                value = argument_for(name, parameter.name)
                if parameter.kind is inspect.Parameter.KEYWORD_ONLY:
                    kwargs[parameter.name] = value
                else:
                    args.append(value)
            await method(*args, **kwargs)
        await device.close()
        with pytest.raises(RuntimeError):
            await device.measure_voltage()

    asyncio.run(run())


def test_async_context_manager_and_cancellation(monkeypatch) -> None:
    class SlowSync(UniversalSync):
        def connect(self): return None
        def close(self): return None
        def set_input_enabled(self, *args, **kwargs):
            time.sleep(0.03)
            return None

    monkeypatch.setattr(async_module, "BK8500B", SlowSync)

    async def run() -> None:
        async with async_module.AsyncBK8500B(DriverConfig(port="FAKE")) as device:
            task = asyncio.create_task(device.set_input_enabled(True))
            await asyncio.sleep(0.005)
            task.cancel()
            with pytest.raises(Exception):
                await task

    asyncio.run(run())

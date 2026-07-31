import pytest

from bk8500b import (
    BK8500B,
    DriverConfig,
    OperatingMode,
    SafeEnableConfig,
    SafetyPolicy,
    SessionState,
    UnsafeOperationError,
)
from tests.fakes import FakeSCPITransport


def make_device(*, safety: SafetyPolicy | None = None):
    transport = FakeSCPITransport()
    config = DriverConfig(
        port="FAKE",
        minimum_command_interval_s=0,
        safety=safety or SafetyPolicy(),
    )
    return BK8500B(config, transport=transport), transport


def test_connect_synchronizes_without_enabling_input() -> None:
    device, transport = make_device()
    device.connect()
    assert device.session_state is SessionState.CONNECTED_READY
    assert device.identify().model == "BK8500B"
    written = b"".join(transport.writes)
    assert b"INPut ON" not in written
    device.close()


def test_measure_all() -> None:
    device, _ = make_device()
    with device:
        snapshot = device.measure_all()
        assert snapshot.voltage.value == pytest.approx(12.0)
        assert snapshot.current.value == pytest.approx(1.0)
        assert snapshot.power.value == pytest.approx(12.0)


def test_reconfiguration_blocked_while_input_on() -> None:
    device, transport = make_device()
    with device:
        transport.state["INPut"] = "1"
        with pytest.raises(UnsafeOperationError):
            device.set_current_setpoint(1.0)


def test_verified_current_setpoint() -> None:
    device, transport = make_device()
    with device:
        result = device.set_current_setpoint(2.5)
        assert result.verified is True
        assert result.applied == pytest.approx(2.5)
        assert transport.state["CURRent"] == "2.5"


def test_safe_configure_and_enable() -> None:
    device, transport = make_device()
    with device:
        result = device.configure_and_enable(
            SafeEnableConfig(mode=OperatingMode.CURRENT, setpoint=1.25)
        )
        assert result.input_enabled is True
        assert transport.state["INPut"] == "1"


def test_close_performs_best_effort_input_off() -> None:
    device, transport = make_device()
    device.connect()
    transport.state["INPut"] = "1"
    device.close()
    assert transport.state["INPut"] == "0"
    assert not transport.is_open


def test_raw_access_degrades_and_requires_resynchronization() -> None:
    device, _ = make_device()
    with device:
        assert device.query_raw_scpi("*STB?") == "0"
        assert device.session_state is SessionState.DEGRADED
        status = device.synchronize_state()
        assert status.synchronized
        assert device.session_state is SessionState.CONNECTED_READY

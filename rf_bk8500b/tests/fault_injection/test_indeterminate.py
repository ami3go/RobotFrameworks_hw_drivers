import pytest

from bk8500b import BK8500B, DriverConfig, IndeterminateCommandOutcome, SafetyPolicy
from tests.fakes import FakeSCPITransport


def test_state_write_timeout_is_never_blindly_retried() -> None:
    transport = FakeSCPITransport()
    device = BK8500B(
        DriverConfig(port="FAKE", minimum_command_interval_s=0),
        transport=transport,
    )
    device.connect()
    transport.fail_write_for.add("INPut ON")
    before = len(transport.writes)
    with pytest.raises(IndeterminateCommandOutcome):
        device.set_input_enabled(True)
    after_commands = [w.decode().strip() for w in transport.writes[before:]]
    assert after_commands.count("INPut ON") == 1
    device.close()


def test_read_only_query_is_retried_once() -> None:
    transport = FakeSCPITransport()
    device = BK8500B(
        DriverConfig(port="FAKE", minimum_command_interval_s=0),
        transport=transport,
    )
    device.connect()
    transport.fail_read_count = 1
    assert device.measure_voltage().value == pytest.approx(12.0)
    commands = [w.decode().strip() for w in transport.writes]
    assert commands.count("MEASure:VOLTage?") == 2
    device.close()


def test_enable_verification_timeout_is_indeterminate_without_replaying_enable() -> None:
    transport = FakeSCPITransport()
    device = BK8500B(
        DriverConfig(port="FAKE", minimum_command_interval_s=0),
        transport=transport,
    )
    device.connect()
    transport.fail_read_count = 2
    before = len(transport.writes)
    with pytest.raises(IndeterminateCommandOutcome):
        device.set_input_enabled(True)
    commands = [w.decode().strip() for w in transport.writes[before:]]
    assert commands.count("INPut ON") == 1
    assert commands.count("INPut?") == 2
    device.close()


def test_setpoint_verification_timeout_does_not_repeat_setter() -> None:
    transport = FakeSCPITransport()
    device = BK8500B(
        DriverConfig(
            port="FAKE",
            minimum_command_interval_s=0,
            safety=SafetyPolicy(require_off_before_reconfiguration=False),
        ),
        transport=transport,
    )
    device.connect()
    transport.fail_read_count = 2
    before = len(transport.writes)
    with pytest.raises(IndeterminateCommandOutcome):
        device.set_current_setpoint(2.0)
    commands = [w.decode().strip() for w in transport.writes[before:]]
    assert commands.count("CURRent 2") == 1
    assert commands.count("CURRent?") == 2
    device.close()

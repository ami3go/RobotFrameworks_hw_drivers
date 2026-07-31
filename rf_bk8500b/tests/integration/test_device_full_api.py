import pytest

from bk8500b import (
    BK8500B,
    DriverConfig,
    DynamicMode,
    LEDConfig,
    OCPTestConfig,
    OperatingMode,
    SafetyPolicy,
    SafetyToken,
    TimingTestConfig,
    TransientConfig,
    TriggerSource,
    UnsupportedFeatureError,
)
from bk8500b.enums import TriggerEdge
from bk8500b.measurements import ListConfig
from tests.fakes import FakeSCPITransport


def connected_device(*, safety: SafetyPolicy | None = None):
    transport = FakeSCPITransport()
    device = BK8500B(
        DriverConfig(
            port="FAKE",
            minimum_command_interval_s=0,
            safety=safety or SafetyPolicy(),
        ),
        transport=transport,
    )
    device.connect()
    return device, transport


def test_common_register_and_state_api() -> None:
    device, transport = connected_device()
    try:
        device.clear_status()
        device.set_event_status_enable(129)
        assert device.get_event_status_enable() == 129
        assert device.read_event_status_register() == 0
        device.operation_complete()
        assert device.is_operation_complete()
        device.set_power_on_status_clear(False)
        assert not device.get_power_on_status_clear()
        device.set_service_request_enable(128)
        assert device.get_service_request_enable() == 128
        assert device.read_status_byte() == 0
        assert device.self_test().passed
        device.save_state(3)
        assert any(w.decode().strip() == "*SAV 3" for w in transport.writes)
    finally:
        device.close()


def test_modes_ranges_slew_sense_and_thresholds() -> None:
    device, _ = connected_device()
    try:
        device.set_operating_mode(OperatingMode.VOLTAGE)
        assert device.get_operating_mode() is OperatingMode.VOLTAGE
        assert device.set_voltage_setpoint(10).verified
        assert device.get_voltage_setpoint() == 10
        assert device.set_power_setpoint(10).verified
        assert device.get_power_setpoint() == 10
        assert device.set_resistance_setpoint(10).verified
        assert device.get_resistance_setpoint() == 10
        assert device.set_current_range(5).verified
        assert device.get_current_range() == 5
        assert device.set_voltage_range(50).verified
        assert device.get_voltage_range() == 50
        device.set_voltage_autorange(False)
        assert not device.get_voltage_autorange()
        assert device.set_current_slew(2).verified
        assert device.set_current_slew_rise(3).verified
        assert device.set_current_slew_fall(4).verified
        assert device.get_current_slew().rise_a_per_us == 3
        device.set_remote_sense(True)
        assert device.get_remote_sense()
        assert device.set_load_on_voltage(2).verified
        assert device.get_load_on_voltage() == 2
        assert device.set_load_off_voltage(1).verified
        assert device.get_load_off_voltage() == 1
        assert device.set_current_protection(2).verified
        assert device.get_current_protection() == 2
        assert device.set_power_protection(20).verified
        assert device.get_power_protection() == 20
        assert device.set_dynamic_slew_rise(1.2).verified
        assert device.set_dynamic_slew_fall(1.1).verified
        assert device.set_voltage_time_low_threshold(1).verified
        assert device.set_voltage_time_high_threshold(10).verified
    finally:
        device.close()


def test_all_measurement_and_peak_methods() -> None:
    device, _ = connected_device()
    try:
        assert device.measure_voltage_maximum().value == 12.1
        assert device.measure_voltage_minimum().value == 11.9
        assert device.measure_voltage_peak_to_peak().value == 0.2
        assert device.measure_current_maximum().value == 1.1
        assert device.measure_current_minimum().value == 0.9
        assert device.measure_current_peak_to_peak().value == 0.2
        device.set_peak_enabled(True)
        device.clear_peak()
        assert device.read_peak_voltage_maximum().value == 12.2
        assert device.read_peak_voltage_minimum().value == 11.8
        assert device.read_peak_current_maximum().value == 1.2
        assert device.read_peak_current_minimum().value == 0.8
        assert device.read_voltage_rise_time().value == 0.002
        assert device.read_voltage_fall_time().value == 0.003
    finally:
        device.close()


def test_advanced_config_and_blocked_runs() -> None:
    device, _ = connected_device()
    try:
        transient = TransientConfig(1.0, 0.01, 0.1, 0.02, 2.0, DynamicMode.CONTINUOUS)
        device.configure_transient(transient)
        assert device.get_transient_config().high_level == 1.0
        led = LEDConfig(18, 0.35, 0.2)
        device.configure_led(led)
        assert device.get_led_config() == led
        device.configure_ocp_test(OCPTestConfig(1, 2, 10, 0.01, 5))
        device.set_ocp_test_enabled(False)
        assert not device.get_ocp_test_enabled()
        result = device.read_ocp_result()
        assert result.maximum_power_w == 55.34
        timing = TimingTestConfig(
            True,
            OperatingMode.CURRENT,
            1.0,
            TriggerSource.VOLTAGE,
            TriggerEdge.RISE,
            1.0,
            TriggerSource.VOLTAGE,
            TriggerEdge.FALL,
            5.0,
        )
        device.configure_timing_test(timing)
        device.set_timing_enabled(False)
        assert not device.get_timing_enabled()
        assert device.read_timing_result().duration_s == 0.004
        with pytest.raises(UnsupportedFeatureError):
            device.run_ocp_test()
        with pytest.raises(UnsupportedFeatureError):
            device.run_timing_test()
        with pytest.raises(UnsupportedFeatureError):
            device.configure_list(ListConfig(steps=()))
        with pytest.raises(UnsupportedFeatureError):
            device.run_list()
    finally:
        device.close()


def test_status_error_queue_and_protected_actions() -> None:
    safety = SafetyPolicy(allow_short=True)
    device, transport = connected_device(safety=safety)
    try:
        device.set_questionable_enable(32)
        assert device.get_questionable_enable() == 32
        device.set_operation_enable(64)
        assert device.get_operation_enable() == 64
        assert device.read_questionable_event() == 0
        assert device.read_operation_event() == 0
        transport.error_queue.extend(['-200,"Execution error"', '-100,"Command error"'])
        entries = device.drain_error_queue()
        assert [entry.code for entry in entries] == [-200, -100]
        short_token = SafetyToken.issue("enable_short")
        device.set_short_enabled(True, token=short_token)
        assert device.get_short_enabled()
        device.set_short_enabled(False, token=short_token)
        device.clear_protection(token=SafetyToken.issue("clear_protection"))
        device.trigger()
    finally:
        device.close()


def test_local_reset_and_recall_require_resync() -> None:
    device, _ = connected_device()
    try:
        device.set_remote()
        device.set_remote_with_local_lockout()
        device.set_local()
        device.synchronize_state()
        device.reset_device()
        device.synchronize_state()
        device.recall_state(1)
        device.synchronize_state()
    finally:
        device.close()

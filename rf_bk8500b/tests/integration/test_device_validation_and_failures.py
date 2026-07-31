from __future__ import annotations

import math
import pytest

from bk8500b import (
    BK8500B, DriverConfig, DynamicMode, InstrumentRangeError, InvalidStateTransitionError,
    LEDConfig, MalformedResponseError, OCPTestConfig, OperatingMode, Protocol,
    ReconnectPolicy, SafeEnableConfig, SafetyPolicy, SafetyToken, SessionState,
    TimingTestConfig, TransientConfig, TriggerSource,
    UnsupportedFeatureError, UnsafeOperationError,
)
from bk8500b.enums import ProtectionFlag, TriggerEdge
from bk8500b.exceptions import ProtectionTrippedError
from bk8500b.status import DeviceStatus
from tests.fakes import FakeSCPITransport
from tests.fakes_legacy import FakeLegacyTransport


def connected(*, safety: SafetyPolicy | None = None, transport=None, reconnect=None):
    tr = transport or FakeSCPITransport()
    policy = safety or SafetyPolicy(turn_input_off_on_close=False)
    cfg = DriverConfig(
        port="F", minimum_command_interval_s=0, safety=policy,
        reconnect=reconnect or ReconnectPolicy(),
    )
    d = BK8500B(cfg, transport=tr)
    d.connect()
    return d, tr


def close(d):
    if d.session_state not in {SessionState.DISCONNECTED, SessionState.FAILED}:
        d.close()
    elif d.session_state is SessionState.FAILED:
        d.close()


@pytest.mark.parametrize("method,value", [
    ("set_event_status_enable", -1), ("set_event_status_enable", 256),
    ("set_service_request_enable", -1), ("set_service_request_enable", 256),
    ("save_state", -1), ("save_state", 100),
    ("recall_state", -1), ("recall_state", 10),
    ("set_questionable_enable", -1), ("set_questionable_enable", 32768),
    ("set_operation_enable", -1), ("set_operation_enable", 65536),
])
def test_common_range_validation(method, value):
    d, _ = connected()
    try:
        with pytest.raises(InstrumentRangeError): getattr(d, method)(value)
    finally: close(d)


def test_setpoint_validation_and_unverified_path(monkeypatch):
    d, _ = connected(safety=SafetyPolicy(verify_critical_writes=False, turn_input_off_on_close=False))
    try:
        assert not d.set_current_setpoint(1).verified
        with pytest.raises(InstrumentRangeError): d.set_current_setpoint(math.nan)
        with pytest.raises(InstrumentRangeError): d.set_current_setpoint(9999)
        with pytest.raises(InstrumentRangeError): d.set_resistance_setpoint(-1)
    finally: close(d)


def test_setpoint_and_boolean_verification_mismatches(monkeypatch):
    d, _ = connected(safety=SafetyPolicy(allow_short=True, turn_input_off_on_close=False))
    try:
        monkeypatch.setattr(d, "_q_float", lambda *a, **k: 2.0)
        with pytest.raises(MalformedResponseError): d.set_current_setpoint(1.0)
        monkeypatch.setattr(d, "get_input_enabled", lambda: False)
        with pytest.raises(MalformedResponseError): d.set_input_enabled(True)
        monkeypatch.setattr(d, "get_short_enabled", lambda: False)
        with pytest.raises(MalformedResponseError): d.set_short_enabled(True, token=SafetyToken.issue("enable_short"))
        monkeypatch.setattr(d, "get_operating_mode", lambda: OperatingMode.VOLTAGE)
        with pytest.raises(MalformedResponseError): d.set_operating_mode(OperatingMode.CURRENT)
        monkeypatch.setattr(d, "get_voltage_autorange", lambda: False)
        with pytest.raises(MalformedResponseError): d.set_voltage_autorange(True)
        monkeypatch.setattr(d, "get_remote_sense", lambda: False)
        with pytest.raises(MalformedResponseError): d.set_remote_sense(True)
    finally: close(d)


def test_safety_tokens_and_short_policy():
    d, _ = connected(safety=SafetyPolicy(require_enable_token=True, turn_input_off_on_close=False))
    try:
        with pytest.raises(UnsafeOperationError): d.set_input_enabled(True)
        with pytest.raises(UnsafeOperationError): d.set_input_enabled(True, token=SafetyToken.issue("wrong"))
        d.set_input_enabled(True, token=SafetyToken.issue("enable_input"))
        d.set_input_enabled(False)
        with pytest.raises(UnsafeOperationError): d.set_short_enabled(True, token=SafetyToken.issue("enable_short"))
        with pytest.raises(UnsafeOperationError): d.clear_protection(token=SafetyToken.issue("wrong"))
    finally: close(d)


def test_mode_type_and_operation_complete_validation(monkeypatch):
    d, _ = connected()
    try:
        with pytest.raises(TypeError): d.set_operating_mode("CURRent")
        monkeypatch.setattr(d, "_q_text", lambda *a, **k: "0")
        with pytest.raises(MalformedResponseError): d.operation_complete()
    finally: close(d)


def test_safe_enable_prevalidation():
    d, _ = connected()
    try:
        with pytest.raises(TypeError): d.configure_and_enable(object())
        with pytest.raises(UnsupportedFeatureError):
            d.configure_and_enable(SafeEnableConfig(OperatingMode.CURRENT, 1, voltage_limit_v=1))
        with pytest.raises(UnsupportedFeatureError):
            d.configure_and_enable(SafeEnableConfig(OperatingMode.CURRENT, 1, resistance_limit_ohm=1))
        with pytest.raises(UnsupportedFeatureError):
            d.configure_and_enable(SafeEnableConfig(OperatingMode.DYNAMIC, 1))
        with pytest.raises(InstrumentRangeError):
            d.configure_and_enable(SafeEnableConfig(OperatingMode.CURRENT, 1, current_limit_a=9999))
        with pytest.raises(InstrumentRangeError):
            d.configure_and_enable(SafeEnableConfig(OperatingMode.CURRENT, 1, power_limit_w=999999))
    finally: close(d)


def test_safe_enable_protection_rolls_back(monkeypatch):
    d, tr = connected()
    protected = DeviceStatus(False, False, OperatingMode.CURRENT, 0, 2, 0, ProtectionFlag.OVER_CURRENT, 0, True)
    monkeypatch.setattr(d, "get_device_status", lambda: protected)
    try:
        with pytest.raises(ProtectionTrippedError) as exc:
            d.configure_and_enable(SafeEnableConfig(OperatingMode.CURRENT, 1))
        assert exc.value.context["input_off_after_failure"] is True
        assert tr.state["INPut"] == "0"
    finally: close(d)


def test_safe_enable_detects_failed_final_enable(monkeypatch):
    d, _ = connected()
    normal = DeviceStatus(False, False, OperatingMode.CURRENT, 0, 0, 0, ProtectionFlag.NONE, 0, True)
    calls = iter([normal, normal])
    monkeypatch.setattr(d, "get_device_status", lambda: next(calls))
    monkeypatch.setattr(d, "set_input_enabled", lambda enabled, token=None: None)
    try:
        with pytest.raises(MalformedResponseError):
            d.configure_and_enable(SafeEnableConfig(OperatingMode.CURRENT, 1))
    finally: close(d)


def test_transient_led_ocp_and_timing_validation(monkeypatch):
    d, tr = connected()
    try:
        with pytest.raises(TypeError): d.configure_transient(object())
        with pytest.raises(InstrumentRangeError):
            d.configure_transient(TransientConfig(-1, .01, 0, .01, 1))
        tr.state["DYNamic:MODE"] = "UNKNOWN"
        with pytest.raises(MalformedResponseError): d.get_transient_config()
        with pytest.raises(InstrumentRangeError): d.configure_led(LEDConfig(1, 1, 0))
        with pytest.raises(InstrumentRangeError): d.configure_ocp_test(OCPTestConfig(2, 1, 2, .01, 1))
        with pytest.raises(InstrumentRangeError): d.configure_ocp_test(OCPTestConfig(1, 2, 0, .01, 1))
        with pytest.raises(InstrumentRangeError): d.configure_ocp_test(OCPTestConfig(1, 2, 2, 1.5, 1))
        bad_mode = TimingTestConfig(True, OperatingMode.DYNAMIC, 1, TriggerSource.VOLTAGE, TriggerEdge.RISE, 1, TriggerSource.VOLTAGE, TriggerEdge.FALL, 2)
        with pytest.raises(UnsupportedFeatureError): d.configure_timing_test(bad_mode)
        nonfinite = TimingTestConfig(True, OperatingMode.CURRENT, math.nan, TriggerSource.VOLTAGE, TriggerEdge.RISE, 1, TriggerSource.VOLTAGE, TriggerEdge.FALL, 2)
        with pytest.raises(InstrumentRangeError): d.configure_timing_test(nonfinite)
    finally: close(d)


def test_ocp_malformed_result():
    class BadOCP(FakeSCPITransport):
        def _handle(self, text):
            if text == "OCP:RESult:PMAX?": self.responses.append(b"1,2\n"); return
            super()._handle(text)
    d, _ = connected(transport=BadOCP())
    try:
        with pytest.raises(MalformedResponseError): d.read_ocp_result()
    finally: close(d)


def test_drain_limits_and_full_queue():
    d, tr = connected()
    try:
        with pytest.raises(InstrumentRangeError): d.drain_error_queue(maximum=0)
        tr.error_queue.extend(['-1,"x"', '-2,"y"'])
        result = d.drain_error_queue(maximum=2)
        assert len(result) == 2
    finally: close(d)


def test_measure_all_tolerates_optional_failures(monkeypatch):
    d, _ = connected()
    monkeypatch.setattr(d, "get_device_status", lambda: (_ for _ in ()).throw(MalformedResponseError("status")))
    monkeypatch.setattr(d, "measure_resistance", lambda: (_ for _ in ()).throw(MalformedResponseError("res")))
    try:
        snap = d.measure_all()
        assert snap.status is None and snap.resistance is None
    finally: close(d)


def test_raw_write_degrades_and_protocol_mixing_is_blocked():
    d, _ = connected()
    try:
        d.write_raw_scpi("*CLS")
        assert d.session_state is SessionState.DEGRADED
        with pytest.raises(UnsupportedFeatureError): d.transact_raw_legacy(b"x" * 26)
    finally: close(d)


def test_legacy_identify_without_cached_identity_and_raw_scpi_blocked():
    tr = FakeLegacyTransport()
    cfg = DriverConfig(port="F", protocol=Protocol.LEGACY, minimum_command_interval_s=0, safety=SafetyPolicy(turn_input_off_on_close=False))
    d = BK8500B(cfg, transport=tr); d.connect(); d._identity = None
    try:
        with pytest.raises(UnsupportedFeatureError): d.identify()
        with pytest.raises(UnsupportedFeatureError): d.write_raw_scpi("*CLS")
    finally: close(d)


def test_decode_protection_flags_and_unknown_bits():
    flags, unknown = BK8500B._decode_protection((1 << 0) | (1 << 13) | (1 << 15))
    assert flags & ProtectionFlag.REVERSE_VOLTAGE
    assert flags & ProtectionFlag.OVER_VOLTAGE
    assert unknown == 1 << 15


def test_refresh_capabilities_and_scpi_version():
    d, _ = connected()
    try:
        assert d.get_scpi_version() == "1999.0"
        before = d.get_capabilities()
        d._capabilities = None
        assert d.get_capabilities(refresh=True).model == before.model
    finally: close(d)


def test_reconnect_wrong_state():
    d = BK8500B(DriverConfig(port="F", reconnect=ReconnectPolicy(enabled=True)), transport=FakeSCPITransport())
    with pytest.raises(InvalidStateTransitionError): d.reconnect()

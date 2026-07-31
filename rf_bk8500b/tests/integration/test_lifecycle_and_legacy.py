import pytest

from bk8500b import (
    BK8500B, ConfigurationError, DriverConfig, InvalidStateTransitionError,
    Protocol, ReconnectPolicy, SafetyPolicy, SessionState, UnsupportedFeatureError,
    UnsupportedModelError, UnsafeOperationError,
)
from bk8500b.protocol.legacy_codec import build_frame
from tests.fakes import FakeSCPITransport
from tests.fakes_legacy import AutoLegacyTransport, FakeLegacyTransport


def test_constructor_type_and_disconnected_close() -> None:
    with pytest.raises(ConfigurationError): BK8500B(object())
    d = BK8500B(DriverConfig(port="FAKE"), transport=FakeSCPITransport())
    d.close()
    with pytest.raises(InvalidStateTransitionError): d.measure_voltage()
    with pytest.raises(InvalidStateTransitionError): d.synchronize_state()


def test_connect_is_idempotent_for_same_open_session() -> None:
    t = FakeSCPITransport(); d = BK8500B(DriverConfig(port="F", minimum_command_interval_s=0), transport=t)
    d.connect(); count = len(t.writes); d.connect(); assert len(t.writes) == count; d.close()


def test_connect_failure_returns_to_disconnected() -> None:
    t = FakeSCPITransport(); t.identity_response = "bad"
    d = BK8500B(DriverConfig(port="F", minimum_command_interval_s=0), transport=t)
    with pytest.raises(Exception): d.connect()
    assert d.session_state is SessionState.DISCONNECTED
    assert not t.is_open


def test_legacy_explicit_and_raw_transaction() -> None:
    t = FakeLegacyTransport()
    d = BK8500B(DriverConfig(port="F", protocol=Protocol.LEGACY, minimum_command_interval_s=0), transport=t)
    d.connect()
    assert d.session_state is SessionState.DEGRADED
    assert d.identify().model == "8500B-series legacy"
    with pytest.raises(UnsupportedFeatureError): d.synchronize_state()
    frame = build_frame(0, 0x01)
    assert d.transact_raw_legacy(frame) == frame
    with pytest.raises(UnsafeOperationError): d.transact_raw_legacy(build_frame(0xFF, 0x01))
    with pytest.raises(UnsupportedFeatureError): d.query_raw_scpi("*IDN?")
    d.close()


def test_auto_detection_falls_back_to_legacy() -> None:
    t = AutoLegacyTransport()
    d = BK8500B(DriverConfig(port="F", protocol=Protocol.AUTO, minimum_command_interval_s=0, retry=__import__('bk8500b').RetryPolicy(max_read_attempts=1)), transport=t)
    d.connect()
    assert d.session_state is SessionState.DEGRADED
    assert t.open_count == 2
    d.close()


def test_reconnect_success_and_disabled_policy() -> None:
    t = FakeSCPITransport()
    d = BK8500B(DriverConfig(port="F", minimum_command_interval_s=0), transport=t)
    d.connect()
    with pytest.raises(InvalidStateTransitionError): d.reconnect()
    d.close()

    t2 = FakeSCPITransport()
    cfg = DriverConfig(port="F", minimum_command_interval_s=0, reconnect=ReconnectPolicy(enabled=True))
    d2 = BK8500B(cfg, transport=t2); d2.connect(); d2.reconnect()
    assert d2.session_state is SessionState.CONNECTED_READY
    d2.close()


def test_reconnect_wrong_device_fails() -> None:
    class ChangedIdentityTransport(FakeSCPITransport):
        def open(self):
            super().open()
            if len([w for w in self.writes if w.decode().strip() == "*IDN?"]) >= 1:
                self.identity_response = "B&K Precision,BK8500B,OTHER,1.45"
    t = ChangedIdentityTransport()
    cfg = DriverConfig(port="F", minimum_command_interval_s=0, reconnect=ReconnectPolicy(enabled=True, max_attempts=1, total_deadline_s=1))
    d = BK8500B(cfg, transport=t); d.connect()
    with pytest.raises(UnsupportedModelError): d.reconnect()
    assert d.session_state is SessionState.FAILED
    d.close()


def test_unknown_model_hazard_blocked() -> None:
    t = FakeSCPITransport(); t.identity_response = "Vendor,UnknownModel,SN,1"
    d = BK8500B(DriverConfig(port="F", minimum_command_interval_s=0), transport=t); d.connect()
    with pytest.raises(UnsupportedModelError): d.set_input_enabled(True)
    d.set_input_enabled(False)
    d.close()


def test_health_degrades_and_diagnostic_partial() -> None:
    t = FakeSCPITransport(); d = BK8500B(DriverConfig(port="F", minimum_command_interval_s=0), transport=t); d.connect()
    t.fail_read_count = 6
    assert not d.health_check().healthy
    assert not d.health_check().healthy
    assert not d.health_check().healthy
    assert d.session_state is SessionState.DEGRADED
    t.fail_read_count = 2
    snap = d.diagnostic_snapshot()
    assert snap.partial
    d.close()


def test_close_swallows_best_effort_input_off_failure() -> None:
    t = FakeSCPITransport(); d = BK8500B(DriverConfig(port="F", minimum_command_interval_s=0), transport=t); d.connect()
    t.fail_write_for.add("INPut OFF")
    d.close()
    assert d.session_state is SessionState.DISCONNECTED
    assert "close input-off" in (d.diagnostic_snapshot().last_error or "")

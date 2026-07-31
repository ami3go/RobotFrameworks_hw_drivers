import inspect

import bk8500b


REQUIRED = {
    "BK8500B", "AsyncBK8500B", "DriverConfig", "RetryPolicy", "ReconnectPolicy",
    "SafetyPolicy", "Protocol", "OperatingMode", "DynamicMode", "TriggerSource",
    "SessionState", "CommandOutcome", "InstrumentIdentity", "InstrumentCapabilities",
    "Measurement", "MeasurementSnapshot", "AppliedSetpoint", "DeviceStatus",
    "DiagnosticSnapshot", "HealthReport", "SelfTestResult", "SCPIErrorEntry",
    "ProtectionFlag", "SafetyToken", "SlewRate", "TransientConfig", "LEDConfig",
    "OCPTestConfig", "OCPTestResult", "TimingTestConfig", "TimingTestResult",
    "ListConfig", "ListRunResult", "SafeEnableConfig", "SafeEnableResult",
}


def test_required_public_exports_present() -> None:
    assert REQUIRED <= set(bk8500b.__all__)


def test_constructor_does_not_open_transport() -> None:
    from tests.fakes import FakeSCPITransport
    transport = FakeSCPITransport()
    bk8500b.BK8500B(bk8500b.DriverConfig(port="FAKE"), transport=transport)
    assert not transport.is_open


def test_frozen_method_signatures() -> None:
    sig = inspect.signature(bk8500b.BK8500B.set_input_enabled)
    assert list(sig.parameters) == ["self", "enabled", "token"]
    assert sig.parameters["token"].kind is inspect.Parameter.KEYWORD_ONLY

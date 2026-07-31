from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import math
import pytest

from bk8500b import DriverConfig, Protocol
from bk8500b.diagnostics import AuditEvent, NullAuditSink, NullMetricsSink
from bk8500b.enums import CommandOutcome, OperatingMode, RiskClass, SessionState
from bk8500b.exceptions import FrameSyncError, InvalidStateTransitionError, ReadTimeoutError, UnsupportedFeatureError
from bk8500b.execution import CommandExecutor
from bk8500b.measurements import InstrumentIdentity, Measurement
from bk8500b.protocol.legacy import LegacyProtocol
from bk8500b.protocol.legacy_codec import build_frame
from bk8500b.state_machine import SessionStateMachine, TransactionStateMachine
from bk8500b.status import DiagnosticSnapshot, HealthReport, _json_value


class ByteTransport:
    def __init__(self, chunks=()): self.chunks=deque(chunks); self._open=True
    @property
    def is_open(self): return self._open
    def open(self): self._open=True
    def close(self): self._open=False
    def write(self, data, *, timeout_s=None): return len(data)
    def read(self, size, *, timeout_s=None):
        if not self.chunks: raise ReadTimeoutError("empty")
        return self.chunks.popleft()
    def read_until(self, *a, **k): raise ReadTimeoutError("unused")
    def reset_input_buffer(self): pass
    def reset_output_buffer(self): pass


def legacy(chunks):
    cfg=DriverConfig(port="x", protocol=Protocol.LEGACY, minimum_command_interval_s=0)
    tr=ByteTransport(chunks)
    return LegacyProtocol(cfg, CommandExecutor(cfg,tr))


def test_legacy_frame_reader_skips_noise_and_handles_partial_and_timeout():
    frame=build_frame(0,1)
    p=legacy([b"\x00", *[bytes([b]) for b in frame]])
    assert p._read_frame(0.1) == frame
    with pytest.raises(FrameSyncError): legacy([b"\xaa", b"\x00"])._read_frame(0.01)
    with pytest.raises(ReadTimeoutError): legacy([])._read_frame(0.01)
    with pytest.raises(UnsupportedFeatureError): p.stable_command()


def test_state_machine_noop_fail_and_terminal_rejection():
    sm=SessionStateMachine(); sm.transition(SessionState.DISCONNECTED)
    with pytest.raises(InvalidStateTransitionError): sm.fail()
    sm.transition(SessionState.CONNECTING); sm.fail(); sm.fail()
    assert sm.state is SessionState.FAILED
    tx=TransactionStateMachine(); tx.transition(CommandOutcome.FAILED_NOT_SENT)
    with pytest.raises(InvalidStateTransitionError): tx.transition(CommandOutcome.COMPLETED)


def test_status_json_conversion_and_diagnostic_models():
    assert _json_value(b"\x01") == "01"
    assert _json_value(Protocol.SCPI) == "scpi"
    assert _json_value({1:(Protocol.LEGACY,b"\x02")}) == {"1":["legacy","02"]}
    assert _json_value("plain") == "plain"
    ident=InstrumentIdentity("B&K","BK8500B","S","1","raw")
    health=HealthReport(True,SessionState.CONNECTED_READY,ident,0.1,0,"ok")
    assert health.to_dict()["session_state"] == "connected_ready"
    snap=DiagnosticSnapshot(datetime.now(timezone.utc),SessionState.CONNECTED_READY,Protocol.SCPI,True,ident,None,None,{"x":1},False,("n",))
    assert snap.to_dict()["protocol"] == "scpi"


def test_audit_event_and_null_sinks():
    event=AuditEvent.create("op",RiskClass.READ_ONLY,CommandOutcome.COMPLETED,"done",context={"x":1})
    data=event.to_dict(); assert data["risk"] == "read_only" and data["outcome"] == "completed"
    NullAuditSink().record(event)
    NullMetricsSink().increment("x")
    NullMetricsSink().observe("x",1.0)


def test_enum_and_measurement_invalid_values():
    with pytest.raises(ValueError): OperatingMode.from_response("unknown")
    with pytest.raises(ValueError): Measurement.now(math.nan,"V",Protocol.SCPI)

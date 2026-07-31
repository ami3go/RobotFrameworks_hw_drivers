from __future__ import annotations

import time
import pytest

from bk8500b import DriverConfig, RetryPolicy
from bk8500b.diagnostics import AuditEvent
from bk8500b.enums import RiskClass
from bk8500b.exceptions import (
    ConnectionLostError, IndeterminateCommandOutcome, LockTimeoutError,
    ReadTimeoutError, TransportError, WriteTimeoutError,
)
from bk8500b.execution import CommandExecutor


class ScriptedTransport:
    def __init__(self):
        self._open = True
        self.write_error = None
        self.read_actions = []
        self.reset_error = None
        self.writes = []
    @property
    def is_open(self): return self._open
    def open(self): self._open = True
    def close(self): self._open = False
    def write(self, data, *, timeout_s=None):
        self.writes.append(data)
        if self.write_error: raise self.write_error
        return len(data)
    def read(self, size, *, timeout_s=None):
        action = self.read_actions.pop(0)
        if isinstance(action, Exception): raise action
        return action
    def read_until(self, terminator, *, maximum_bytes, timeout_s=None):
        return self.read(maximum_bytes, timeout_s=timeout_s)
    def reset_input_buffer(self):
        if self.reset_error: raise self.reset_error
    def reset_output_buffer(self): pass


class RecordingMetrics:
    def __init__(self): self.calls = []
    def increment(self, name, value=1, **labels): self.calls.append(("inc", name, value, labels))
    def observe(self, name, value, **labels): self.calls.append(("obs", name, value, labels))


class FailingAudit:
    def record(self, event: AuditEvent): raise RuntimeError("sink failed")


class SlowAudit:
    def record(self, event: AuditEvent): time.sleep(0.011)


def executor(transport=None, **cfg):
    tr = transport or ScriptedTransport()
    config = DriverConfig(**({"port": "x", "minimum_command_interval_s": 0} | cfg))
    return CommandExecutor(config, tr), tr


def test_lock_timeout():
    ex, _ = executor(lock_timeout_s=0.001)
    ex._lock.acquire()
    try:
        with pytest.raises(LockTimeoutError): ex.write(b"x", operation="locked")
    finally:
        ex._lock.release()


@pytest.mark.parametrize("error", [WriteTimeoutError("timeout"), ConnectionLostError("lost")])
def test_write_after_dispatch_is_indeterminate(error):
    ex, tr = executor(); tr.write_error = error
    with pytest.raises(IndeterminateCommandOutcome):
        ex.write(b"x", operation="write", risk=RiskClass.HAZARDOUS)
    assert ex.counters["indeterminate"] == 1


def test_query_write_timeout_is_indeterminate():
    ex, tr = executor(); tr.write_error = WriteTimeoutError("timeout")
    with pytest.raises(IndeterminateCommandOutcome):
        ex.query(b"q", operation="query", read_response=lambda _: b"x", validate_response=lambda x: x)


def test_retry_read_timeout_reset_failure_then_success(monkeypatch):
    ex, tr = executor(retry=RetryPolicy(max_read_attempts=2, initial_backoff_s=0, maximum_backoff_s=0))
    tr.read_actions = [ReadTimeoutError("first"), b"ok"]
    tr.reset_error = TransportError("reset failed")
    result = ex.query(
        b"q", operation="retry",
        read_response=lambda _: tr.read(2), validate_response=lambda x: x,
    )
    assert result == b"ok" and ex.counters["read_retries"] == 1


def test_destructive_read_timeout_is_indeterminate():
    ex, tr = executor(); tr.read_actions = [ReadTimeoutError("timeout")]
    with pytest.raises(IndeterminateCommandOutcome):
        ex.query(
            b"q", operation="destructive", read_response=lambda _: tr.read(1),
            validate_response=lambda x: x, destructive_read=True,
        )


def test_connection_loss_during_read_is_indeterminate():
    ex, tr = executor(); tr.read_actions = [ConnectionLostError("lost")]
    with pytest.raises(IndeterminateCommandOutcome):
        ex.query(b"q", operation="lost", read_response=lambda _: tr.read(1), validate_response=lambda x: x)


def test_validation_failure_is_protocol_failure():
    ex, tr = executor(); tr.read_actions = [b"bad"]
    with pytest.raises(ValueError):
        ex.query(
            b"q", operation="validate", read_response=lambda _: tr.read(3),
            validate_response=lambda _: (_ for _ in ()).throw(ValueError("bad")),
        )
    assert ex.counters["failures"] == 1


def test_audit_extensions_cannot_break_success_and_metrics_are_emitted():
    metrics = RecordingMetrics()
    cfg = DriverConfig(port="x", minimum_command_interval_s=0)
    tr = ScriptedTransport()
    ex = CommandExecutor(cfg, tr, audit_sink=FailingAudit(), metrics_sink=metrics)
    ex.write(b"x", operation="ok")
    assert ex.counters["failures"] == 1
    assert any(call[0] == "inc" for call in metrics.calls)


def test_slow_audit_is_counted():
    cfg = DriverConfig(port="x", minimum_command_interval_s=0)
    ex = CommandExecutor(cfg, ScriptedTransport(), audit_sink=SlowAudit())
    ex.write(b"x", operation="slow")
    assert ex.counters["audit_sink_slow"] == 1


def test_pacing_and_backoff_sleep(monkeypatch):
    sleeps = []
    monkeypatch.setattr("bk8500b.execution.time.sleep", sleeps.append)
    ex, _ = executor(minimum_command_interval_s=0.1)
    ex._last_command_monotonic = time.monotonic()
    ex._pace()
    ex._backoff(0)
    assert sleeps

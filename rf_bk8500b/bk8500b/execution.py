"""Serialized, deadline-bounded command execution.

The executor is deliberately protocol-agnostic. It never retries state-changing
writes and turns any post-write ambiguity into IndeterminateCommandOutcome.
"""
from __future__ import annotations

from contextlib import contextmanager
import logging
import random
from threading import Lock
import time
from typing import Callable, TypeVar

from .config import DriverConfig
from .diagnostics import AuditEvent, AuditSink, MetricsSink, NullAuditSink, NullMetricsSink
from .enums import CommandOutcome, RiskClass
from .exceptions import (
    IndeterminateCommandOutcome,
    LockTimeoutError,
    ReadTimeoutError,
    TransportError,
    WriteTimeoutError,
)
from .state_machine import TransactionStateMachine
from .transport import Transport

T = TypeVar("T")
_LOG = logging.getLogger(__name__)


class CommandExecutor:
    def __init__(
        self,
        config: DriverConfig,
        transport: Transport,
        *,
        audit_sink: AuditSink | None = None,
        metrics_sink: MetricsSink | None = None,
    ) -> None:
        self.config = config
        self.transport = transport
        self.audit_sink = audit_sink or NullAuditSink()
        self.metrics_sink = metrics_sink or NullMetricsSink()
        self._lock = Lock()
        self._last_command_monotonic = 0.0
        self.counters: dict[str, int | float] = {
            "transactions": 0,
            "completed": 0,
            "failures": 0,
            "indeterminate": 0,
            "read_retries": 0,
            "audit_sink_slow": 0,
        }
        self.last_audit_event_id: str | None = None

    @contextmanager
    def _owned_lock(self):
        acquired = self._lock.acquire(timeout=self.config.lock_timeout_s)
        if not acquired:
            raise LockTimeoutError(
                "Timed out waiting for the session command lock",
                context={"timeout_s": self.config.lock_timeout_s},
            )
        try:
            yield
        finally:
            self._lock.release()

    def _pace(self) -> None:
        interval = self.config.minimum_command_interval_s
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_command_monotonic
        if elapsed < interval:
            time.sleep(interval - elapsed)

    def _audit(
        self,
        operation: str,
        risk: RiskClass,
        outcome: CommandOutcome,
        detail: str,
        *,
        context: dict | None = None,
    ) -> str:
        event = AuditEvent.create(operation, risk, outcome, detail, context=context)
        started = time.monotonic()
        try:
            self.audit_sink.record(event)
        except Exception:  # audit sinks are extensions; never turn a device success into failure
            _LOG.exception("Audit sink failed")
            self.counters["failures"] = int(self.counters["failures"]) + 1
        elapsed = time.monotonic() - started
        if elapsed > 0.010:
            self.counters["audit_sink_slow"] = int(self.counters["audit_sink_slow"]) + 1
            _LOG.warning("Audit sink blocked command path for %.6fs", elapsed)
        self.last_audit_event_id = event.event_id
        return event.event_id

    def _backoff(self, attempt_index: int) -> None:
        policy = self.config.retry
        base = min(
            policy.maximum_backoff_s,
            policy.initial_backoff_s * (2**attempt_index),
        )
        jitter = base * policy.jitter_fraction
        delay = max(0.0, base + random.uniform(-jitter, jitter))
        if delay:
            time.sleep(delay)

    def write(
        self,
        payload: bytes,
        *,
        operation: str,
        risk: RiskClass = RiskClass.CONFIGURATION,
        timeout_s: float | None = None,
    ) -> str:
        tx = TransactionStateMachine()
        tx.transition(CommandOutcome.VALIDATED)
        self.counters["transactions"] = int(self.counters["transactions"]) + 1
        started = time.monotonic()
        try:
            tx.transition(CommandOutcome.WAITING_FOR_LOCK)
            with self._owned_lock():
                self._pace()
                tx.transition(CommandOutcome.WRITING)
                try:
                    self.transport.write(
                        payload,
                        timeout_s=self.config.write_timeout_s if timeout_s is None else timeout_s,
                    )
                except WriteTimeoutError as exc:
                    tx.transition(CommandOutcome.OUTCOME_INDETERMINATE)
                    self.counters["indeterminate"] = int(self.counters["indeterminate"]) + 1
                    event_id = self._audit(
                        operation,
                        risk,
                        tx.state,
                        "Write timed out after transmission may have begun",
                        context={"payload_length": len(payload)},
                    )
                    raise IndeterminateCommandOutcome(
                        f"Outcome of {operation!r} is indeterminate",
                        context={"operation": operation, "audit_event_id": event_id},
                    ) from exc
                tx.transition(CommandOutcome.WRITE_COMPLETE)
                self._last_command_monotonic = time.monotonic()
                tx.transition(CommandOutcome.COMPLETED)
            self.counters["completed"] = int(self.counters["completed"]) + 1
            self.metrics_sink.increment("bk8500b_transactions_total", outcome="completed")
            self.metrics_sink.observe(
                "bk8500b_transaction_duration_seconds", time.monotonic() - started,
                operation=operation,
            )
            return self._audit(operation, risk, tx.state, "Command completed")
        except (IndeterminateCommandOutcome, LockTimeoutError):
            self.counters["failures"] = int(self.counters["failures"]) + 1
            raise
        except TransportError as exc:
            self.counters["failures"] = int(self.counters["failures"]) + 1
            if tx.state == CommandOutcome.WRITING:
                tx.transition(CommandOutcome.OUTCOME_INDETERMINATE)
                self.counters["indeterminate"] = int(self.counters["indeterminate"]) + 1
                event_id = self._audit(operation, risk, tx.state, "Transport failed during write")
                raise IndeterminateCommandOutcome(
                    f"Outcome of {operation!r} is indeterminate",
                    context={"operation": operation, "audit_event_id": event_id},
                ) from exc
            self._audit(operation, risk, CommandOutcome.FAILED_NOT_SENT, "Transport failure before confirmed write")
            raise

    def query(
        self,
        payload: bytes,
        *,
        operation: str,
        read_response: Callable[[float], bytes],
        validate_response: Callable[[bytes], T],
        timeout_s: float | None = None,
        retryable: bool = True,
        destructive_read: bool = False,
    ) -> T:
        attempts = self.config.retry.max_read_attempts if retryable and not destructive_read else 1
        deadline_per_attempt = self.config.query_timeout_s if timeout_s is None else timeout_s
        last_error: Exception | None = None
        for attempt in range(attempts):
            tx = TransactionStateMachine()
            tx.transition(CommandOutcome.VALIDATED)
            self.counters["transactions"] = int(self.counters["transactions"]) + 1
            started = time.monotonic()
            try:
                tx.transition(CommandOutcome.WAITING_FOR_LOCK)
                with self._owned_lock():
                    self._pace()
                    tx.transition(CommandOutcome.WRITING)
                    try:
                        self.transport.write(payload, timeout_s=self.config.write_timeout_s)
                    except WriteTimeoutError as exc:
                        tx.transition(CommandOutcome.OUTCOME_INDETERMINATE)
                        self.counters["indeterminate"] = int(self.counters["indeterminate"]) + 1
                        event_id = self._audit(
                            operation,
                            RiskClass.READ_ONLY,
                            tx.state,
                            "Query write timed out",
                        )
                        raise IndeterminateCommandOutcome(
                            f"Query {operation!r} may have been accepted",
                            context={"audit_event_id": event_id},
                        ) from exc
                    tx.transition(CommandOutcome.WRITE_COMPLETE)
                    self._last_command_monotonic = time.monotonic()
                    tx.transition(CommandOutcome.READING)
                    raw = read_response(deadline_per_attempt)
                    tx.transition(CommandOutcome.RESPONSE_VALIDATED)
                    value = validate_response(raw)
                    tx.transition(CommandOutcome.COMPLETED)
                self.counters["completed"] = int(self.counters["completed"]) + 1
                self.metrics_sink.increment("bk8500b_transactions_total", outcome="completed")
                self.metrics_sink.observe(
                    "bk8500b_transaction_duration_seconds",
                    time.monotonic() - started,
                    operation=operation,
                )
                self._audit(operation, RiskClass.READ_ONLY, tx.state, "Query completed")
                return value
            except ReadTimeoutError as exc:
                last_error = exc
                if tx.state == CommandOutcome.READING:
                    if destructive_read:
                        tx.transition(CommandOutcome.OUTCOME_INDETERMINATE)
                    else:
                        tx.transition(CommandOutcome.RETRYABLE_READ_FAILURE)
                self._audit(
                    operation,
                    RiskClass.READ_ONLY,
                    tx.state,
                    "Read timed out",
                    context={"attempt": attempt + 1, "attempts": attempts},
                )
                if attempt + 1 >= attempts:
                    if destructive_read:
                        self.counters["indeterminate"] = int(self.counters["indeterminate"]) + 1
                        raise IndeterminateCommandOutcome(
                            f"Destructive query {operation!r} timed out; register/queue state is unknown"
                        ) from exc
                    raise
                self.counters["read_retries"] = int(self.counters["read_retries"]) + 1
                try:
                    self.transport.reset_input_buffer()
                except TransportError:
                    pass
                self._backoff(attempt)
            except IndeterminateCommandOutcome:
                raise
            except TransportError as exc:
                self.counters["failures"] = int(self.counters["failures"]) + 1
                if tx.state in {CommandOutcome.WRITING, CommandOutcome.WRITE_COMPLETE, CommandOutcome.READING}:
                    if tx.state == CommandOutcome.WRITING:
                        tx.transition(CommandOutcome.OUTCOME_INDETERMINATE)
                    elif tx.state in {CommandOutcome.WRITE_COMPLETE, CommandOutcome.READING}:
                        tx.transition(CommandOutcome.OUTCOME_INDETERMINATE)
                    self.counters["indeterminate"] = int(self.counters["indeterminate"]) + 1
                    event_id = self._audit(operation, RiskClass.READ_ONLY, tx.state, "Transport failed after query dispatch")
                    raise IndeterminateCommandOutcome(
                        f"Outcome of query {operation!r} is indeterminate",
                        context={"audit_event_id": event_id},
                    ) from exc
                raise
            except Exception:
                self.counters["failures"] = int(self.counters["failures"]) + 1
                if tx.state == CommandOutcome.RESPONSE_VALIDATED:
                    tx.transition(CommandOutcome.PROTOCOL_FAILURE)
                self._audit(operation, RiskClass.READ_ONLY, CommandOutcome.PROTOCOL_FAILURE, "Query validation failed")
                raise
        assert last_error is not None
        raise last_error

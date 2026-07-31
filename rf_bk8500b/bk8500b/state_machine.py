"""Centralized session and transaction state-transition enforcement."""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock

from .enums import CommandOutcome, SessionState
from .exceptions import InvalidStateTransitionError


_SESSION_TRANSITIONS: dict[SessionState, frozenset[SessionState]] = {
    SessionState.DISCONNECTED: frozenset({SessionState.CONNECTING}),
    SessionState.CONNECTING: frozenset({SessionState.IDENTIFYING, SessionState.FAILED, SessionState.CLOSING}),
    SessionState.IDENTIFYING: frozenset({SessionState.CONNECTED_UNSYNCHRONIZED, SessionState.FAILED, SessionState.CLOSING}),
    SessionState.CONNECTED_UNSYNCHRONIZED: frozenset({SessionState.CONNECTED_READY, SessionState.DEGRADED, SessionState.FAILED, SessionState.CLOSING}),
    SessionState.CONNECTED_READY: frozenset({SessionState.DEGRADED, SessionState.RECONNECTING, SessionState.FAILED, SessionState.CLOSING}),
    SessionState.DEGRADED: frozenset({SessionState.RECONNECTING, SessionState.CONNECTED_READY, SessionState.FAILED, SessionState.CLOSING}),
    SessionState.RECONNECTING: frozenset({SessionState.CONNECTED_UNSYNCHRONIZED, SessionState.FAILED, SessionState.CLOSING}),
    SessionState.CLOSING: frozenset({SessionState.DISCONNECTED, SessionState.FAILED}),
    SessionState.FAILED: frozenset({SessionState.CLOSING}),
}


@dataclass(slots=True)
class SessionStateMachine:
    _state: SessionState = SessionState.DISCONNECTED
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)

    @property
    def state(self) -> SessionState:
        with self._lock:
            return self._state

    def transition(self, new_state: SessionState) -> None:
        with self._lock:
            if new_state == self._state:
                return
            if new_state not in _SESSION_TRANSITIONS[self._state]:
                raise InvalidStateTransitionError(
                    f"Invalid session transition {self._state.value} -> {new_state.value}",
                    context={"from": self._state.value, "to": new_state.value},
                )
            self._state = new_state

    def fail(self) -> None:
        with self._lock:
            if self._state == SessionState.FAILED:
                return
            if self._state == SessionState.DISCONNECTED:
                raise InvalidStateTransitionError("Cannot fail a disconnected session")
            self._state = SessionState.FAILED


_TRANSACTION_TRANSITIONS: dict[CommandOutcome, frozenset[CommandOutcome]] = {
    CommandOutcome.CREATED: frozenset({CommandOutcome.VALIDATED, CommandOutcome.CANCELLED_NOT_SENT, CommandOutcome.FAILED_NOT_SENT}),
    CommandOutcome.VALIDATED: frozenset({CommandOutcome.WAITING_FOR_LOCK, CommandOutcome.CANCELLED_NOT_SENT, CommandOutcome.FAILED_NOT_SENT}),
    CommandOutcome.WAITING_FOR_LOCK: frozenset({CommandOutcome.WRITING, CommandOutcome.CANCELLED_NOT_SENT, CommandOutcome.FAILED_NOT_SENT}),
    CommandOutcome.WRITING: frozenset({CommandOutcome.WRITE_COMPLETE, CommandOutcome.FAILED_NOT_SENT, CommandOutcome.OUTCOME_INDETERMINATE}),
    CommandOutcome.WRITE_COMPLETE: frozenset({CommandOutcome.READING, CommandOutcome.COMPLETED, CommandOutcome.RETRYABLE_READ_FAILURE, CommandOutcome.OUTCOME_INDETERMINATE}),
    CommandOutcome.READING: frozenset({CommandOutcome.RESPONSE_VALIDATED, CommandOutcome.RETRYABLE_READ_FAILURE, CommandOutcome.OUTCOME_INDETERMINATE}),
    CommandOutcome.RESPONSE_VALIDATED: frozenset({CommandOutcome.COMPLETED, CommandOutcome.PROTOCOL_FAILURE, CommandOutcome.DEVICE_REJECTED}),
}
for terminal in (
    CommandOutcome.COMPLETED,
    CommandOutcome.CANCELLED_NOT_SENT,
    CommandOutcome.FAILED_NOT_SENT,
    CommandOutcome.RETRYABLE_READ_FAILURE,
    CommandOutcome.OUTCOME_INDETERMINATE,
    CommandOutcome.PROTOCOL_FAILURE,
    CommandOutcome.DEVICE_REJECTED,
):
    _TRANSACTION_TRANSITIONS[terminal] = frozenset()


@dataclass(slots=True)
class TransactionStateMachine:
    state: CommandOutcome = CommandOutcome.CREATED

    def transition(self, new_state: CommandOutcome) -> None:
        if new_state not in _TRANSACTION_TRANSITIONS[self.state]:
            raise InvalidStateTransitionError(
                f"Invalid transaction transition {self.state.value} -> {new_state.value}",
                context={"from": self.state.value, "to": new_state.value},
            )
        self.state = new_state

import pytest

from bk8500b import CommandOutcome, InvalidStateTransitionError, SessionState
from bk8500b.state_machine import SessionStateMachine, TransactionStateMachine


def test_valid_session_path() -> None:
    sm = SessionStateMachine()
    for state in (
        SessionState.CONNECTING,
        SessionState.IDENTIFYING,
        SessionState.CONNECTED_UNSYNCHRONIZED,
        SessionState.CONNECTED_READY,
        SessionState.CLOSING,
        SessionState.DISCONNECTED,
    ):
        sm.transition(state)
    assert sm.state is SessionState.DISCONNECTED


def test_invalid_session_transition() -> None:
    sm = SessionStateMachine()
    with pytest.raises(InvalidStateTransitionError):
        sm.transition(SessionState.CONNECTED_READY)


def test_transaction_complete_path() -> None:
    tx = TransactionStateMachine()
    for state in (
        CommandOutcome.VALIDATED,
        CommandOutcome.WAITING_FOR_LOCK,
        CommandOutcome.WRITING,
        CommandOutcome.WRITE_COMPLETE,
        CommandOutcome.READING,
        CommandOutcome.RESPONSE_VALIDATED,
        CommandOutcome.COMPLETED,
    ):
        tx.transition(state)
    assert tx.state is CommandOutcome.COMPLETED

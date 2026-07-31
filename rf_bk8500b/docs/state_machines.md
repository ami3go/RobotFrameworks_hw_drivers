# Runtime state machines

## Session

```text
DISCONNECTED -> CONNECTING -> IDENTIFYING -> CONNECTED_UNSYNCHRONIZED
CONNECTED_UNSYNCHRONIZED -> CONNECTED_READY | DEGRADED | FAILED | CLOSING
CONNECTED_READY -> DEGRADED | RECONNECTING | FAILED | CLOSING
DEGRADED -> CONNECTED_READY | RECONNECTING | FAILED | CLOSING
RECONNECTING -> CONNECTED_UNSYNCHRONIZED | FAILED | CLOSING
FAILED -> CLOSING -> DISCONNECTED
```

Control operations require `CONNECTED_READY`. Raw access, reset, recall, local front-panel handoff, and uncertain outcomes invalidate synchronized state.

## Transaction

```text
CREATED -> VALIDATED -> WAITING_FOR_LOCK -> WRITING -> WRITE_COMPLETE
WRITE_COMPLETE -> READING -> RESPONSE_VALIDATED -> COMPLETED
```

Terminal failure states are `CANCELLED_NOT_SENT`, `FAILED_NOT_SENT`, `RETRYABLE_READ_FAILURE`, `OUTCOME_INDETERMINATE`, `PROTOCOL_FAILURE`, and `DEVICE_REJECTED`.

## Safe enable

```text
READ_STATE -> REQUIRE/FORCE_OFF -> VALIDATE_ALL -> APPLY_LIMITS
-> APPLY_MODE_AND_SETPOINT -> VERIFY -> CHECK_PROTECTION
-> ENABLE_INPUT -> VERIFY_ENABLED -> COMPLETE
```

Every unsupported field and range is validated before the first write. Failure after enable begins triggers one bounded best-effort input-off attempt; the exception context records whether OFF was verified.

## Reconnect

Reconnect never replays input ON, short ON, trigger, reset, recall, protection clear, OCP start, or timing start. Identity is rechecked, cached state is invalidated, and synchronization must pass before return to `CONNECTED_READY`.

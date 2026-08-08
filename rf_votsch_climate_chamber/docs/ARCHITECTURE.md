# Architecture

```text
Robot Framework
  -> canonical keyword adapter (`library.py`)
  -> suite lifecycle listener (`lifecycle.py`)
  -> named session registry (`sessions.py`)
  -> chamber semantics (`core/chamber.py`)
  -> SimServ encoder/parser (`protocol/simserv.py`)
  -> transport interface (`transports/base.py`)
  -> TCP or deterministic simulator transport
```

The layers use composition. Robot presentation, connection lifecycle, chamber
semantics, protocol syntax, and transport I/O are independently testable.
Construction and plugin discovery perform no hardware access.

The duplicate API 2 package and inheritance-based compatibility adapter were
removed in v26.07. A local lifecycle listener remains because the approved
shared `rfds-core` distribution was not supplied; this is an open pre-P1
deviation, not a hidden compatibility implementation.

## Evidence (`evidence.py`, v26.09)

An RFDS-008 live evidence run sits alongside this stack rather than inside
it: `library.py`'s `_evidenced` decorator wraps every keyword with an
operation record, and `Connect` attaches the run as one more
`TraceObserver` on that session's transport (`transports/tracing.py`) — the
same mechanism `core/chamber.py` already uses for its own in-memory
`protocol_trace`. No transport or protocol code was changed to add this;
evidence recording is purely an additional observer. See
`docs/TROUBLESHOOTING.md`'s "Evidence and diagnostics" section for how this
differs from `Get Diagnostics`/`Export Diagnostics`.

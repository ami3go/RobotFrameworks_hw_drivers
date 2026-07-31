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

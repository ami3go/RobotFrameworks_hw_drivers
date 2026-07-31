# Architecture

## Design decision

The project uses a thin Robot Framework adapter over an independent Python driver.

```text
.robot suite
   │
   │ explicit keywords, Robot time/booleans, assertions, logging
   ▼
VotschClimateChamberLibrary  [SUITE scope]
   │ owns exactly zero or one driver instance
   ▼
ClimateChamber
   │ protocol framing, parsing, validation, reconnect, readback
   ▼
TCP socket → chamber controller
```

## Responsibilities

### Driver

- Owns socket and protocol details.
- Preserves legacy Python API.
- Validates chamber-domain constraints.
- Implements reconnect, retries, readback, stabilization, and dwell.
- Uses only Python logging, not Robot APIs.
- Can defer connection with `connect_on_init=False`.

### Robot adapter

- Exposes only `@keyword` methods because `auto_keywords=False`.
- Does not connect during import or construction.
- Converts Robot time and boolean values.
- Manages suite-level connection lifecycle.
- Adds chamber-specific assertions and readable progress logs.
- Sanitizes raw byte values before returning dictionaries.

### Tests

- Unit tests validate driver and adapter behavior.
- A deterministic local TCP server tests protocol behavior without hardware.
- Robot acceptance tests exercise the real adapter against that server.
- Hardware suites are tagged and opt-in.

## Why composition

Inheritance would expose driver implementation details and tightly couple framework lifecycle to socket lifecycle. Composition keeps the public Robot API intentional and permits driver replacement by a fake during unit testing.

## Connection lifecycle

1. Robot imports the library: no network activity.
2. `Connect Climate Chamber` creates a deferred driver.
3. Adapter calls `connect()` and verifies communication with a status query.
4. Tests reuse the session within the suite.
5. Teardown calls stop and/or disconnect explicitly.

## Threading

The driver serializes socket traffic with an `RLock` and serializes high-level state-changing operations with another `RLock`. A single library instance is not intended for parallel tests that independently control one chamber. Use suite-level serialization for hardware tests.

# Logging and evidence (RFDS-008)

`rf_bk8500_load` records every public keyword call as structured evidence so a
failure can be diagnosed after the fact, without needing to reproduce it live.
This document describes the **live, always-on evidence system** added in
v26.17 (`bk8500_load/evidence.py`). It is distinct from, and complementary to,
the one-off archived conformance record already checked into
`evidence/hardware_conformance/v26.14_com12_2026-07-28/` — that directory is a
point-in-time summary generated from one completed `output.xml` after a real
hardware run of `hardware_tests/01_all_library_keywords.robot` (see its own
`README.md`); the system described here instead runs for *any* use of the
library, not only that specific suite.

## Why

"Set Load Setpoint reported success but the load never changed" is a lot
easier to debug from a structured record of exactly which 26-byte frames were
sent and received, in what order, than from console output alone. That record
is what this system produces.

## What gets recorded, and where

`BK8500Library` is `ROBOT_LIBRARY_SCOPE = "GLOBAL"` and can hold several
simultaneously open, aliased load connections. There is **one evidence run
per library instance**, not one per alias — operations against different
aliases are tagged with different `session_alias` values within that one run.
The run is created lazily on first keyword call and written to:

```text
results/session/bk8500_load/<UTC timestamp>_<run_id>/
├── run_summary.json          # authoritative: final status, error/warning counts, duration
├── run_summary.md            # human-readable derived summary
├── environment.json          # Python/Robot/driver versions, sanitized host token
├── device_identity.json      # one entry per open alias: manufacturer, serial, firmware
├── evidence_manifest.json    # one entry per artifact below, with a SHA-256 hash each
├── events/
│   ├── events.jsonl          # every lifecycle event (run start/finish, operation start/end)
│   ├── operations.jsonl      # one entry per keyword call: arguments, duration, result, status
│   └── errors.jsonl          # one entry per raised exception: category, message, traceback
├── protocol/
│   ├── exchanges.jsonl       # every 26-byte frame, machine-readable, with a hex dump
│   ├── outbound_trace.log    # the same frames, human-readable (driver -> instrument)
│   └── inbound_trace.log     # instrument -> driver
└── integrity/
    └── checksums.sha256      # sha256sum-compatible list of every artifact above
```

Override the root with the `RFDS_EVIDENCE_ROOT` environment variable (default
`results`, relative to the current working directory). The run finalizes
(writes `run_summary.json`/`evidence_manifest.json`) once every open alias has
been closed, via `Close Load Connection` or `Close All Load Connections`.

## Reading a failure

1. Open `run_summary.json` — `final_status`, `error_count`, and
   `evidence_completeness` tell you whether to keep looking.
2. Open `events/errors.jsonl` — one JSON object per exception, each with a
   `category` (`VALIDATION`, `STATE`, `HARDWARE`, `ASSERTION`, or `UNKNOWN` —
   see `bk8500_load/exceptions.py` for the underlying hierarchy this maps
   from), the exception type/message, and a full traceback.
3. Cross-reference `operation_id`/`correlation_id` from the error into
   `events/operations.jsonl` for the exact keyword call (arguments included)
   that failed, and into `protocol/exchanges.jsonl` to see exactly which
   frames that operation sent/received before failing.
4. `protocol/outbound_trace.log`/`inbound_trace.log` give a plain
   chronological read of every frame, including the decoded command byte and
   the full hex frame — useful without parsing JSON.

Every event/operation/error carries a `correlation_id`: calls made *because
of* another call (e.g. `Apply Constant Current` calling `Set Load Mode` and
`Set Load Setpoint` internally) share their parent's correlation ID.

## Frame-level protocol tracing

The B&K 8500 series speaks a fixed 26-byte binary frame protocol (see
`bk8500_load/protocol.py`). `BK8500Driver._transact` is the single choke
point every command passes through; `BK8500Library` wires an `on_frame`
callback into each driver instance that records the outbound request frame,
the inbound response frame (or the error if an attempt failed), and repeats
per retry attempt. `protocol/exchanges.jsonl`'s `frame_hex` field preserves
the raw bytes losslessly (RFDS-008 §24.1); `operation` carries the
human-readable decode from `protocol.format_frame`.

One known gap: automatic baud-rate detection (`auto_detect_baudrate=${TRUE}`)
performs its probing entirely inside `BK8500Driver.connect_serial_with_baud_detection`
before the evidence hook can be attached, so the probe attempts themselves are
not traced (only frames from the point the connection opens onward are). The
probe attempt log is still available separately via `Get Load Connection
Info`'s `baudrate_probe_attempts` field.

## Enabling/disabling it

Evidence recording is on by default. Pass `evidence_enabled=${FALSE}` when
importing the library to disable it — errors still go to the standard Python
logger (and Robot's own log) either way, only the structured run directory is
skipped:

```robotframework
Library    BK8500Library    evidence_enabled=${FALSE}
```

## Exporting a diagnostic bundle

Call the `Export Diagnostic Bundle` keyword to zip the current run —
including a freshly recomputed manifest — to a single file:

```robotframework
${path}=    Export Diagnostic Bundle
Log    Diagnostic bundle written to ${path}
```

Works whether or not any alias is currently connected, and mid-session,
before the run is finalized — useful when troubleshooting a problem that
hasn't finished happening yet.

## Simulation honesty (RFDS-008 §6.6)

`device_identity.json` records `simulated: true/false` per alias, and
`environment.json`'s `execution_mode` reflects whether the run used
`SimulatedTransport` — simulated evidence is never silently presented as
proof of real hardware behavior.

## What this system deliberately does not do

RFDS-008 describes a platform-wide evidence standard; this addition
implements the parts of it that make a concrete troubleshooting difference
for this driver, and intentionally does not implement log rotation/
backpressure policy, cryptographic signing, retention/archival automation, or
a shared cross-driver package (none exists yet in this repository — this
module is self-contained, following the same pattern first built for
`rf_phidget_relay`). RFDS-007 error codes were not available while writing
this; `category` in `errors.jsonl` is a pragmatic mapping of this driver's
own exception hierarchy, not literal RFDS-007 codes.

## Validating a run's integrity

`scripts/validate_evidence.py` (with `.sh`/`.bat`/`.ps1` wrappers) recomputes
every SHA-256 hash in a run's `evidence_manifest.json`, checks every JSONL
stream is valid JSON with a gap-free monotonic `sequence`, and confirms
`run_summary.json` exists and is internally consistent:

```console
python scripts/validate_evidence.py results/session/bk8500_load/<run>/
```

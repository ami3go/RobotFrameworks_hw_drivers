# Logging and evidence (RFDS-008)

`rf_phidget_relay` records every public keyword call as structured evidence so a
failure can be diagnosed after the fact, without needing to reproduce it live.
This document describes what gets recorded, where it goes, and how to read it.
The implementation is `rf_phidget_relay/evidence.py`.

## Why

`Get Relay State` reporting the wrong thing, `Connect Relays` timing out, a
relay pattern applying in the wrong order — these are all easier to debug from
a structured record of exactly what SDK calls were made, in what order, with
what arguments, than from console output alone. That record is what this
system produces.

## What gets recorded, and where

Each **session** (one `PhidgetRelayLibrary` instance, from its first keyword
call until `Disconnect Relays` returns) is one **run**, written to:

```text
results/session/rf_phidget_relay/<UTC timestamp>_<run_id>/
├── run_summary.json          # authoritative: final status, error/warning counts, duration
├── run_summary.md            # human-readable derived summary
├── environment.json          # Python/Robot/driver/Phidget22 versions, sanitized host token
├── device_identity.json      # manufacturer, serials, channel count — written after Connect Relays
├── evidence_manifest.json    # one entry per artifact below, with a SHA-256 hash each
├── events/
│   ├── events.jsonl          # every lifecycle event (run start/finish, operation start/end)
│   ├── operations.jsonl      # one entry per keyword call: arguments, duration, result, status
│   └── errors.jsonl          # one entry per raised exception: category, message, traceback
├── protocol/
│   ├── exchanges.jsonl       # every Phidget22 SDK call, machine-readable
│   ├── outbound_trace.log    # the same calls, human-readable (driver -> SDK)
│   └── inbound_trace.log     # SDK/device -> driver (getState reads, attach confirmations)
└── integrity/
    └── checksums.sha256      # sha256sum-compatible list of every artifact above
```

Override the root with the `RFDS_EVIDENCE_ROOT` environment variable (default
`results`, relative to the current working directory).

## Reading a failure

1. Open `run_summary.json` — `final_status`, `error_count`, and
   `evidence_completeness` tell you whether to keep looking.
2. Open `events/errors.jsonl` — one JSON object per exception, each with a
   `category` (`VALIDATION`, `STATE`, `HARDWARE`, `ENVIRONMENT`, `ASSERTION`,
   or `UNKNOWN`), the exception type/message, and a full traceback.
3. Cross-reference `operation_id`/`correlation_id` from the error into
   `events/operations.jsonl` to see the exact keyword call (arguments
   included) that failed, and into `protocol/exchanges.jsonl` to see what
   Phidget22 SDK calls that operation had already made before it failed.
4. `protocol/outbound_trace.log` gives a plain chronological read of every
   `DigitalOutput` SDK call this run made — useful for "did it even try to
   write CH5?" questions without parsing JSON.

Every event/operation/error also carries a `correlation_id`: calls made
*because of* another call (e.g. `Close Relay` calling `Set Relay State`, or
`Get All Relay States` reading all eight channels) share their parent's
correlation ID, so you can pull one workflow's full trace out of the JSONL
files with a single `grep`.

## Enabling/disabling it

Evidence recording is on by default. Pass `evidence_enabled=${FALSE}` when
importing the library to disable it — errors still go to the standard Python
logger (and Robot's own log) either way, only the structured run directory is
skipped:

```robotframework
Library    rf_phidget_relay.PhidgetRelayLibrary    evidence_enabled=${FALSE}
```

`session_alias` (default `default`) tags every record from a given library
instance — set it explicitly when a suite drives more than one
`PhidgetRelayLibrary` instance so their evidence doesn't get mixed up in
review.

## Exporting a diagnostic bundle

Call the `Export Diagnostic Bundle` keyword (or `EvidenceRun.export_diagnostic_bundle()`
directly in Python) to zip the current run — including a freshly recomputed
manifest — to a single file for attaching to a bug report:

```robotframework
${path}=    Export Diagnostic Bundle
Log    Diagnostic bundle written to ${path}
```

This works mid-session, before `Disconnect Relays` — useful when
troubleshooting something that hasn't finished failing yet.

## Simulation honesty (RFDS-008 §6.6)

`run_summary.json`'s `execution_mode` is `REAL_HARDWARE` unless the library
was constructed with an explicit `output_factory` (i.e. a test double is in
use, as `tests/test_library.py` does), in which case it's `FAKE`. Evidence
from a `FAKE` run is never silently presented as proof of real hardware
behavior.

## What this system deliberately does not do

RFDS-008 describes a platform-wide evidence standard; this driver implements
the parts of it that make a concrete troubleshooting difference for a small,
single-vendor-SDK relay driver, and intentionally does not implement:

- **A shared cross-driver package.** No such package exists yet in this
  repository (see `AI_Guides/RFDS-008...md` §35), so `evidence.py` here is
  self-contained rather than importing one. Other drivers in this repository
  that adopt the same pattern will each carry their own adapted copy — the
  general design should stay the same, the protocol-specific parts (what
  counts as an "outbound"/"inbound" operation) won't.
- **Log rotation / backpressure policy** (§34) — this driver's event volume
  per session is small enough that it isn't needed.
- **Cryptographic signing, retention/archival automation, crash-recovery
  tooling** (§30.4, §31.2, §32) — out of scope for a single driver package.
- **RFDS-007 error codes** — RFDS-007 wasn't available while writing this;
  `category` in `errors.jsonl` is a pragmatic mapping of this driver's own
  exception hierarchy (`rf_phidget_relay/exceptions.py`), not literal RFDS-007
  codes.

## Validating a run's integrity

`scripts/validate_evidence.py` (with `.sh`/`.bat`/`.ps1` wrappers) recomputes
every SHA-256 hash in a run's `evidence_manifest.json`, checks every JSONL
stream is valid JSON with a gap-free monotonic `sequence`, and confirms
`run_summary.json` exists and is internally consistent:

```console
python scripts/validate_evidence.py results/session/rf_phidget_relay/<run>/
```

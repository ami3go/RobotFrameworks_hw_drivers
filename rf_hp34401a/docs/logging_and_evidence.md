# Logging and evidence (RFDS-008)

`rf_hp34401a` records every public keyword call as structured evidence so a failure can be
diagnosed after the fact, without needing to reproduce it on the original bench. This document
describes what gets recorded, where it goes, and how it relates to the other evidence this
driver already produces. The implementation is `hp34401a_dmm/evidence.py`.

## How this relates to the driver's other evidence systems

This driver already has several evidence-producing systems, each answering a different
question:

| System | Question it answers | Scope |
|---|---|---|
| `hp34401a_dmm/logging_utils.py` (`CsvMeasurementLog`, `JsonlEventLog`) | "What did every measurement read, over an 8-hour production run?" | Long-running station logging, opt-in per script/CLI use |
| `tests/hil/verify_all_public_api_real_hardware.robot` + `RealHardwareApiCoverage.py` | "Was every public keyword exercised against real hardware, and did it pass?" | One formal RFDS-019 real-hardware conformance run |
| `tests/conformance/driver_call_protocol_conformance.robot` | "Does every keyword send the exact expected SCPI text?" | One formal RFDS-019 protocol-vector conformance run |
| **This system** (`hp34401a_dmm/evidence.py`) | "Why did *this* keyword call, in *this* Robot session, just fail?" | Every session, on by default, no formal-run setup required |

None of these replace each other. This one is the only one that runs automatically for
ordinary keyword use (examples, ad hoc scripts, a suite that isn't a formal conformance run) and
correlates a failure back to the exact arguments and SCPI traffic that produced it.

## What gets recorded, and where

Each **session** — one `Hp34401ALibrary` instance, from its first keyword call until a
disconnect-family keyword (`Disconnect`, `Close DMM`, `Disconnect DMM`, `Disconnect All`, `Close
All DMMs`) leaves zero DMM sessions open — is one **evidence run**, written to:

```text
results/session/rf_hp34401a/<UTC timestamp>_<run_id>/
├── run_summary.json          # authoritative: final status, error/warning counts, duration
├── run_summary.md            # human-readable derived summary
├── environment.json          # Python/Robot/core-driver versions, sanitized host token
├── device_identity.json      # one entry per connected DMM alias: manufacturer/model/serial/transport
├── evidence_manifest.json    # one entry per artifact below, with a SHA-256 hash each
├── events/
│   ├── events.jsonl          # every lifecycle event (run start/finish, operation start/end)
│   ├── operations.jsonl      # one entry per keyword call: arguments, duration, result, status
│   └── errors.jsonl          # one entry per raised exception: category, message, traceback
├── protocol/
│   ├── exchanges.jsonl       # every SCPI command/response, machine-readable, tagged with transport
│   ├── outbound_trace.log    # the same, human-readable (driver -> instrument)
│   └── inbound_trace.log     # instrument -> driver
└── integrity/
    └── checksums.sha256      # sha256sum-compatible list of every artifact above
```

Because this driver supports three interchangeable transports for the same SCPI command set —
VISA/GPIB, RS-232 serial, and a Prologix adapter — plus the in-process simulator, every protocol
exchange records which one carried it (`"transport": "visa_gpib" | "serial_rs232" | "simulation"`),
which is often the first thing worth checking when a command that works on one bench fails on
another. Multiple DMM aliases connected in one suite all write into the same run, distinguished
by `session_alias`.

Override the root with the `RFDS_EVIDENCE_ROOT` environment variable (default `results`).

## Reading a failure

1. Open `run_summary.json` — `final_status`, `error_count`, and `evidence_completeness` tell you
   whether to keep looking.
2. Open `events/errors.jsonl` — one JSON object per exception, each with a `category`
   (`VALIDATION`, `STATE`, `TIMEOUT`, `CONNECTION`, `PROTOCOL`, `DEVICE`, `CLEANUP`,
   `UNSUPPORTED`, or `UNKNOWN` — a pragmatic mapping of this driver's own exception hierarchy,
   not literal RFDS-007 codes), the exception type/message, and a full traceback.
3. Cross-reference `operation_id`/`correlation_id` from the error into `events/operations.jsonl`
   for the exact keyword call (arguments included) that failed, and into
   `protocol/exchanges.jsonl` for the SCPI commands/responses that operation exchanged before
   failing.
4. `protocol/outbound_trace.log` gives a plain chronological read of every SCPI command this run
   sent, across all aliases and transports, without parsing JSON.

Every event/operation/error also carries a `correlation_id`: calls made *because of* another
call share their parent's correlation ID, so one workflow's full trace can be pulled out of the
JSONL files with a single `grep`.

## Enabling/disabling it

On by default. Disable it per library instance:

```robotframework
Library    rf_hp34401a.Hp34401ALibrary    evidence_enabled=${FALSE}
```

Errors still reach Robot's own log and the standard Python logger either way — only the
structured run directory is skipped.

## Exporting a diagnostic bundle

```robotframework
${path}=    Export Diagnostic Bundle
Log    Diagnostic bundle written to ${path}    console=True
```

Zips the current run — including a freshly recomputed manifest — to a single file. Works
mid-session, before any disconnect keyword; useful when troubleshooting something that hasn't
finished failing yet. Returns `None` if `evidence_enabled=False` was passed.

## Simulation honesty (RFDS-008 §6.6)

`run_summary.json`'s `execution_mode` is always `REAL_HARDWARE` for this driver's evidence
engine today — `Open Simulated DMM` sessions are tagged `"transport": "simulation"` per-session
in `device_identity.json` and every protocol exchange from that alias, so simulated and real
traffic in a mixed multi-alias run remain distinguishable at the record level even though the
run-level `execution_mode` field isn't split per-alias.

## What this system deliberately does not do

- **A shared cross-driver package.** No such package exists yet in this repository (this
  driver's own `pyproject.toml` has an aspirational `rfds = ["rfds-core>=1.0,<2.0"]` extra for
  exactly this, but it isn't published), so `evidence.py` here is self-contained.
- **Log rotation / backpressure policy, cryptographic signing, retention/archival automation** —
  out of scope for a single driver package.
- **Literal RFDS-007 error codes** — RFDS-007 wasn't available while writing this; `category` in
  `errors.jsonl` is a pragmatic mapping of this driver's own exception hierarchy.

## Validating a run's integrity

```console
python scripts/validate_evidence.py results/session/rf_hp34401a/<run>/
```

Recomputes every SHA-256 hash in the run's `evidence_manifest.json`, checks every JSONL stream
is valid JSON with a gap-free monotonic `sequence`, and confirms `run_summary.json` exists and is
internally consistent.

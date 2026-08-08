# Logging and evidence (RFDS-008)

`rf_slcan` records every public keyword call as structured evidence so a
failure — a rejected command, a dropped frame, a timed-out ack — can be
diagnosed after the fact without needing to reproduce it live on a real CAN
bus. This document describes what gets recorded, where it goes, and how to
read it. The implementation is `slcan/evidence.py` (framework-agnostic, in
the core driver package) plus the RF adapter's use of it in
`rf_slcan/library.py`.

## Why SLCAN in particular benefits from this

Every other driver in this repository is synchronous query/response: send a
command, read exactly the line that answers it. SLCAN isn't — a background
reader thread (`slcan/reader.py`) continuously classifies incoming lines and
routes them to either the current command's ack or the unsolicited-frame
queue, because a real CAN adapter can push a received-frame notification onto
the wire at any moment, including mid-command. That timing-sensitive design
is exactly the kind of thing a plain console log doesn't reconstruct well
after the fact — a correlated, ordered protocol trace does.

## What gets recorded, and where

One Robot suite = one **run**, written to:

```text
results/session/rf_slcan/<UTC timestamp>_<run_id>/
├── run_summary.json          # authoritative: final status, error/warning counts, duration,
│                              # execution_mode (REAL_HARDWARE / SIMULATOR / MIXED)
├── run_summary.md            # human-readable derived summary
├── environment.json          # Python/Robot/driver/pyserial versions, sanitized host token
├── device_identity.json      # adapter HW/SW version + serial number — from Get Identity
├── evidence_manifest.json    # one entry per artifact below, with a SHA-256 hash each
├── events/
│   ├── events.jsonl          # every lifecycle event (run start/finish, operation start/end)
│   ├── operations.jsonl      # one entry per keyword call: arguments, duration, result, status
│   └── errors.jsonl          # one entry per raised exception: category, message, traceback
├── protocol/
│   ├── exchanges.jsonl       # every SLCAN ASCII line, machine-readable
│   ├── outbound_trace.log    # the same lines, human-readable (driver -> adapter)
│   └── inbound_trace.log     # adapter -> driver: acks, nacks, query data, AND every
│                              # received CAN frame (t/T/r/R lines), whether solicited or not
└── integrity/
    └── checksums.sha256      # sha256sum-compatible list of every artifact above
```

Override the root with `RFDS_EVIDENCE_ROOT` (default `results`).

## Reading the protocol trace

SLCAN's wire format is already a human-readable CAN-frame representation, so
`protocol/outbound_trace.log`/`inbound_trace.log` need no further decoding:

```text
2026-08-06T10:09:19.987Z [pex-06697c2ea2] S6            # Set Bitrate 500K -> S<index 6>
2026-08-06T10:09:19.988Z [pex-a7be221652] O              # Open Channel NORMAL
2026-08-06T10:09:19.989Z [pex-13ce43f638] t1233AABBCC    # Send Frame 0x123, DLC=3, data=AABBCC
```

`t1233AABBCC` decodes directly: `t` = standard data frame, `123` = arbitration
ID (hex), `3` = DLC, `AABBCC` = data bytes. An extended-ID frame uses `T` and
an 8-hex-digit ID; a remote frame uses `r`/`R` with no data. Frames the
adapter received off the bus (not requested by any command) appear in
`inbound_trace.log` too, at the point a keyword (`Receive Frame`/`Drain
Received Frames`) actually retrieved them from the background reader's queue
— not when the reader thread itself queued them — so each trace entry stays
correlated with the operation that observed it.

## Reading a failure

1. `run_summary.json` — `final_status`, `error_count`, `execution_mode`.
2. `events/errors.jsonl` — one object per exception, with a `category`
   (`VALIDATION`, `STATE`, `TIMEOUT`, `HARDWARE`, `PROTOCOL`, `ENVIRONMENT`,
   `ASSERTION`, `UNKNOWN` — approximated from `slcan/exceptions.py`'s own
   hierarchy) plus the exception type/message/traceback.
3. Cross-reference `operation_id`/`correlation_id` into
   `events/operations.jsonl` for the exact keyword call and arguments, and
   into `protocol/exchanges.jsonl` for what was actually on the wire before
   the failure.

Every event/operation/error carries a `correlation_id`; calls made *because
of* another call share their parent's ID, so one call's full trace — e.g.
everything `Connect` did, including its `V`/`N` identity queries — is one
`grep` away.

## Multiple adapters, one run

This library can drive several SLCAN adapters at once via the `alias`
parameter. All of them share one evidence run per suite (not one per alias)
— `session_alias` on every record tells you which adapter a given event
belongs to. `execution_mode` is `MIXED` if the suite connected at least one
alias with `simulated=${TRUE}` and at least one to real hardware.

## Enabling/disabling it

On by default. Disable with:

```robotframework
Library    rf_slcan.SlcanLibrary    evidence_enabled=${FALSE}
```

Errors still reach Robot's own log and the standard Python logger either way.

## Exporting a diagnostic bundle

```robotframework
${path}=    Export Diagnostic Bundle
Log    Diagnostic bundle written to ${path}
```

Zips the current run (refreshing its manifest first) without finalizing it —
useful mid-suite, before the run's `_end_suite`-triggered finalization.

## Suite/test/keyword correlation

`SlcanLibrary` already implements Robot's dynamic self-listener protocol
(`ROBOT_LIBRARY_LISTENER = self`, pre-existing — it's how `Disconnect` gets
guaranteed even if a suite forgets it). `_start_suite`/`_end_suite`/
`_start_test`/`_end_test`/`_start_keyword`/`_end_keyword` forward the active
suite/test/keyword name into every evidence event's `source` block
automatically — no `--listener` flag needed.

## What this system deliberately does not do

Same scope decisions as `rf_phidget_relay` (see that driver's
`docs/logging_and_evidence.md` for the full reasoning): no shared
cross-driver evidence package exists yet in this repository, so this is a
self-contained module, not an imported dependency; no log
rotation/backpressure policy, cryptographic signing, or retention automation;
`category` in `errors.jsonl` approximates this driver's own exception
hierarchy rather than literal RFDS-007 codes (RFDS-007 wasn't available while
writing this).

## Validating a run's integrity

```console
python scripts/validate_evidence.py results/session/rf_slcan/<run>/
```

Recomputes every SHA-256 hash, checks every JSONL stream for valid JSON and a
gap-free monotonic `sequence`, and confirms `run_summary.json` is present and
consistent.

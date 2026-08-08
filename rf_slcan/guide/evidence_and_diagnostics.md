# Guide: diagnosing a failed SLCAN test run

A task-oriented companion to `docs/logging_and_evidence.md` (which describes
the evidence system itself).

## "A test failed against a real adapter — what happened?"

1. Get the evidence run directory (or the `Export Diagnostic Bundle` zip, if
   the failing suite's teardown calls it — see below).
2. Open `run_summary.md` first.
3. Open `events/errors.jsonl`. Find the entry whose `capability` matches the
   keyword Robot reported as failing, and note its `operation_id`.
4. Search `events/operations.jsonl` for that `operation_id` to see the exact
   arguments Robot passed.
5. Search `protocol/exchanges.jsonl` (or just read `protocol/outbound_trace.log`
   / `inbound_trace.log`, which are chronological and human-readable) around
   the same timestamp to see the actual SLCAN ASCII lines exchanged —
   `t1233AABBCC`, `S6`, a bare ack, or `BEL(nack)`.

A `SlcanDeviceError` ("adapter rejected command") shows up as `BEL(nack)` in
the inbound trace right after the rejected command in the outbound trace —
useful for telling "the adapter actively refused this" apart from "nothing
answered in time" (`SlcanTimeoutError`, traced as `(timeout: no response)`).

## "I want every future failure on this bench to leave a diagnostic bundle automatically"

```robotframework
*** Settings ***
Library         rf_slcan.SlcanLibrary
Suite Setup     Connect    resource=/dev/ttyACM0
Suite Teardown  Teardown With Diagnostics

*** Keywords ***
Teardown With Diagnostics
    Run Keyword And Ignore Error    Close Channel
    ${bundle}=    Export Diagnostic Bundle
    Log    Diagnostic bundle: ${bundle}    console=True
    Disconnect
```

## "Did this run actually touch a real adapter?"

Check `execution_mode` in `run_summary.json`/`run_summary.md`:
`REAL_HARDWARE`, `SIMULATOR` (every `Connect ... simulated=${TRUE}` call in
the suite), or `MIXED` (both occurred). RFDS-008 §6.6 calls this "simulation
honesty" — the run never silently presents simulated behavior as proof of
real adapter/bus behavior.

## "Why does `protocol/inbound_trace.log` show frames I never explicitly asked for?"

Those are unsolicited CAN frames the adapter pushed onto the wire and this
driver's background reader queued — logged at the moment `Receive Frame` or
`Drain Received Frames` actually retrieved them, not when the reader thread
first saw them. If you see fewer received-frame entries than you expected,
check `Get Receive Overflow Count` in the same test's operations — a full
receive queue drops the oldest frame rather than blocking, and that counter
is the only place that shows up.

## "I just want to turn this off"

```robotframework
Library    rf_slcan.SlcanLibrary    evidence_enabled=${FALSE}
```

## Validating that a run directory wasn't tampered with or truncated

```console
python scripts/validate_evidence.py results/session/rf_slcan/<run>/
```

Non-zero exit code and a listed finding for any hash mismatch, missing file,
or JSONL sequence gap/duplicate.

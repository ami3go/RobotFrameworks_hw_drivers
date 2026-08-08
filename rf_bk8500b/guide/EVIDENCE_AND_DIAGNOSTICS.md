# Guide: diagnosing a failed electronic-load test run

A task-oriented companion to `docs/logging_and_evidence.md` (which describes
the evidence system itself).

## "A test failed in CI/on a bench I can't access — what happened?"

1. Get the evidence run directory from whoever ran it, or the zip from
   `Export Diagnostic Bundle` if it was called (add it to suite teardown —
   see below — so it's captured automatically next time).
2. Open `run_summary.md` first for the one-paragraph version.
3. Open `events/errors.jsonl`; find the entry whose `capability` matches the
   keyword Robot reported as failing.
4. Note its `operation_id`. Search `events/operations.jsonl` for that ID for
   the exact arguments Robot passed.
5. Search `protocol/exchanges.jsonl` for the same `operation_id` for the raw
   SCPI command/response text or legacy frame bytes that keyword actually
   exchanged with the load before failing.

## "I want every future failure on this bench to leave a diagnostic bundle automatically"

```robotframework
*** Settings ***
Library         BK8500BLibrary
Suite Setup     Connect To Electronic Load    ${PORT}
Suite Teardown  Teardown With Diagnostics

*** Keywords ***
Teardown With Diagnostics
    Run Keyword And Ignore Error    Disable Input
    ${bundle}=    Export Diagnostic Bundle
    Log    Diagnostic bundle: ${bundle}    console=True
    Disconnect All Electronic Loads
```

## "Did an AuditEvent I already know about (from the existing audit_sink) show up here too?"

Yes — every `AuditEvent` the existing `CommandExecutor` produces is forwarded
into `events/events.jsonl` as an `AUDIT_<OPERATION>` event automatically, as
long as the device was built through the library's default device factory
(true for `Connect To Electronic Load` unless a test/caller overrides
`library._device_factory`). You do not need to wire your own `AuditSink` to
get this — it's already connected.

## "I just want to turn this off"

```robotframework
Library    BK8500BLibrary    evidence_enabled=${FALSE}
```

Exceptions still reach Robot's own log and the standard Python logger — you
lose the structured record, not the error itself.

## Validating that a run directory wasn't tampered with or truncated

```console
python scripts/validate_evidence.py results/session/rf_bk8500b/<run>/
```

Reports any hash mismatch, missing file, or JSONL stream with a sequence gap
or duplicate. Non-zero exit on any finding.

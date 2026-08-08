# Guide: diagnosing a failed relay test run

A short, task-oriented companion to `docs/logging_and_evidence.md` (which
describes the evidence system itself). This guide walks through the two
situations that actually come up on a bench.

## "A test failed in CI/on a bench I can't access — what happened?"

1. Ask whoever ran it for the evidence run directory, or for the zip from
   `Export Diagnostic Bundle` if they called it (or add the keyword call to
   the failing suite's teardown so it's captured automatically next time —
   see below).
2. Open `run_summary.md` first — it's the one-paragraph version.
3. Open `events/errors.jsonl`. Each line is one exception; find the one whose
   `capability` matches the keyword Robot reported as failing.
4. Note its `operation_id`. Search `events/operations.jsonl` for that ID to
   see the exact arguments Robot passed in.
5. Search `protocol/exchanges.jsonl` for the same `operation_id` to see
   exactly which `DigitalOutput` SDK calls that keyword made before failing —
   this tells you whether the failure was in argument validation (no SDK
   calls logged) or partway through a multi-channel write (some but not all
   channels logged).

## "I want every future failure on this bench to leave a diagnostic bundle automatically"

Add `Export Diagnostic Bundle` to suite teardown, guarded so it always runs
even after a failure:

```robotframework
*** Settings ***
Library         rf_phidget_relay.PhidgetRelayLibrary
Suite Setup     Connect Relays    ${DEVICE_A_SERIAL}    ${DEVICE_B_SERIAL}
Suite Teardown  Teardown With Diagnostics

*** Keywords ***
Teardown With Diagnostics
    Run Keyword And Ignore Error    Emergency Open All Relays
    ${bundle}=    Export Diagnostic Bundle
    Log    Diagnostic bundle: ${bundle}    console=True
    Disconnect Relays
```

The bundle path is logged to the console and to Robot's own `log.html`, so
whoever triages the run doesn't need shell access to the machine that ran it
— just the zip.

## "Did this run actually touch real hardware?"

Check `execution_mode` in `run_summary.json` (also shown in
`run_summary.md`): `REAL_HARDWARE` or `FAKE`. A `FAKE` run means the suite (or
someone's exploratory script) constructed `PhidgetRelayLibrary` with a custom
`output_factory`, i.e. no physical board was involved — see RFDS-008 §6.6
("simulation honesty") for why this distinction is recorded explicitly rather
than left to be inferred.

## "I just want to turn this off"

```robotframework
Library    rf_phidget_relay.PhidgetRelayLibrary    evidence_enabled=${FALSE}
```

Nothing gets written to `results/`. Exceptions still reach Robot's own log
and the standard Python logger — you lose the structured record, not the
error itself.

## Validating that a run directory wasn't tampered with or truncated

```console
python scripts/validate_evidence.py results/session/rf_phidget_relay/<run>/
```

Reports any hash mismatch, missing file, or JSONL stream with a gap or
duplicate in its `sequence` numbers. Exit code is non-zero on any finding.

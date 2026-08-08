# Release notes — release 17 (`rf_bk8500_load_v26.17`)

Package: `rf_bk8500_load_v26.17.zip`, unpacking to `rf_bk8500_load/`.  
Python distribution: **`bk8500-load==26.17.0`**.  
Lifecycle: Phase 1, Gate 5 maintenance revision 12.

## Main change: live RFDS-008 evidence engine

Every public keyword call is now recorded — arguments, duration,
result/failure — together with a frame-level trace of every 26-byte
command/response exchanged with the load, to a timestamped,
SHA-256-hashed run directory:

```robotframework
Open Load Connection    port=COM12    baudrate=9600
Set Current    2.5
${bundle}=    Export Diagnostic Bundle
```

This is distinct from, and complements, the archived one-off conformance
record already checked into
`evidence/hardware_conformance/v26.14_com12_2026-07-28/`: that directory is a
point-in-time snapshot of one completed Robot suite run, while the new engine
is live and always-on for any use of the library, not just a formal
conformance run. See [Logging and evidence](logging_and_evidence.md).

## New keyword

`Export Diagnostic Bundle` zips the current session's evidence run —
including a freshly recomputed integrity manifest — to a single file for
attaching to a bug report. Public keyword count is now 62.

## Backward compatibility

Evidence recording is on by default and adds no required arguments to any
existing keyword; pass `evidence_enabled=${FALSE}` when importing the
library to disable it. Errors still reach the standard Python logger and
Robot's own log either way.

## Verification

`python scripts/validate_evidence.py <run directory>` recomputes every
SHA-256 hash in a run's manifest and checks every JSONL stream for a
gap-free monotonic sequence — this caught a real finalization-ordering bug
during development (an outer keyword's own operation record could be
excluded from the manifest if its own body finalized evidence too early;
fixed with call-depth tracking).

The release passes the full existing pytest suite plus new evidence-engine
tests, and the existing `hardware_tests/01_all_library_keywords.robot`
real-hardware conformance suite gains one new test case
(`Export Diagnostic Bundle`) without modification to the other 61.

# Release v26.15 — physical evidence and documentation closure

## Input evidence

A Robot Framework hardware report generated on 28 July 2026 for driver
`26.14.0` recorded 56/56 PASS on B&K Precision 8500 serial `1687710135`,
firmware `1.84`, through COM12 at 9600 baud.

## Confirmed

- 55/55 public keyword tests passed.
- `WF-001 Save Reconfigure And Recall List` passed.
- Source and installed versions matched.
- Non-empty identity and rated limits were returned.
- Echo-aware serial communication completed.
- Safe suite teardown passed.
- Two failure-level log entries were expected negative-path assertions.

## Changes

- Preserve the original Robot report in `evidence/`.
- Generate coverage, environment, identity, expected-negative-message, and
  integrity files.
- Update every current package document and GitHub Pages page.
- Update AI contract to revision 11.
- Align package metadata to `26.15.0`.
- Keep all functional core files and all 55 keyword signatures unchanged.
- Pass 103 package tests and build/install the `26.15.0` wheel.

## Scope

Physical keyword callability is closed. Full RFDS-019 protocol-observation
closure remains open because this report has no per-keyword raw TX/RX trace
or injected protocol-fault/recovery vectors.

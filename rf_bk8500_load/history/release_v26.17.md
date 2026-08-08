# Release v26.17 — RFDS-008 live evidence engine

## Summary

Added a live, always-on RFDS-008 evidence and diagnostics engine, distinct
from (and complementary to) the archived one-off conformance record already
checked into `evidence/hardware_conformance/v26.14_com12_2026-07-28/`. Every
public keyword call is now recorded — arguments, duration, result/failure —
together with a frame-level trace of every 26-byte command/response exchanged
with the load, to a timestamped, SHA-256-hashed run directory.

## Code changes

- Added `bk8500_load/evidence.py`: `EvidenceRun`, `NullEvidenceRun`,
  `EvidenceListener`, JSON Lines event/operation/error streams, a SHA-256
  evidence manifest, redaction of credential-shaped arguments, and
  correlation IDs linking nested keyword calls (e.g. `Close All Load
  Connections` calling `Close Load Connection`).
- Added an optional `on_frame` trace hook to `BK8500Driver` (`driver.py`),
  fired from the single `_transact` choke point every command passes
  through — one call per attempt, including retries.
- Wrapped every public keyword in `BK8500Library` with evidence recording via
  a post-hoc class-level wrapper (`_wrap_public_keywords_with_evidence`)
  rather than annotating each of the 62 keyword methods individually.
- One evidence run per library instance (not per alias), since
  `BK8500Library` is `ROBOT_LIBRARY_SCOPE = "GLOBAL"` and supports several
  simultaneously open aliased connections; operations are tagged with the
  alias they acted on. The run finalizes once every alias is closed.
- Added the `Export Diagnostic Bundle` keyword (public keyword count is now
  62) to zip a run's evidence directory for troubleshooting.
- Fixed a real ordering bug found by the new test suite during development:
  finalizing evidence from inside a keyword's own body could run before an
  *outer* caller's own operation-completion record was written (e.g. calling
  `Close All Load Connections` left its own completion record out of the
  finalized manifest). Fixed with call-depth tracking so finalization runs
  only once, after the outermost wrapped keyword call for a given Robot
  invocation returns.

## Tests

Added `tests/evidence/test_evidence.py` (manifest hash integrity, JSONL
sequence gap-freeness, protocol frame trace correctness, correlation ID
propagation across nested keyword calls, redaction, multi-alias tagging,
`Export Diagnostic Bundle`, and `validate_evidence.py` clean/tampered
detection) and `tests/conftest.py`. Extended `tests/test_all_keyword_execution.py`
to exercise `Export Diagnostic Bundle`. Regenerated the RFDS-017 contract
lock after adding the new keyword (revision 13).

## Documentation

Added `docs/logging_and_evidence.md` and `guide/logging_and_evidence.md`
(reference and task-oriented troubleshooting guide), `schemas/evidence/*.schema.json`,
and `scripts/validate_evidence.{py,sh,bat,ps1}`. Updated `README.md` and
`hardware_tests/README.md` for the new keyword and current expected result
(62 passed, 0 failed). Added `KW-061 Export Diagnostic Bundle` to
`hardware_tests/01_all_library_keywords.robot` and an `OperatingSystem`
library import it needed.

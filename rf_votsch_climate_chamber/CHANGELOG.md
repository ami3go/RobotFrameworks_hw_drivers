# Changelog

## Unreleased

- Fixed `run_summary.json`/`run_summary.md` always reporting `final_status: "PASS"` even when the run recorded an operation failure (e.g. `Get Dryer`/`Set Dryer` raising `DriverUnsupportedOperationError` because no `dryer_output_channel` was configured). `_finalize_evidence` (`library.py`) now derives the finalized status from the evidence run's own `has_errors` (new `EvidenceRun` property, `evidence.py`), so any recorded error surfaces as `final_status: "FAIL"` instead of being silently swallowed at suite end.
- Fixed `Set Dryer`/`Set Compressed Air` verifying their write with a single instantaneous readback, producing false `RFDS-SAF-001` failures on real hardware. `_set_digital_output` now polls the readback until it matches, bounded by `state_change_timeout_s` — the same delayed-readback tolerance `_wait_for_setpoint_readback` and `_wait_for_state` already applied to setpoints and start/stop. The timeout error now also carries `reported`, `verification_attempts`, and `elapsed_s`.
- Fixed the `SIM::` simulator (and `tests/support/fake_chamber.py`) hardcoding auxiliary digital outputs to channels 7 and 8: a write to any other channel was acknowledged but silently discarded, and the readback then reported `0` forever, so a simulator round trip failed for wiring the documentation explicitly permits. Both now model whichever channel the caller configured.
- Added validation rejecting a configuration that maps `dryer_output_channel` and `compressed_air_output_channel` to the same channel — one physical output cannot drive two loads, the two features would silently alias, and `Safe Shutdown` would report switching both off after touching only one.
- Fixed `tests/hardware/verify_all_api.robot` test 03 asserting `Should Be True    Is Connected` / `Check Communication`, which evaluates the literal keyword name as a Python expression (`SyntaxError: invalid syntax`) instead of calling the keyword; the results are now assigned first.
- Fixed `tests/hardware/verify_all_api.robot` test 04 reading `${exported}[path]` from `Export Driver Configuration`, which returns the written path under `destination`.
- Fixed `tests/hardware/verify_all_api.robot`'s `Restore Original Chamber State And Disconnect` suite teardown crashing with an unrelated `Invalid IF condition: ... '${ORIGINAL_RUNNING}' not found` error whenever `Connect And Capture Original Chamber State` (suite setup) failed before reaching its `Set Suite Variable` calls — e.g. `ALLOW_AUXILIARY_OUTPUTS=True` with no `DRYER_OUTPUT_CHANNEL` configured. Teardown now reads each `ORIGINAL_*` value defensively via `Get Variable Value` and skips restoring only what was never captured, so the original setup failure is reported instead of being masked, and the unconditional `Disconnect` still runs.

## v26.09 — 2026-08-07

- Added an RFDS-008 live evidence engine (`rf_votsch_climate_chamber/evidence.py`): every public keyword call is recorded as a correlated operation (arguments, duration, result/failure), and `Connect` attaches the run as an additional `TraceObserver` on that session's transport, capturing every SimServ protocol frame — no transport or protocol code changed to add this.
- Added `Export Diagnostic Bundle` keyword, distinct from the pre-existing `Export Diagnostics` snapshot: zips the whole append-only evidence run (events, protocol trace, device identity, SHA-256 manifest) for troubleshooting.
- Added `schemas/evidence/*.schema.json`, `scripts/validate_evidence.{py,sh,bat,ps1}`, and `tests/evidence/` covering manifest integrity, JSONL sequencing, redaction, and this driver's own exception-category mapping.
- Documented the evidence system in `docs/TROUBLESHOOTING.md` ("Evidence and diagnostics") and `docs/ARCHITECTURE.md`.
- Regenerated `api/public_api.yaml`, `ai/votsch_climate_chamber_ai_contract.yaml`/`.lock`, `generated/api_manifest/public_api.json`, `tests/conformance/data/keyword_inventory.yaml`, and `docs/keywords.md` via `scripts/generate_rfds_metadata.py` for the new keyword (57 → 58 canonical keywords).
- Fixed a stray case-mismatched duplicate: `docs/KEYWORDS.md` (tracked, uppercase) vs `docs/keywords.md` (what `mkdocs.yml`'s nav and the generator actually target) — removed the stale uppercase copy. `docs/ARCHITECTURE.md`, `docs/EXAMPLES.md`, and `docs/SAFETY.md` have the same nav-vs-filename case mismatch on case-sensitive filesystems and were left as pre-existing, unrelated issues.

## v26.08 — 2026-07-31

- Added bounded polling for delayed setpoint readback.
- Fixed effective-configuration round-trip and close-only disconnect policy.
- Made auxiliary output mappings explicit and disabled by default on real hardware.
- Made safe shutdown capability-aware while preserving mandatory chamber stop.
- Added real-hardware regression tests and updated smoke/API suites.


## v26.07 — 2026-07-31

- Removed all API 2 Robot keyword aliases and the duplicate legacy Python package.
- Reduced the runtime surface from 92 to 57 canonical keywords.
- Removed obsolete wrappers, dead helpers, compatibility suites, duplicate scripts, and generated caches.
- Migrated active Robot suites to named canonical `Connect` arguments.
- Regenerated RFDS-017/RFDS-019 metadata and added file-by-file cleanup evidence.
- Incremented public API version to 3.0.0.

## v26.06 — 2026-07-31

- Fixed RFDS-019 inventory execution ordering and cascading disconnected-session failures.
- Added deterministic per-keyword session, simulator-state, and configuration-profile preconditions.
- Added lifecycle recovery after disconnect, reconnect, cancellation, and legacy connection keywords.
- Added transport-boundary outbound/inbound evidence and ordered protocol-vector matching.
- Added a 92-keyword Robot-dispatch-equivalent regression test.
- Added approved `SIM::` support to the deprecated `Connect Climate Chamber` adapter.
- Corrected safe-shutdown and disconnect protocol vectors.

## v26.05 — 2026-07-31

- Fixed the hardware smoke suite by importing Robot Framework's `Collections` library before calling `Log Dictionary`.
- Updated active Robot acceptance and hardware suites to use the canonical `rf_votsch_climate_chamber.library` import path.
- Added static regression tests that reject missing `Collections` imports and legacy imports in active verification suites.
- No public driver keyword, protocol, configuration, or safety behavior changed.

## v26.04 — 2026-07-30

- Adopted RFDS-002 v1.1 canonical lifecycle and temperature keywords.
- Retained 35 v26.03 keyword names as deprecated compatibility aliases.
- Added named sessions and deterministic active-session selection.
- Added RFDS-004-style TCP, simulator, trace, and protocol boundaries.
- Added RFDS-007 canonical error hierarchy and structured diagnostics.
- Added RFDS-014 configuration schema, validation, import/export, and profiles.
- Added RFDS-015 plugin provider, manifest, and entry point.
- Regenerated RFDS-017 contract and RFDS-019 inventory/protocol vectors.
- Added 13 canonical Robot examples and source-standard package artifacts.
- Classified release D0 / D1 candidate pending Robot-runtime and hardware evidence.

Earlier history is retained in `history/`.

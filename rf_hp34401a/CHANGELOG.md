# Changelog

## 26.07 — 2026-08-08

- Added an RFDS-008 structured evidence engine (`hp34401a_dmm/evidence.py`): every public keyword call is now recorded with correlated arguments, duration, result/failure, and the literal SCPI commands/responses it caused on whichever of the three transports (VISA, RS-232, Prologix) or the simulator carried it, tagged per DMM alias, finalized into a SHA-256-hashed manifest under `results/session/rf_hp34401a/`.
- Added the `Export Diagnostic Bundle` keyword (109th public keyword) to zip the current evidence run for troubleshooting; regenerated the RFDS-002/RFDS-017 AI contract, RFDS-019 keyword inventory/protocol vectors, and HIL coverage state to include it.
- Added `docs/logging_and_evidence.md` and `guide/evidence_and_diagnostics.md` explaining how this relates to the existing `logging_utils.py` production logs and the `tests/hil/`/`tests/conformance/` conformance suites.
- Added `schemas/evidence/*.schema.json` and `scripts/validate_evidence.{py,sh,bat,ps1}` (recomputes evidence-manifest hashes and JSONL sequence integrity).
- Added `tests/evidence/test_evidence.py`.
- Does not change SCPI behavior, measurement logic, or any existing public keyword's signature or return value.

## 26.06 — 2026-07-31

- Fixed RFDS real-hardware all-API bookkeeping so executed public keywords are captured by an explicit file-backed Robot listener.
- Registered disabled fixture profiles as EXCLUDED during suite setup, before test execution.
- Changed disabled profile test cases to terminate as successful profile declarations after exclusions are recorded.
- Split coverage report generation from acceptance assertion so the summary is always logged before a teardown failure.
- Added regression validation for the listener, shared state file, launchers, and 108-keyword inventory.

## 26.05 — 2026-07-31

- Fixed lowercase command-line Boolean handling in the all-public-API real-hardware Robot suite.
- Added fail-closed normalization for `true/false`, `yes/no`, `on/off`, and `1/0`.
- Normalized every HIL profile flag before Robot `IF` expressions and Boolean assertions.
- Updated PowerShell and Linux HIL runners to emit canonical `True`/`False`.
- Prevented suite teardown from reporting all 108 APIs as `NOT RUN` when preflight fails before coverage starts.
- Preserved the complete 108-keyword public API without signature changes.

## 26.04 — 2026-07-30

- Added RFDS-002 v1.1 canonical lifecycle and conditional keyword groups.
- Added RFDS-013 capability discovery, RFDS-014 JSON configuration, and RFDS-015 plugin metadata.
- Added structured RFDS-007 errors and explicit raw-I/O authorization.
- Expanded synchronized API/AI/conformance artifacts to 108 public keywords.
- Added all-public-API real-hardware Robot verification with explicit safety profiles and evidence.
- Preserved all v26.03 compatibility keywords and matrix-orchestration methods.

## 26.03 — 2026-07-24

- Added RFDS-019 v1.1 public-call and protocol-conformance structure.
- Added complete 69-keyword inventory and one primary vector per exported keyword.
- Added exact SCPI/transport oracles for 50 device-facing keywords and raw inbound-response capture.
- Added timeout, malformed-response, SCPI-error, calibration-blocking, and recovery vectors.
- Added timestamped Robot runners and machine-readable conformance evidence generation.
- Added conformance documentation, lifecycle gate reviews, tests, traceability, and release-candidate status.
- Preserved the 69-keyword public Robot interface and RFDS-017 interface hash.

## 26.02 — 2026-07-21

- Added the transport-neutral `Connect DMM` and `Disconnect DMM` project-standard keywords while preserving every v26.01 public keyword.
- Added `Get Driver Metadata` and `Get Driver Capabilities` for runtime discovery and multi-driver planning.
- Integrated non-keyword Python compatibility methods used by legacy orchestration libraries, including `connect_to_dmm`, `disconnect`, and `close_connection`.
- Replaced the variadic strict stable-resistance signature with an explicit Robot signature.
- Added the canonical RFDS-017 v3.0 `ai/ai_contract.yaml` covering all public keywords exactly once.
- Added `ai/ai_contract.lock`, a SHA-256 lock over the normalized public keyword surface.
- Added contract validation and CI enforcement for signatures, states, error references, enums, verification oracles, and lock staleness.
- Added an RFDS-018 `system_ai_contract.yaml` bench template with conservative `UNKNOWN` values for site-specific topology and limits.
- Added AI-contract and bench-integration documentation, tests, release records, and traceability.
- Updated versioning, Libdoc, MkDocs, packaging, and release scripts for v26.02.

## 26.01 — 2026-07-18

- Added explicit SUITE-scoped Robot Framework library.
- Added named VISA, serial, and deterministic simulated sessions.
- Added all principal 34401A measurement modes and BUS-trigger support.
- Added strict overload and invalid-reading rejection.
- Added stable-resistance strict and non-strict keywords.
- Added metadata dictionaries, assertions, health, recovery, terminal, and error keywords.
- Added 12 examples, scripts, guides, tests, Libdoc generation, CI, and GitHub Pages sources.
- Incorporated reviewed core driver version 1.2.8 without duplicating SCPI logic.

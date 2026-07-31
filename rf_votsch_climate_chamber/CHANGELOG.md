# Changelog

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

# Changelog

## v26.02 — 2026-07-21

- Added RFDS-017 v3.0 `ai/ai_contract.yaml` and staleness lock.
- Documented all 36 public Robot keywords with exact signatures and machine-readable semantics.
- Added RFDS-018 v1.0 `system_ai_contract.yaml` standalone bench template.
- Added contract validation, CI enforcement, documentation, history and review.
- Preserved the full v26.01 Robot keyword API.

### Project package format

- Renamed the release archive to `rf_votsch_climate_chamber_v26.01.zip`.
- Fixed the archive root as `rf_votsch_climate_chamber/`.
- Added mandatory `history/`, `review/`, and `guide/` folders.
- Added cross-platform example runners, project-layout validation, and repeatable release ZIP generation.
- Added MkDocs-based GitHub Pages source and deployment automation.

## v26.01 — 2026-07-14

### Added

- Suite-scoped Robot Framework adapter with explicit keyword exposure.
- Deferred driver connection and real communication verification.
- Persistent TCP receive buffer and transport configuration validation.
- Callback-driven stabilization and dwell operations.
- Connection, status, temperature, gradient, output, wait, and assertion keywords.
- Fake TCP chamber, unit tests, Robot acceptance tests, and hardware smoke suite.
- Thirteen Robot Framework examples.
- Full Markdown documentation, scripts, packaging, and CI.

### Compatibility

The existing Python driver constructor and legacy public API remain available. New adapter code uses `connect_on_init=False`.

# RFDS Project Requirements — v26.08

- Release archive: `rf_votsch_climate_chamber_v26.08.zip`
- Fixed archive root: `rf_votsch_climate_chamber/`
- Python distribution version: `26.8`
- Public API version: `3.0.0`
- Release class: D0 / D1 candidate
- Runtime keyword policy: canonical keywords only; no deprecated aliases

The package applies RFDS-001 v1.2, RFDS-002 v1.1, RFDS-003 v2.0,
RFDS-004 v2.0, RFDS-005 v1.3, RFDS-006/007/009/010/012/014/015,
RFDS-017 v3.0, RFDS-018 v1.0, RFDS-019 v1.1, and the Driver
Implementation Lifecycle v1.1.

RFDS-005 is treated as the package-layout authority, so the repository uses a
flat Python package and no `src/` directory. The accepted API-breaking cleanup
and the open shared-`rfds-core` deviation are recorded in `api/deviations.yaml`.

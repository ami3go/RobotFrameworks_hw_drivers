# Compatibility

v26.07 changes the public API major version from 2.0.0 to 3.0.0.

## Supported

- canonical import: `rf_votsch_climate_chamber.VotschClimateChamberLibrary`;
- 57 canonical Robot Framework keywords;
- Python 3.11–3.13;
- Robot Framework 7.x and 8.x as declared by package metadata;
- Windows and Linux;
- deterministic simulator and SimServ-compatible TCP protocol.

## Removed

- all 35 deprecated v26.03 Robot keyword aliases;
- Python import package `votsch_climate_chamber`;
- obsolete compatibility wrappers and legacy Robot suites.

Real chamber model and firmware compatibility remains `UNKNOWN` until D2/P1
hardware qualification. Use [`migration.md`](migration.md) to update API 2 tests.

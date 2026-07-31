# Validation Report — v26.01

Validation date: 2026-07-17

## Completed automated checks

| Check | Result |
|---|---|
| Required fixed-root project layout | PASS |
| Required `history/`, `review/`, `guide/`, `examples/`, and `scripts/` content | PASS |
| Robot example count | 13 suites |
| Python compile/import | PASS |
| Ruff static lint | PASS |
| Mypy type check | PASS |
| Python unit tests | 35 passed |
| Total branch-aware coverage | 85.76% |
| Robot adapter coverage | 96% |
| Robot acceptance tests | 6 passed |
| Robot example dry-run | 13 suites passed |
| Libdoc generation | PASS |
| MkDocs/GitHub Pages strict build | PASS |
| Wheel build | PASS |
| Source distribution build | PASS |
| Twine metadata check | PASS |
| Release ZIP root verification | PASS |
| SHA-256 checksum generation | PASS |

## Release artifacts

- `rf_votsch_climate_chamber_v26.01.zip`
- `rf_votsch_climate_chamber_v26.01_SHA256SUMS.txt`
- `docs/VotschClimateChamberLibrary.html`
- `dist/robotframework_votsch_climate_chamber-26.1-py3-none-any.whl`
- `dist/robotframework_votsch_climate_chamber-26.1.tar.gz`

## Package structure verification

The release archive has exactly one fixed top-level directory:

```text
rf_votsch_climate_chamber/
```

The version exists only in the ZIP filename. Future releases can therefore replace the current extracted project folder without creating parallel versioned directories.

## Not completed

No physical climate chamber was available in the build environment. The hardware smoke suite and safety procedure are included, but the hardware gate remains pending. Therefore v26.01 remains a production-oriented release candidate rather than a hardware-validated final release.

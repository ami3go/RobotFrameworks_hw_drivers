# Production Implementation Task — v26.01

## Objective

Deliver an installable, documented, tested Robot Framework library using a separate adapter over the supplied Vötsch climate-chamber driver. Preserve Python API compatibility and keep the extracted repository folder version-independent.

## Release identity

- Human release: `v26.01`
- PEP 440 package version: `26.1`
- ZIP: `rf_votsch_climate_chamber_v26.01.zip`
- Fixed folder inside ZIP: `rf_votsch_climate_chamber/`

## Mandatory architecture

- Driver has no Robot Framework imports.
- Adapter uses composition and `@library(scope="SUITE", auto_keywords=False)`.
- Library import and Libdoc generation perform no network operation.
- Raw commands are not exposed as MVP keywords.

## Mandatory production controls

1. Explicit connection lifecycle and real-query verification.
2. Local temperature safety limits with no silent clamping.
3. Finite wait defaults and consecutive stability samples.
4. Retry/reconnect with diagnostic counters.
5. Persistent TCP receive buffering.
6. Idempotent disconnect and safety-oriented stop/disconnect teardown.
7. Robot time/boolean conversion and clear units.
8. Rate-limited progress logging.
9. Driver exception categories preserved.
10. Opt-in hardware control tests.

## Deliverables

- Python driver and Robot adapter package.
- At least 10 complete Robot examples; target 12 or more.
- README, architecture, keyword, safety, testing, troubleshooting, review, changelog, contribution, security, and support documentation.
- Unit tests, fake TCP server, Robot acceptance tests, and hardware smoke suite.
- Windows/Linux scripts and GitHub Actions.
- Wheel, sdist, Libdoc HTML, validation report, and versioned ZIP.

## Quality gates

### Gate A — Review

No unresolved high-severity design issue; compatibility decisions recorded.

### Gate B — Core

Offline import, connect/disconnect, identification, temperature, start/stop, logging, and unit tests pass.

### Gate C — Reliability

Stabilization, dwell, gradients, outputs, assertions, simulator failures, and Robot acceptance pass.

### Gate D — Distribution

Docs, examples, CI, wheel/sdist, clean install, and Libdoc pass.

### Gate E — Hardware

Read-only and approved control smoke tests pass; original safe state is restored; logs are archived.

## Acceptance criteria

- Fixed internal folder and correct v26.01 archive name.
- No network during import.
- Only documented decorated keywords visible.
- Unsafe setpoint rejected before send.
- Simulator and Robot acceptance tests pass on Windows/Linux.
- Package builds and installs from wheel.
- At least 10 examples are present and syntactically valid.
- Markdown documentation is complete.
- No critical/high issue remains.
- Production promotion requires target-hardware evidence.

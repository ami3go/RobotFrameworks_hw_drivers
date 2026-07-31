# Release Notes — v26.01

This is the first year/release-numbered package of the Robot Framework Vötsch climate chamber library.

Highlights:

- Separate Robot adapter preserves the reusable Python driver.
- Import, test discovery, and Libdoc work without chamber access.
- Explicit suite-scoped lifecycle and safety-oriented teardown.
- Finite stabilization and dwell operations with Robot time syntax.
- Reconnect, readback verification, communication statistics, and health snapshot.
- Thirteen complete examples and a deterministic TCP simulator.
- Windows/Linux CI, package build, generated keyword reference, and clean-install verification.

Compatibility:

- Python 3.10–3.13
- Robot Framework 7.4.x
- Vötsch/SimServ-compatible TCP protocol on port 2049, subject to target-hardware validation

Project package format:

- Archive: `rf_votsch_climate_chamber_v26.01.zip`
- Fixed internal root: `rf_votsch_climate_chamber/`
- Versioned history and code review included
- PyCharm/Robot Framework setup guide included
- MkDocs GitHub Pages workflow included
- Cross-platform example and release scripts included

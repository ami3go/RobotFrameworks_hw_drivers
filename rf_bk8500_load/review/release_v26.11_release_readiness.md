# Release readiness — rf_bk8500_load_v26.11

## Release identity

- ZIP: `rf_bk8500_load_v26.11.zip`
- Internal root: `rf_bk8500_load/`
- Python distribution: `bk8500-load==26.11.0`
- Public Robot keywords: 55

## Required checks

- Complete simulator execution of all public keyword methods.
- Static one-to-one coverage between the hardware suite and public keyword
  surface.
- Hazard gates for input enable, persistent writes and SHORT function.
- RFDS contract and lock consistency.
- Flat package layout with root `bk8500_load/` and `ai/`; no `src/` directory.
- Wheel build, archive extraction and checksum verification.

## Automated evidence

- 84 pytest checks passed.
- All 55 decorated keywords executed against the simulator.
- Hardware suite contains 55 uniquely identified test cases and references all 55 keywords.
- Wheel installation reports `bk8500-load==26.11.0`.

## Hardware boundary

The package is ready for a real-device run. It is not marked hardware verified
until the user runs `hardware_tests/01_all_library_keywords.robot` on the target
instrument and retains `output.xml`, `log.html` and `report.html`.

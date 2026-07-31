# Release readiness — rf_bk8500_load_v26.14

## Identity

- ZIP: `rf_bk8500_load_v26.14.zip`
- Internal root: `rf_bk8500_load/`
- Python distribution: `bk8500-load==26.14.0`
- Public Robot keywords: 55

## Automated evidence

- 102 pytest checks pass.
- Uploaded bench packet bytes are reproduced exactly.
- Closed-port DTR/RTS sequence is regression-tested.
- Echo followed by a valid status frame is accepted.
- Echo without a device response is rejected.
- Empty product identity is rejected.
- Python compilation and wheel build pass.
- Clean wheel install reports `26.14.0`.
- Contract lock contains 55 keywords.
- Flat layout contains no `src/`.

## Remaining hardware closure

Run `hardware_tests/02_serial_echo_diagnostic.py` on the selected COM port.
The port must return `0x12/0x80` for writes and a non-empty identity. Then run
the 56-test physical suite. Release closure requires 56/56 PASS.

# Release v26.14 — serial opening and local-echo handling

## Input evidence

The uploaded `BK8500_test.py` opened COM12 by creating the serial object closed,
asserting DTR and RTS before open, reasserting them afterwards, waiting one
second, and transmitting valid 26-byte packets. The accompanying log showed
exact request copies for commands `0x20` and `0x5D`.

## Interpretation

The packet construction is correct, but a write-command response must be a
`0x12` status frame. The exact request copies are local echo and are not proof
of instrument acceptance.

## Changes

- Match the proven DTR/RTS/open/settle sequence.
- Discard exact write echoes and continue waiting for the real status frame.
- Report echo-only timeouts explicitly.
- Reject empty product-information payloads.
- Add `hardware_tests/02_serial_echo_diagnostic.py`.
- Add packet, line-sequence, echo-plus-status, echo-only and empty-identity
  regression tests.
- Update package version to `26.14.0`, contract revision to 10 and maintenance
  revision to 9.

## Compatibility

No public Robot Framework keyword name or signature changed.

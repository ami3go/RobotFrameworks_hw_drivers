# Release v26.16 — automatic baud-rate detection

## Summary

Added optional, read-only automatic detection of the BK8500 serial baud rate
without adding or removing Robot Framework keywords.

## Code changes

- Added validated candidate ordering for 4800, 9600, 19200, and 38400 baud.
- Added `BK8500Driver.connect_serial_with_baud_detection()`.
- Added `baudrate=AUTO` and optional detection arguments to
  `Open Load Connection`.
- Require two consecutive matching product identities by default.
- Close every failed serial candidate before trying the next rate.
- Restore normal transaction timeout and retries after successful probing.
- Record the selected baud and attempt history in `Get Load Connection Info`.
- Keep simulation and fixed-baud paths unchanged.

## Tests

Added tests for order/de-duplication, unsupported rates, fallback success,
inconsistent identity, all-rate failure cleanup, Robot integration, and
simulation bypass.

## Documentation

Updated README, release notes, package manifest, GitHub Pages, guides, examples,
hardware runners, AI contract revision 12, review documents, and history.

## Validation

- 114 pytest checks passed.
- Python compilation, YAML/JSON parsing and Markdown-link checks passed.
- Wheel build and clean installation report `26.16.0`.

## Compatibility

- Public Robot keyword count remains 55.
- Default `auto_detect_baudrate` is false.
- Existing numeric-baud suites retain deterministic behaviour.

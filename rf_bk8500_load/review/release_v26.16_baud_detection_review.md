# Release v26.16 automatic baud-detection review

## Review scope

Connection-layer change from explicit single-rate open to optional ordered baud
probing.

## Findings

### Safety

PASS. Detection sends only `GET_PRODUCT_INFO` (`0x6A`). It does not claim
remote control, change a setpoint, close the load input, or write EEPROM.

### False-positive resistance

PASS. Existing frame validation, checksum/address checks, local-echo handling,
and empty-identity rejection remain active. The new logic additionally requires
model and serial number and, by default, two consecutive matching identities.

### Resource cleanup

PASS. Every failed candidate closes its transport. The successful candidate is
kept open and has its normal timeout/retry policy restored.

### Compatibility

PASS. Fixed numeric baud remains the default. Simulation bypasses probing. No
public keyword was added or removed; only optional parameters were appended to
`Open Load Connection`.

### Diagnostics

PASS. Every attempt is recorded with baud, result, and error/identity details.
The complete failure exception includes all attempted rates.

## Remaining verification

A physical test should set the instrument to a non-default supported rate, call
with an incorrect preferred rate and autodetection enabled, then run the full
56-test hardware suite. This is a feature-specific confirmation, not a blocker
for simulator/unit correctness.

## Verdict

APPROVED for package release v26.16 with physical fallback confirmation marked
as pending evidence.

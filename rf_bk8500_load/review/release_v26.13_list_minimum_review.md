# Release v26.13 list-minimum correction review

## Evidence reviewed

The v26.12 physical run reported 55 passed public keyword tests and one failed
supplemental workflow. The failure occurred before recall, when command `0x3E`
was sent with a list step count of one. Model 8500 firmware 1.84 returned the
parameter-range status.

## Root cause

The test used a profile that the physical instrument does not accept. The
library allowed that profile because its lower-bound validation only rejected
an empty list. The simulator also accepted one step, so software validation did
not reproduce the device behavior.

## Correction review

1. The lower bound is enforced before partition query or list writes.
2. The exception is a local `BK8500ValidationError` with the observed hardware
   rationale.
3. The simulator returns the protocol parameter error for counts outside
   `2..partition_capacity`.
4. The persistence workflow now compares two valid profiles and can reach the
   recall and restoration oracles.
5. The public keyword surface and signatures remain unchanged.
6. RFDS-017 metadata now declares `min_length: 2`.
7. RFDS-019 v1.1 is included as a governing project specification.

## Risk assessment

Low. The change prevents an operation already rejected by the tested device.
The only compatibility impact is to callers that attempted one-step lists; they
now receive a clear local error instead of a device command error.

## Review result

Code and test design: PASS. Physical v26.13 workflow closure: pending rerun.

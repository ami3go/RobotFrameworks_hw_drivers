# Release notes 26.06

Release 26.06 is a backward-compatible HIL evidence hotfix over v26.05.

## Fixed

- The real-hardware suite now records nested public keyword execution through an explicit Robot listener registered by the packaged launchers.
- Listener results and operator-approved exclusions are stored atomically in a run-local state file.
- Disabled fixture profiles are registered as `EXCLUDED` during suite setup, before any test can terminate.
- Disabled profile test cases terminate with `Pass Execution` after their exclusions are recorded.
- Coverage report generation and acceptance assertion are separate, so the complete summary is always visible even when a zero-exclusion policy fails.
- Lowercase and uppercase command-line Boolean normalization from v26.05 remains supported.

## Compatibility

The 108-keyword public Robot API is unchanged from v26.05. SCPI behavior, measurement logic, configuration schemas, capability identifiers, and legacy E-Resistor compatibility methods are unchanged.

## Release status

D0 development candidate. The user's v26.05 run proved real VISA communication and the non-fixture API groups, but the corrected v26.06 suite must be rerun to produce authoritative per-keyword coverage evidence. Fixture-dependent APIs remain unqualified until their profiles are safely enabled.

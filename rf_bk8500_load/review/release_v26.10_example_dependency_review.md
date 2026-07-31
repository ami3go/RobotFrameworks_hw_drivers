# Example dependency review — release v26.10

## Finding

**Severity: major for usability, no driver safety impact.** The identity example
failed after successful driver import because `Log Dictionary` was unresolved.
The keyword is not built into Robot Framework's `BuiltIn` library; it belongs to
`Collections`.

## Correction assessment

Importing `Collections` once in the shared example resource is preferable to
copying the import into individual suites. It covers every resource-based
example consistently and keeps direct suite execution functional.

The validation boundary was also too narrow. Checking only
`scripts/verify_library_import.robot` proved the driver keyword surface but not
the example dependency graph. Every supported launcher now dry-runs all
examples before it accepts an environment.

## Residual risk

A physical BK8500 run has not been performed in the packaging environment. The
change affects Robot keyword resolution only and does not modify transport,
protocol, safety interlocks, or load-control behavior.

## Decision

Approved for release v26.10 after unit/package checks, static example dependency
checks, wheel build, archive verification, and AI-contract lock regeneration.

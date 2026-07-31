# Release readiness — rf_bk8500_load_v26.10

## Scope

Maintenance correction for missing Robot Framework `Collections` import in
delivered examples and insufficient example-level dry-run validation.

## Acceptance evidence

- Shared example resource imports `Collections`.
- All `Log Dictionary` usages are covered by that shared resource.
- PowerShell, shell, and batch environment checks dry-run all examples.
- Python compilation and pytest package checks pass.
- Wheel and ZIP build successfully with the required flat layout.
- AI contract lock and archive checksum are regenerated.

## Decision

Ready for v26.10 distribution. Replace the complete previous package directory
to avoid stale example resources. Real-instrument verification remains open.

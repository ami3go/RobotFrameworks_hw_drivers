# Release v26.10 change history

## Trigger

Direct execution of `01_identity_and_limits.robot` failed with:

```text
No keyword with name 'Log Dictionary' found.
```

## Root cause

`Log Dictionary` is provided by Robot Framework's standard `Collections`
library. The example suite called the keyword but neither the suite nor its
shared resource imported `Collections`. Previous release validation only
dry-ran the driver import smoke suite and did not parse every delivered example.

## Corrections

- Added `Library    Collections` to
  `examples/resources/bk8500_example.resource`.
- Extended PowerShell, shell, and batch environment validation to dry-run the
  complete `examples/` directory.
- Added package regression checks for standard-library dependencies used by
  examples.
- Updated release, AI-contract, documentation, manifest, and review metadata.

## Compatibility

The 55-keyword driver API and behavior are unchanged. This is an example and
release-validation correction only.

# Release v26.11 change history

## Requested changes

- Add a test that exercises every available Robot Framework library function on
  the connected BK8500 and verifies its response.
- Replace confusing installed versions such as `26.1.5.post4` with a release
  number aligned to the project ZIP.

## Implementation

- Added a 55-keyword real-device Robot Framework suite with individual test
  results and command/readback checks.
- Added explicit safety gates for input enable and persistent storage writes.
- Added direct and canonical PowerShell, batch and shell runners.
- Added a simulator regression that invokes every public keyword and compares
  executed coverage with the live decorated keyword surface.
- Changed the Python distribution version to `26.11.0`, matching package
  release `rf_bk8500_load_v26.11.zip`.
- Corrected the stale `pytest.ini` path from `src` to the flat package root.
- Updated the AI contract, contract lock, documentation, manifest, reviews and
  package tests.

## Compatibility

The Robot keyword names and signatures are unchanged. Existing imports remain:

```robotframework
Library    BK8500Library
```

Only the Python package version scheme changed.

# Release v26.9 change history

## Reported failure

Robot Framework parsed the example but could not find `Open Load Connection`
or `Close All Load Connections`.

## Root cause

The top-level `BK8500Library.py` file only imported and re-exported the class
from `bk8500_load.library`. In the affected runtime this was handled as a module
library, leaving no exported Robot keywords.

## Changes

1. Replaced the re-export with a locally defined `BK8500Library` subclass.
2. Preserved the implementation, signatures, keyword decorators, scope, and
   version metadata through inheritance.
3. Added `scripts/verify_library_import.robot`.
4. Updated environment selectors to run the smoke suite with `--dryrun`.
5. Added static regression tests for the public import class and missing
   setup/teardown keywords.

## Compatibility

No Robot keyword names or signatures changed. Existing imports using either
`BK8500Library` or `bk8500_load.library.BK8500Library` remain supported.

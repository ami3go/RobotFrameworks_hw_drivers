# Release v26.12 hardware-result correction review

## Input reviewed

Robot Framework output from a physical BK Precision 8500 connected on COM9.
The run identified model 8500, serial `1687710135`, firmware `1.84`, and
reported 54/55 keyword tests passed.

## Root-cause boundary

The failed test was named `Recall Load List File`, but the recall keyword was
never reached. The failure occurred in a second `Configure Load List` call at
command `0x3E` after a successful list save. Therefore the evidence supported a
persistence-settle and test-isolation correction, not a rewrite of recall.

## Changes reviewed

1. Save/recall timing barriers are centralized in the driver stabilization map.
2. List capacity is derived from command `0x4B` before list writes.
3. Input OFF is enforced before list editing.
4. `0x3E` failures include profile and partition context.
5. The recall keyword test contains only one fixture configuration.
6. A separate workflow reproduces save → reconfigure → recall.
7. Version and device evidence is written into Robot metadata and JSON.
8. The simulator persists complete list state and validates the workflow.

## Risk assessment

The update is low risk to the public API. Added delays affect only persistent
operations and total less than one second per operation. Partition validation
can reject configurations that the instrument would reject later, producing a
clearer and safer local error.

## Review result

Source and simulator review: PASS. Physical closure: pending v26.12 rerun.

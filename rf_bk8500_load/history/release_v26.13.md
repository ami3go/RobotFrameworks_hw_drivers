# Release v26.13 — observed two-step list minimum

## Triggering evidence

A physical v26.12 run on BK Precision model 8500, serial `1687710135`, firmware
`1.84`, passed all 55 public keyword tests. `Recall Load List File` passed. The
only failing test was the additional save/reconfigure/recall workflow, where a
one-step replacement list was rejected at command `0x3E` as an invalid
parameter.

## Changes

- Require at least two steps in `Configure Load List`.
- Reject shorter profiles locally before reading the partition or writing any
  list command.
- Make the simulator reject wire-level list counts below two.
- Change the workflow replacement profile from one step to two valid steps.
- Add regression tests for local no-traffic rejection and simulator behavior.
- Update version to `26.13.0`, AI contract revision to 9 and maintenance
  revision to 8.
- Add RFDS-019 v1.1 to `ai/` and wheel data.

## Compatibility

The public 55-keyword API is unchanged. The list-profile input contract is
narrowed from one-or-more steps to two-or-more steps.

## Closure criterion

Run the complete physical suite with persistent writes enabled and obtain
56/56 PASS.

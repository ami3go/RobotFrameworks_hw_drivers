# Release history — rf_bk8500_load_v26.8

External package: `rf_bk8500_load_v26.8.zip`  
Internal root: `rf_bk8500_load/`  
Driver version: `26.1.5.post3`  
Lifecycle: Phase 1, Gate 5 maintenance revision 3

## Reason for update

A hardware example launched with the package-private `.venv` failed with
`No module named robot`. A second attempt from `examples/` failed because that
folder did not contain the documented launcher.

## Changes

- Added direct wrappers to `examples/` for PowerShell, batch, and POSIX shells.
- Added environment verification before every canonical example run.
- Added automatic repair of missing Robot Framework, pyserial, and driver
  installation through the package setup scripts.
- Added clear execution messages showing the selected example, simulator mode,
  and serial port.
- Updated setup, examples, package, AI identity, and release documentation.
- Added regression tests that prevent both defects from returning.

## API impact

No Robot keyword names or signatures changed.

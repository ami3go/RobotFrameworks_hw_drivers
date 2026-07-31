# Release v26.12 — list persistence hardware correction

## Triggering evidence

The uploaded Robot Framework result from a real BK Precision 8500 on COM9
reported 54 passed and 1 failed. The failure occurred in `KW-037` before
`Recall Load List File` was called: command `0x3E` rejected a second list-step
count immediately after a successful list save.

## Changes

- Added post-save/post-recall EEPROM settle barriers.
- Added active-partition capacity validation and slot validation.
- Forced input OFF during list programming.
- Added contextual diagnostics for command `0x3E`.
- Made simulated list save/recall stateful.
- Split recall-keyword verification from the cross-keyword persistence
  regression.
- Added software/device version evidence and stale-install rejection.

## Compatibility

The 55-keyword public API and signatures are unchanged. Installed package
version is `bk8500-load==26.12.0`.

## Closure criterion

Run the complete hardware suite with persistent writes enabled and obtain
56/56 PASS: 55 keyword tests plus `WF-001`.

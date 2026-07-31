# Release readiness — rf_bk8500_load_v26.12

- ZIP: `rf_bk8500_load_v26.12.zip`
- Internal root: `rf_bk8500_load/`
- Python distribution: `bk8500-load==26.12.0`
- Public Robot keywords: 55, unchanged
- Hardware suite: 55 keyword tests + 1 workflow regression
- Automated source tests: 92 passed
- AI contract: revision 8, lock regenerated

## Ready

- Source packaging and flat layout
- List partition validation
- EEPROM settle barriers
- Stateful simulator persistence
- Version-evidence capture
- Stale-install rejection
- Safe teardown and hazardous-operation gates

## Pending

A physical v26.12 run with `AllowPersistentWrites=true`. Release closure requires
56 passed, 0 failed. Energized regulation remains a separate bench-level
verification requiring a suitable source and electrical limits.

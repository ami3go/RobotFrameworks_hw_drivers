# Release readiness — rf_bk8500_load_v26.13

- ZIP: `rf_bk8500_load_v26.13.zip`
- Internal root: `rf_bk8500_load/`
- Python distribution: `bk8500-load==26.13.0`
- Public Robot keywords: 55, unchanged
- Hardware suite: 55 keyword tests + 1 workflow regression
- AI contract: revision 9
- Automated checks: 95 passed

## Ready

- Local two-step minimum validation
- Simulator/device behavioral alignment for command `0x3E`
- Valid two-step save/reconfigure/recall workflow
- Source, package, AI and documentation version alignment
- RFDS-019 v1.1 included in the project specifications
- Safe teardown and hazardous-operation gates retained

## Pending

A physical v26.13 run with persistent writes enabled. Release closure requires
56 passed, 0 failed. Electrical regulation accuracy under an energized source
remains a separate bench-level verification.

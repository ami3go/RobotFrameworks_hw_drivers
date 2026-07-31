# Package manifest — rf_bk8500_load_v26.16

## Release identity

- ZIP: `rf_bk8500_load_v26.16.zip`
- Internal root: `rf_bk8500_load/`
- Python distribution: `bk8500-load==26.16.0`
- Lifecycle: Phase 1, Gate 5 maintenance revision 11
- AI contract revision: 12
- Public Robot keywords: 55

## Required project structure

- `bk8500_load/`
- `ai/`
- `examples/`
- `scripts/`
- `history/`
- `review/`
- `guide/`
- `docs/`
- `hardware_tests/`
- `evidence/`
- `tests/`
- `dist/`

There is no intermediate `src/` directory.

## Release change

Release v26.16 adds optional automatic detection across the supported BK8500
baud rates. `Open Load Connection` accepts `baudrate=AUTO` or
`auto_detect_baudrate=${TRUE}`. Detection is read-only and uses command `0x6A`
only. Two matching product identities are required by default.

`Get Load Connection Info` reports the selected baud and all probe attempts.
Numeric baud with autodetection disabled preserves v26.15 behaviour.

## Physical verification baseline

`evidence/hardware_conformance/v26.14_com12_2026-07-28/` contains the original
56/56 passing Robot Framework report for model 8500, serial `1687710135`,
firmware `1.84`, COM12 at 9600 baud. This validates the protocol path reused by
v26.16. Physical fallback probing at a changed front-panel baud is not claimed
by that historical report.

## Documentation updated

Root README/release notes/changelog/manifest, GitHub Pages, user/developer
guides, examples documentation, hardware-test documentation, AI README and
contract, history, reviews, and lifecycle gate report.

## Validation scope

- 114 pytest checks passed.
- All 55 Robot keyword signatures contract-locked.
- Baud probing order, fallback, failure cleanup, identity confirmation, and
  simulation bypass tested without hardware.
- Wheel build and clean installation verified.
- Physical feature confirmation remains recommended.

## Release artifact hashes

| File | SHA-256 |
|---|---|
| `bk8500_load/driver.py` | `502a37057735b6bd2ae5a367a381dae4ce1518fcba285b5d041640014c7a2f85` |
| `bk8500_load/library.py` | `b6c8f3eb57f5abd7b1c73cc13de34439694bb67a259b884510304395e36d29b1` |
| `bk8500_load/transport.py` | `9999589be360fa1f2416849784beb356335dd29ce29991e953f8a4d084df34ff` |
| `bk8500_load/protocol.py` | `a9b7e1296f8446c0bdf3d752f5a97b072fb62cfffecb1cec35d5c2dba4040087` |
| `BK8500Library.py` | `e6aa64556cf3e20941b0f87bd318bace1481af737cead05b37742eac0f0df186` |
| `dist/bk8500_load-26.16.0-py3-none-any.whl` | `780b964d7784dc505226ab47d9495c4d72f42528f5b0e47f4fe9ae984ecb6053` |

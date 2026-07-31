# Release history — rf_bk8500_load_v26.7

External package: `rf_bk8500_load_v26.7.zip`  
Internal root: `rf_bk8500_load/`  
Driver version: `26.1.5.post2`  
Lifecycle: Phase 1, Gate 5 maintenance revision 2

## Requested correction

The prior package stored the implementation under `src/bk8500_load/` and hid
its AI contract under `src/bk8500_load/ai/`. Release v26.7 implements the
required root layout:

```text
rf_bk8500_load/
├── bk8500_load/
└── ai/
```

## Changes

- Moved all Python implementation modules from `src/bk8500_load/` to
  `bk8500_load/`.
- Moved `src/BK8500Library.py` to root `BK8500Library.py`.
- Removed `src/` completely.
- Moved the RFDS-017 contract, lock, and RFDS-018 example into root `ai/`.
- Added `ai/README.md` describing the exact AI-agent consumption sequence.
- Added the governing RFDS-017, RFDS-018, and driver lifecycle specifications.
- Converted `pyproject.toml` to flat-layout package discovery.
- Added wheel data installation for AI documents under
  `share/rf_bk8500_load/ai`.
- Updated `bk8500_load.contract_path()` and `lock_path()` for source and wheel
  installations.
- Added regression tests that require `bk8500_load/` and `ai/` at root and fail
  if `src/` returns.
- Updated README, package manifest, guides, architecture, GitHub Pages, release
  notes, changelog, and review records.

## API compatibility

No Robot Framework keyword names or arguments changed. The package retains 55
contracted keywords.

## Verification limitation

Automated tests use the simulator. Physical BK8500-series hardware verification
remains open.

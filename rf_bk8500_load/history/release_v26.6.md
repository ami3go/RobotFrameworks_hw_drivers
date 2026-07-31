# Release history — rf_bk8500_load_v26.6

Date: 2026-07-23  
External package: `rf_bk8500_load_v26.6.zip`  
Internal root: `rf_bk8500_load/`  
Driver version: `26.1.5.post1`  
Lifecycle stage: Phase 1, Gate 5 maintenance revision 1

## Changes

1. Added the mandatory `history/`, `examples/`, `scripts/`, and `guide/`
   delivery areas.
2. Added twelve safe-by-default Robot Framework examples and cross-platform
   launchers.
3. Added PyCharm/Robot Framework setup, hardware connection, and
   troubleshooting guides.
4. Added a GitHub Pages entry point, Jekyll configuration, CI workflow, and
   Pages deployment workflow.
5. Added a root MIT licence file and package-structure regression tests.
6. Fixed source-only conformance testing by preserving Robot keyword metadata
   when Robot Framework is not yet installed.
7. Rejected duplicate connection aliases instead of replacing a live driver and
   leaking its transport.
8. Closed an opened transport when the initial identity query fails.
9. Updated README, release notes, changelog, AI contract, contract lock, and
   generated keyword documentation for release 6.

## Compatibility

The Robot keyword surface is unchanged. Existing suites remain compatible.
Only two previously unsafe edge cases now fail earlier and more clearly:
duplicate aliases and a failed identity read.

# Project compliance review — release v26.6

Reviewed against:

- RFDS Driver Implementation Lifecycle v1.1
- RFDS-017 AI Driver Contract Specification v3.0
- RFDS-018 AI Test Bench Contract Specification v1.0
- Project package naming and content instructions

## Findings and disposition

| ID | Severity | Finding in v26.5 | Disposition in v26.6 |
|---|---|---|---|
| PC-01 | Major | No `history/` directory | Fixed; release-indexed history added |
| PC-02 | Major | No dedicated `examples/` directory and fewer than ten user examples | Fixed; twelve examples added |
| PC-03 | Major | No scripts to run examples | Fixed; BAT, PowerShell, and shell launchers added |
| PC-04 | Major | No `guide/` with PyCharm and Robot Framework setup | Fixed |
| PC-05 | Moderate | GitHub Pages had no entry point or deployment definition | Fixed; `docs/index.md`, `_config.yml`, and workflow added |
| PC-06 | Moderate | No automated check for mandatory package structure | Fixed with `tests/test_package_structure.py` |
| PC-07 | Moderate | MIT declared but no root licence text delivered | Fixed |
| PC-08 | Major | Source-only pytest claim was false because fallback decorators exposed no Robot metadata | Fixed and regression covered |
| PC-09 | Major | Reusing an alias replaced the live driver without closing it | Fixed and regression covered |
| PC-10 | Major | Failed identity query left the transport open | Fixed and regression covered |
| PC-11 | Major, open | Real BK8500 hardware verification remains outstanding | Not hidden; release remains unverified on hardware |

## RFDS-017 assessment

The mandatory AI contract sections remain present. Every exposed Robot keyword
is represented by one capability, the lock pins the contract and keyword
surface, safety rules and verification objectives remain machine readable, and
an RFDS-018 bench fragment is supplied as an example. The keyword surface was
not changed by this maintenance update.

## Release decision

Approved for simulated/source distribution. Hardware-verified status is not
approved until the existing real-instrument validation finding is closed.

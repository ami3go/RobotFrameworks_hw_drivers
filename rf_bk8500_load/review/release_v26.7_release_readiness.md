# Release readiness — rf_bk8500_load_v26.7

## Automated evidence

| Check | Result | Evidence |
|---|---|---|
| Required root layout | Pass | `bk8500_load/` and `ai/` are direct children of `rf_bk8500_load/` |
| No intermediate source level | Pass | `src/` does not exist; enforced by `tests/test_package_structure.py` |
| AI deliverables | Pass | Seven required files present under root `ai/` |
| RFDS contract integrity | Pass | Lock regenerated for contract SHA-256 `5a661b1ae94c...` and 55 keywords |
| Python compilation | Pass | `compileall` completed for package, shim, tests, and tools |
| pytest | Pass | 72 tests passed |
| Shell launcher syntax | Pass | All `.sh` launchers passed `bash -n` |
| Markdown relative links | Pass | No unresolved relative Markdown links |
| Robot example static safety audit | Pass | 12 examples; simulation defaults and safe teardown verified |
| Wheel build | Pass | `bk8500_load-26.1.5.post2-py3-none-any.whl` |
| Wheel AI content | Pass | Seven AI files included under `share/rf_bk8500_load/ai` |
| Fresh wheel installation | Pass | Import, version, `contract_path()`, and `lock_path()` verified in a clean venv |

## Environment limitation

Robot Framework is not installed in the packaging environment, and no compatible
package was available from the configured package index. Therefore the Robot
acceptance suite and executable example suites were not run in this revision.
Their source structure, imports, simulation defaults, and teardown paths were
checked statically. The Python unit and contract-conformance suite passed.

## Hardware limitation

No physical B&K 8500-series load was available. Serial transport, DTR/RTS,
protocol replies, and electrical behavior remain hardware-verification items.

## Decision

**Ready for package release v26.7 as a layout and AI-deliverable maintenance
revision**, with the Robot-runtime and physical-hardware limitations explicitly
recorded above.

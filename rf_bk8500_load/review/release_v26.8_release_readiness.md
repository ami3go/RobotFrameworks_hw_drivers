# Release readiness — rf_bk8500_load_v26.8

## Acceptance criteria

| Check | Required result |
|---|---|
| Internal ZIP root | Exactly `rf_bk8500_load/` |
| Source layout | Root `bk8500_load/`; no `src/` |
| AI delivery | Root `ai/` complete |
| Example count | At least 10 Robot suites |
| Direct launch | `examples/run_example.ps1` present |
| Environment repair | Missing `robot` triggers setup |
| API contract | 55 keywords and valid lock |
| Python tests | Pass |
| Wheel | Builds and installs |
| Hardware | Open: real BK8500 run required |

## Release decision

Ready for package release v26.8 after automated validation. Simulator and static
checks are not a substitute for a physical BK8500-series test.

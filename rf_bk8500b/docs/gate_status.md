# Implementation gate status

| Gate | Status | Evidence/limitation |
|---|---|---|
| G0 Source normalization | Complete candidate | Source inventory, command catalogs, ambiguity register, traceability, deterministic API snapshot |
| G1 Package/transport | Complete candidate | Root package, validated configuration, serial transport, port listing, bounded deadlines, tests |
| G2 Protocol engines | Complete candidate | Strict SCPI parser/executor; 26-byte legacy codec with 100% branch coverage |
| G3 Stable core API | Complete candidate | Fake-instrument integration, API-contract, safety, and fault-injection tests |
| G4 Advanced functions | Partial | Configuration/query support implemented; OCP/timing execution and legacy list/battery/autotest remain HIL-blocked |
| G5 Resilience/observability | Complete candidate | Locking, indeterminate outcomes, reconnect, health/diagnostics, audit/metrics, async facade |
| G6 Docs/packaging | Locally verified candidate | Wheel/sdist built, installed-wheel tests passed, metadata/content verifier passed; hosted Windows/Ubuntu CI results not executed in this environment |
| G7 Hardware validation | Not executed | Requires supported physical instruments, adapters, independent measurement references, and protocol captures |
| G8 Endurance/release | Not executed | Requires 168-hour soak, 1,000 open/close cycles, leak analysis, and explicit approval |

Current software evidence: 190 passing tests, 96.56% production-package statement coverage, 90.87% branch coverage, and 100% legacy-codec branch coverage.

No production-grade 24/7 claim is permitted at this status.

# Known Risks — v26.08

| ID | Severity | Risk | Current control | Required resolution |
|---|---|---|---|---|
| KR-001 | Major | Approved shared `rfds-core` was not supplied. | Composed local lifecycle listener and typed layer interfaces. | Integrate approved core and run RFDS-003 contract tests before P1. |
| KR-002 | Major | Native Robot RFDS-019 may be unavailable in the build environment. | Full inventory, vectors, simulator harness, and repeatable runner are packaged. | Execute `python scripts/run_conformance.py` in the target Robot environment. |
| KR-003 | Major | No representative physical chamber is qualified. | Hardware control is opt-in and simulator is default. | D2/P1 HIL for each supported model/firmware. |
| KR-004 | High | Auxiliary digital-output mappings are model-specific. | Real hardware defaults to unsupported/null mapping; safe shutdown skips unqualified outputs. | Qualify and configure each output before use. |
| KR-005 | Medium | The tested chamber may update setpoint readback asynchronously or reject remote changes in some modes. | Bounded polling with strict timeout and protocol evidence. | Confirm controller mode and timing on each qualified model. |
| KR-006 | Medium | API 3.0 removed API 2 compatibility early in v26.07. | Major API increment and migration table. | Migrate downstream suites. |

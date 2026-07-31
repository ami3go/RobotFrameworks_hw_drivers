# RFDS-017 / RFDS-018 requirement traceability

| Requirement | Implementation | Verification | Status |
|---|---|---|---|
| RFDS-017 required `ai_contract.yaml` | `ai/ai_contract.yaml` | `verify_ai_contract.py`, `test_ai_contract.py` | Implemented and tested |
| RFDS-017 required lock | `ai/ai_contract.lock` | SHA-256 comparison to AST-extracted keyword surface | Implemented and tested |
| Identity and mental model | `identity`, `mental_model` | JSON Schema required fields | Implemented and tested |
| State machine | `state_machine` | State and transition reference checks | Implemented and tested |
| Resources and dependencies | `resources`, `dependencies` | JSON Schema and review | Implemented |
| One capability per public keyword | `capabilities` | Exact 74-name and signature comparison | Implemented and tested |
| Inputs, outputs, side effects, risk, timing, retry | Every capability entry | JSON Schema required fields and enums | Implemented and tested |
| Closed error catalogue | `errors` | Every `raises` reference resolves | Implemented and tested |
| Safety constraints | `safety` | Schema, review, and contract tests | Implemented; HIL pending |
| Verification objectives with oracles | `verification_objectives` | Oracle presence check | Implemented and tested |
| Setup/teardown contract | `setup_teardown` | Schema and review | Implemented; bench confirmation pending |
| Limitations and planning hints | `limitations`, `planning_hints` | Schema and review | Implemented |
| UNKNOWN handling | `unknown_handling`, `open_questions` | Schema and explicit conservative values | Implemented |
| Conformance enforcement | `conformance`, CI validator | CI and local scripts | Implemented and tested |
| RFDS-018 available drivers | `bench/system_ai_contract.yaml` | Bench-section validator | Template implemented |
| RFDS-018 physical topology | Same | Required section and explicit unknowns | Template; bench completion pending |
| RFDS-018 shared resources and signal graph | Same | Required-section validator | Template implemented |
| RFDS-018 preferred measurement sources | Same | Required-section validator | Template implemented |
| RFDS-018 requirement coverage and test templates | Same | Required-section validator | Template implemented |
| RFDS-018 constraints, scheduling, global safety | Same | Required-section validator | Template implemented; bench approval pending |

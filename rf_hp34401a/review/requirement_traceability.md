# Requirement traceability — v26.06

| Requirement | Implementation | Verification | Result/status |
|---|---|---|---|
| RFDS-001 stable release identity/class | version files; release manifest | version/structure validation | PASS, D0 |
| RFDS-001 canonical lifecycle | `library.py` | Python canonical API tests; HIL suite | Software PASS; HIL pending |
| RFDS-002 100% explicit API | decorators; `api/public_api.yaml` | API/AI validator | PASS, 108/108 |
| RFDS-002 compatibility aliases | DMM-specific keywords and Python compatibility methods | regression tests | PASS |
| RFDS-003 lifecycle semantics | sessions, finite timeout, cleanup, structured errors | unit regression | Local equivalent PASS; shared-core deviation |
| RFDS-004 transport behavior | existing core VISA/serial/fake adapters | inherited core tests, RFDS-019 vectors | Legacy transport PASS; v2 migration deferred |
| RFDS-005 required package content | package tree, examples, scripts, docs, release records | structure/archive validation | PASS for D0 candidate |
| RFDS-007 error categories | `exceptions.py`, `_execute` | exception and failure-path tests | PASS |
| RFDS-009 layered testing | core/unit/Robot/conformance/HIL trees | current Python suite; packaged Robot runners | Python PASS; current Robot/HIL pending |
| RFDS-010 review | v26.06 code and release reviews | review checklist | Conditional D0 approval |
| RFDS-012 generic GUI metadata | public API, capability/configuration models, plugin descriptor | static model validation | Implemented; GUI runtime not claimed |
| RFDS-013 capability artifacts | `capability/`, `capabilities.py` | unit tests and binding validation | PASS |
| RFDS-014 configuration artifacts | `config/`, runtime resources, `configuration.py` | schema/lock/unit/profile tests | PASS |
| RFDS-015 plugin artifacts | provider, manifest, entry point | plugin unit tests | PASS with shared-core deviation |
| RFDS-017 AI contract | `ai/ai_contract.yaml` and lock | `validate_ai_contract.py` | PASS, 108 keywords |
| RFDS-018 integration | bench template | template review | TEMPLATE; deployed bench pending |
| RFDS-019 inventory/vector coverage | conformance data and harness | static validator | PASS, 108/108 defined |
| RFDS-019 official Robot evidence | conformance runner | release-site execution | PENDING |
| All API real hardware Robot file | `verify_all_public_api_real_hardware.robot` | static full-name inventory | PASS source coverage, execution pending |
| HIL explicit enable/no fallback | HIL suite/runner | source review | PASS |
| HIL profile safety | separate `RUN_*_PROFILE` variables | source review | PASS; bench limits remain site-owned |
| At least 10 examples | 13 numbered examples and index | file/index validation | PASS |
| README/Pages/guide current | README/docs/guide/mkdocs | consistency review | PASS source; strict build pending environment |
| Release manifest/SBOM/traceability | `release/` | integrity generation | PASS source records |
| Physical qualification | real VISA/serial HIL | physical bench | PENDING; not claimed |

# Structure and AI deliverables review — release v26.7

## Scope

Review the v26.7 correction against the required package layout and the project
AI-contract instructions.

## Findings

| ID | Requirement | Result | Evidence |
|---|---|---|---|
| STR-01 | Internal ZIP root remains `rf_bk8500_load/` | Pass | ZIP structure validation |
| STR-02 | Python package is `rf_bk8500_load/bk8500_load/` | Pass | `bk8500_load/__init__.py`, implementation modules |
| STR-03 | AI folder is `rf_bk8500_load/ai/` | Pass | Root AI directory and structure test |
| STR-04 | Remove the `src/` level | Pass | No `src/` path; regression test rejects it |
| AI-01 | Machine-readable driver contract is visible | Pass | `ai/ai_contract.yaml` |
| AI-02 | Contract integrity is verifiable | Pass | `ai/ai_contract.lock` and lock test |
| AI-03 | AI agent receives usage guidance | Pass | `ai/README.md` |
| AI-04 | Multi-driver bench composition example exists | Pass | `ai/system_ai_contract.example.yaml` |
| AI-05 | Governing project specifications are included | Pass | RFDS-017, RFDS-018, lifecycle Markdown files |
| PKG-01 | Editable install works with flat layout | Pass | setuptools flat package discovery |
| PKG-02 | Wheel retains AI documents | Pass | data files under `share/rf_bk8500_load/ai` |
| API-01 | Robot keyword surface unchanged | Pass | RFDS lock remains 55 keywords |

## Code review observations

1. Flat package discovery is constrained to `bk8500_load*`; tests, examples, and
   tools cannot be accidentally installed as Python packages.
2. `contract_path()` first honors `RF_BK8500_AI_DIR`, then checks the unpacked
   root `ai/`, then the installed wheel data location.
3. The root AI contract is the canonical editable source. The wheel copy is
   generated through setuptools data files, avoiding a second maintained
   contract source.
4. Historical release documents keep their original v26.6 descriptions; current
   documentation points only to the v26.7 structure.

## Open risk

No physical instrument was available. This review confirms packaging, contract,
and simulated behavior, not electrical or firmware interoperability.

## Decision

**Approved for package release v26.7**, subject to the standing hardware
verification limitation.

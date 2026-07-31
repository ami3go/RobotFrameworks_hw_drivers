# Validation Report — v26.02

**Validation date:** 2026-07-21  
**Python:** 3.13.5  
**Robot Framework:** 7.4.2

## Results

| Validation | Result |
|---|---:|
| Project layout | PASS |
| RFDS-017 contract structure | PASS |
| Contracted public keywords | 36 / 36 |
| Exact keyword signatures | PASS |
| Contract lock and API manifest hashes | PASS |
| RFDS-018 bench sections | PASS |
| Python tests | 38 passed |
| Branch-aware coverage | 85.76% |
| Robot adapter coverage | 96% |
| Robot acceptance tests | 6 passed |
| Robot example dry-runs | 13 passed |
| Ruff | PASS |
| Mypy | PASS |
| Robot Libdoc generation | PASS |
| MkDocs strict build | PASS |
| Wheel and source distribution build | PASS |
| Twine metadata check | PASS |
| AI contracts included in wheel | PASS |
| Clean wheel installation/import | PASS |
| Library construction without network access | PASS |

## Contract-specific checks

- Every explicit `@keyword` entry appears exactly once in `ai/ai_contract.yaml`.
- Capability signatures and argument defaults match `robot_library.py`.
- Every referenced state and error is declared.
- Every coupling rule uses an approved machine prefix.
- Every verification objective includes a pass/fail oracle.
- `ai_contract.lock` matches the contract bytes, API manifest and v26.02 release.
- `system_ai_contract.yaml` contains every RFDS-018 mandatory section and references the v26.02 driver contract.

## Hardware qualification

No physical Vötsch/Weiss chamber was attached in the build environment. The following gates remain pending:

- supported model and firmware matrix;
- hardware-in-the-loop validation;
- long-duration stability and recovery tests;
- verification of dryer and compressed-air output mapping;
- site emergency shutdown and safe-access procedure validation.

The software package and AI contracts are ready for controlled hardware qualification.

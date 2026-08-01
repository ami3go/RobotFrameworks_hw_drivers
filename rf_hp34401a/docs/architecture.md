# Architecture

## Runtime layers

`Hp34401ALibrary` performs Robot argument conversion, session selection, error contextualization, metadata conversion, assertions, and unified API exposure. `SessionManager` owns isolated aliases. `hp34401a_dmm.Hp34401A` owns all instrument protocol, recovery, safety, transport, and parsing behavior.

This separation prevents two diverging SCPI implementations.

## Compatibility layer

Release 26.06 adds project-standard Robot keywords without removing or renaming v26.01 keywords. Non-decorated Python compatibility methods support orchestration code written against earlier generic DMM method names. Because `ROBOT_AUTO_KEYWORDS` is disabled, those methods do not enlarge the public Robot interface or invalidate Libdoc.

## AI-contract layer

`ai/hp34401a_ai_contract.yaml` is the canonical machine-readable semantic description of one driver. It includes:

- exact public keyword signatures;
- state machine and valid transitions;
- resource ownership and physical connection points;
- closed error catalogue and recovery policy;
- safety constraints and safe teardown;
- verification objectives with pass/fail oracles;
- timing, blocking, idempotency, retry, and planning metadata.

`ai/hp34401a_ai_contract.lock` contains a SHA-256 hash of the normalized live keyword surface. `scripts/validate_ai_contract.py` compares the library, contract, and lock so stale contracts fail CI.

RFDS-018 describes the complete bench and is intentionally not embedded as an asserted bench configuration. The included template must be completed in the bench repository using verified wiring, shared resources, safety zones, and driver aliases.

# Using the AI Contracts

Release v26.02 adds machine-readable contracts for automatic test planning.

## Driver contract

The canonical single-driver contract is:

```text
ai/ai_contract.yaml
```

It conforms to RFDS-017 v3.0 and contains:

- driver identity and mental model;
- state and resource ownership;
- one capability entry for every public Robot Framework keyword;
- exact keyword signatures and argument defaults;
- preconditions, postconditions, side effects, timing and retry policy;
- a closed error catalogue;
- machine-checkable safety rules;
- verification objectives with pass/fail oracles;
- suite setup and teardown rules;
- conservative `UNKNOWN` handling.

The file uses JSON syntax, which is valid YAML 1.2. This makes it readable by YAML and JSON tooling without adding a runtime parser dependency.

## Contract lock

`ai/ai_contract.lock` stores:

- SHA-256 of the canonical contract;
- SHA-256 of the exact public keyword manifest;
- keyword count;
- driver release version.

Any public keyword change or contract edit makes the lock stale. Regenerate it only after reviewing the semantic change:

```bash
python scripts/update_ai_contract_lock.py
python scripts/validate_ai_contract.py
```

## Test-bench contract

`system_ai_contract.yaml` conforms structurally to RFDS-018 v1.0. It is a conservative standalone bench template that links this climate-chamber driver to placeholder DUT and independent reference-temperature drivers.

Values such as chamber IP, model limits, DUT limits, reference sensor and emergency procedure remain `UNKNOWN` until the actual laboratory fills them in. The template explicitly denies control-changing plan generation while critical safety values are unknown.

## AI planner workflow

1. Load `ai/ai_contract.yaml`.
2. Verify its hash against `ai/ai_contract.lock`.
3. Load the laboratory-specific `system_ai_contract.yaml`.
4. Resolve every safety-critical `UNKNOWN` value.
5. Select verification objectives and compatible test templates.
6. Generate Robot Framework calls using the exact capability signatures.
7. Emit the contracted suite teardown and failure recovery sequence.
8. Preserve generated evidence and requirement-to-oracle traceability.

## CI validation

The repository and release builder run:

```bash
python scripts/validate_ai_contract.py
```

The check fails when a public keyword is undocumented, a signature changes, an error or state reference is invalid, a mandatory RFDS section is missing, or the lock is stale.

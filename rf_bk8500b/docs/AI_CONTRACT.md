# AI driver contract

Release v26.04 adds the canonical RFDS-017 machine contract:

- `ai/bk8500b_ai_contract.yaml` — one entry for every public Robot Framework keyword.
- `ai/bk8500b_ai_contract.lock` — SHA-256 of the public keyword names and exact signatures.
- `ai/rfds017.schema.json` — project-local validation schema for the RFDS-017 v3 structure.

The contract describes the instrument mental model, state machine, resources,
dependencies, keyword preconditions and postconditions, risks, timing, retry policy,
error recovery, safety sequences, verification oracles, setup/teardown, limitations,
and unknown-value handling.

Validate it from the repository root:

```bash
python scripts/verify_ai_contract.py
```

After an intentional public keyword name or signature change, first update the matching
capability entry and then regenerate the lock:

```bash
python scripts/verify_ai_contract.py --update-lock
```

A lock mismatch is treated as a stale contract and fails CI. The validator also fails
when a public keyword is missing, duplicated, or has a different signature; when an
error or state reference cannot be resolved; or when a verification objective lacks an
oracle.

The contract truthfully marks hardware qualification and several exact model limits as
unknown where the release has no HIL evidence. AI planners must apply the conservative
fallbacks defined in `unknown_handling` rather than guessing.

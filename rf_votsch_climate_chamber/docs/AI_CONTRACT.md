# RFDS-017 AI Driver Contract

The canonical file is `ai/ai_contract.yaml` in the repository root.

Release v26.02 documents all 36 public Robot Framework keywords as machine-verifiable capabilities. Each capability defines its exact signature, semantic purpose, input and return types, preconditions, postconditions, side effects, risk, blocking behavior, timing, stabilization delay, retry policy, errors, and exclusive resources.

## Safety and planning model

The contract distinguishes the TCP session from the physical chamber state. A network disconnect does **not** prove that environmental control stopped. Generated teardown must therefore call `Stop And Disconnect Climate Chamber`, and any communication loss must leave the physical state treated as uncertain.

The chamber internal temperature is preferred for control and stability monitoring. It is not declared traceable for calibration or temperature-accuracy verification; an independent calibrated sensor is required for those objectives.

## Staleness detection

`ai/ai_contract.lock` binds the contract to the exact keyword manifest and release. Run:

```bash
python scripts/validate_ai_contract.py
```

Use `python scripts/update_ai_contract_lock.py` only after intentionally reviewing and accepting API or semantic changes.

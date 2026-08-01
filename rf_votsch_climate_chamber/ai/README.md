# AI contracts

This directory contains the canonical RFDS-017 v3.0 contract for the driver.

- `votsch_climate_chamber_ai_contract.yaml` is JSON-compatible YAML and defines every public Robot keyword, state, resource, error, safety rule, oracle, and planning constraint.
- `votsch_climate_chamber_ai_contract.lock` records the SHA-256 of the contract and the exact public keyword manifest.

Validate both files with:

```bash
python scripts/validate_ai_contract.py
```

The repository root also contains `system_ai_contract.yaml`, an RFDS-018 bench template. It intentionally retains `UNKNOWN` values where the actual chamber, DUT, fixture, reference sensor, or emergency procedure must be supplied by the laboratory.
